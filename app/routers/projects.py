"""Read-only contract fixture for the first modular MVP milestone."""

import json
from copy import deepcopy
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import update
from sqlalchemy.orm import Session

from app import repository
from app.db import Project, get_session
from app.project_schemas import (
    SpeakerNotesEditRequest, SectionEditRequest,
    SlideRegenerateRequest, SourceVisibilityRequest, ConfirmSourceRequest, CompositionRequest, BlockEditRequest, BuildRequest, OutlineApproveRequest, OutlineGenerateRequest, OutlineRevisionRequest, OutlineSaveRequest,
    ProjectCreateRequest, ProjectResponse, SourceRef,
)
from app.services.outline_service import starter_outline
from app.services.project_outline_llm import generate_model_outline
from app.services.modular_build import queued_slide, run_build
from app.services.modular_export import render_project_pptx
from app.services.modular_pdf import render_project_pdf
from app.services.llm_service import get_llm_service
from app.services.modular_regenerate import run_regeneration
from app.services.live_draft import run_live_draft
from app.services.slide_revision import run_slide_revision
from app.services.ai_design import run_design


# Mounted under /api so the modular journey's own pages — /projects/new and
# /projects/<id> in the SPA router — keep their URLs. Sharing the prefix made
# the two indistinguishable to the reverse proxy: a request for the page was
# answered by the API, or the other way round, depending on the rule in nginx.
router = APIRouter(prefix="/api/projects", tags=["projects"])
_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "project-instructions" / "fixtures" / "demo-project.json"
_DEMO_DIR = _FIXTURE_PATH.parent


@router.get("/demo/materials")
def demo_materials() -> dict[str, str]:
    assignment = (_DEMO_DIR / "demo-assignment.md").read_text(encoding="utf-8")
    context_pack = (_DEMO_DIR / "demo-context-pack.md").read_text(encoding="utf-8")
    return {
        "assignment_text": assignment.split("\n", 1)[1].strip(),
        "context_pack_text": context_pack.strip(),
        "source_filename": "slidecraft-synthetic-demo-source.pdf",
    }


@router.get("/demo/source.pdf")
def demo_source_pdf() -> FileResponse:
    return FileResponse(_DEMO_DIR / "demo-source.pdf", media_type="application/pdf",
                        filename="slidecraft-synthetic-demo-source.pdf")


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, session: Session = Depends(get_session)) -> ProjectResponse:
    if project_id == "demo-project":
        return ProjectResponse.model_validate(json.loads(_FIXTURE_PATH.read_text(encoding="utf-8")))
    project = repository.get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return repository.project_response(session, project)


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(payload: ProjectCreateRequest, session: Session = Depends(get_session)) -> ProjectResponse:
    if not payload.assignment_text.strip() or not payload.context_pack_text.strip():
        raise HTTPException(status_code=422, detail="Assignment and Context Pack are required")
    if payload.source_document_id:
        source = repository.get_document(session, payload.source_document_id)
        if source is None or source.status != "ready":
            raise HTTPException(status_code=422, detail="Source PDF is missing or not ready")
    project = repository.create_project(session, payload)
    return repository.project_response(session, project)


def _editable_project(session: Session, project_id: str) -> Project:
    if project_id == "demo-project":
        raise HTTPException(status_code=403, detail="The demo fixture is read-only")
    project = repository.get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _require_revision(session: Session, project: Project, expected_revision: int) -> None:
    if project.revision != expected_revision:
        raise HTTPException(status_code=409, detail={
            "message": "Project changed. Refresh before saving again.",
            "project": repository.project_response(session, project).model_dump(),
        })


def _change_project(session: Session, project: Project, expected_revision: int, **values: object) -> ProjectResponse:
    result = session.execute(
        update(Project)
        .where(Project.id == project.id, Project.revision == expected_revision)
        .values(revision=expected_revision + 1, **values)
    )
    if result.rowcount != 1:
        session.rollback()
        latest = _editable_project(session, project.id)
        _require_revision(session, latest, expected_revision)
        raise HTTPException(status_code=409, detail="Project changed")
    session.commit()
    session.expire_all()
    return repository.project_response(session, _editable_project(session, project.id))


@router.get("/{project_id}/source-candidates", response_model=list[SourceRef])
def source_candidates(project_id: str, session: Session = Depends(get_session)) -> list[SourceRef]:
    project = _editable_project(session, project_id)
    if not project.source_document_id:
        return []
    source = repository.get_document(session, project.source_document_id)
    if source is None or source.status != "ready":
        return []
    return [SourceRef(document_id=source.id, filename=source.filename,
                      page_number=chunk.page_number, excerpt=chunk.chunk_text[:600])
            for chunk in repository.list_document_chunks(session, source.id)
            if chunk.page_number is not None][:30]


@router.post("/{project_id}/draft/start", response_model=ProjectResponse, status_code=202)
def start_draft(project_id: str, payload: BuildRequest, background: BackgroundTasks,
                session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase != "intake" and not (project.phase == "error" and not project.outline_json):
        raise HTTPException(status_code=422, detail="Start a draft from saved materials")
    if payload.mode == "model":
        try:
            get_llm_service()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="AI provider is not configured. Try the key-free draft.") from exc
    updated = _change_project(session, project, payload.expected_revision, phase="drafting", build_mode=payload.mode, workflow_json={**(project.workflow_json or {}),"stage":"planning"})
    background.add_task(run_live_draft, project_id)
    return updated


@router.post("/{project_id}/draft/slides/{slide_id}/source", response_model=ProjectResponse)
def confirm_draft_source(project_id: str, slide_id: str, payload: ConfirmSourceRequest,
                         session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    candidates = source_candidates(project_id, session)
    if payload.source_ref not in candidates:
        raise HTTPException(status_code=422, detail="Select an excerpt from the shared PDF")
    outline = deepcopy(project.outline_json)
    slides = deepcopy(project.slides_json)
    target = next((s for s in slides if s["id"] == slide_id), None)
    item = next((s for s in outline if s["id"] == slide_id), None)
    if project.phase != "outline_draft" or not target or target["status"] != "ready":
        raise HTTPException(status_code=422, detail="Wait for this draft slide before confirming its source")
    ref = payload.source_ref
    item["evidence_refs"] = [ref.model_dump()]
    target["blocks"]["source_label"].update(text=f"{ref.filename}, p. {ref.page_number}", status="ready", error=None,
                                          revision=target["blocks"]["source_label"]["revision"] + 1)
    target["revision"] += 1
    return _change_project(session, project, payload.expected_revision, slides_json=slides, outline_json=outline)


@router.patch("/{project_id}/draft/slides/{slide_id}/composition", response_model=ProjectResponse)
def change_composition(project_id: str, slide_id: str, payload: CompositionRequest,
                       session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    outline = deepcopy(project.outline_json)
    slides = deepcopy(project.slides_json)
    item = next((s for s in outline if s["id"] == slide_id), None)
    target = next((s for s in slides if s["id"] == slide_id), None)
    if project.phase not in {"outline_draft", "ready"} or not target or target["status"] != "ready" or target["blocks"]["body"]["status"] == "generating":
        raise HTTPException(status_code=422, detail="Wait for the slide before changing its composition")
    body = target["blocks"]["body"]
    if payload.layout_type == "comparison" and target.get("sections"):
        if len(target["sections"]) != 2:
            raise HTTPException(status_code=422, detail="Use two sections before choosing a comparison")
        body["text"] = " | ".join(s["text"] for s in target["sections"])
    elif payload.layout_type == "comparison" and "|" not in body["text"]:
        import re
        points = re.split(r"(?<=[.!?])\s+|\n", body["text"], maxsplit=1)
        if len(points) != 2 or not all(p.strip() for p in points):
            raise HTTPException(status_code=422, detail="A comparison needs two points. Add two sentences first.")
        body["text"] = " | ".join(points)
    elif payload.layout_type != "comparison":
        body["text"] = body["text"].replace(" | ", "\n").replace("|", "\n")
    if len(body["text"]) > 500:
        raise HTTPException(status_code=422, detail="Shorten the slide text before changing its composition")
    body["revision"] += 1
    item["layout_type"] = payload.layout_type
    target.update(design=None, design_status="none", design_error=None)
    target["visual"] = None
    target["revision"] += 1
    return _change_project(session, project, payload.expected_revision, slides_json=slides, outline_json=outline)


@router.delete("/{project_id}/draft/slides/{slide_id}/visual", response_model=ProjectResponse)
def hide_visual(project_id: str, slide_id: str, payload: OutlineRevisionRequest,
                session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    slides = deepcopy(project.slides_json)
    target = next((s for s in slides if s["id"] == slide_id), None)
    if not target or target["status"] != "ready":
        raise HTTPException(status_code=422, detail="Wait for this slide to finish")
    if project.phase == "designing":
        raise HTTPException(status_code=422, detail="Wait for design to finish")
    target["visual"] = None
    target.update(design=None,design_status="none",design_error=None,design_stage="none",quality_issues=[],quality_attempts=0)
    target["revision"] += 1
    workflow={**(project.workflow_json or {}),"stage":"review","coherence_review":None,"deck_review":None,"deck_design":None,"deck_design_signature":None}
    return _change_project(session, project, payload.expected_revision, slides_json=slides,
                           workflow_json=workflow,phase="outline_draft" if project.phase=="ready" else project.phase)


@router.patch("/{project_id}/draft/slides/{slide_id}/source-visibility", response_model=ProjectResponse)
def source_visibility(project_id: str, slide_id: str, payload: SourceVisibilityRequest,
                      session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    slides = deepcopy(project.slides_json)
    target = next((row for row in slides if row["id"] == slide_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Slide not found")
    target["show_source"] = payload.show_source
    target["revision"] += 1
    return _change_project(session, project, payload.expected_revision, slides_json=slides)


@router.post("/{project_id}/draft/slides/{slide_id}/regenerate", response_model=ProjectResponse, status_code=202)
def revise_slide(project_id: str, slide_id: str, payload: SlideRegenerateRequest, background: BackgroundTasks,
                 session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    slides = deepcopy(project.slides_json)
    target = next((row for row in slides if row["id"] == slide_id), None)
    if project.phase not in {"outline_draft", "ready"} or not target or target["status"] != "ready":
        raise HTTPException(status_code=422, detail="Wait for this slide before revising it")
    if any(block["status"] == "generating" for block in target["blocks"].values()):
        raise HTTPException(status_code=409, detail="This slide is already regenerating")
    instruction = payload.instruction.strip()
    if not instruction:
        raise HTTPException(status_code=422, detail="Describe what should change on this slide")
    try:
        get_llm_service()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="AI provider is not configured for regeneration") from exc
    target["revision_instruction"] = instruction
    tokens = {}
    for key in ("title", "body"):
        block = target["blocks"][key]
        block.update(status="generating", error=None, revision=block["revision"] + 1)
        tokens[key] = block["revision"]
    target["revision"] += 1
    updated = _change_project(session, project, payload.expected_revision, slides_json=slides)
    background.add_task(run_slide_revision, project_id, slide_id, tokens)
    return updated


@router.post("/{project_id}/draft/slides/{slide_id}/retry", response_model=ProjectResponse, status_code=202)
def retry_draft(project_id: str, slide_id: str, payload: OutlineRevisionRequest, background: BackgroundTasks,
                session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    target = next((s for s in project.slides_json if s["id"] == slide_id), None)
    if project.phase != "outline_draft" or not target or target["status"] != "error":
        raise HTTPException(status_code=422, detail="Only a failed draft slide can be retried")
    updated = _change_project(session, project, payload.expected_revision, phase="drafting")
    background.add_task(run_live_draft, project_id, only_slide_id=slide_id)
    return updated


@router.post("/{project_id}/design/start", response_model=ProjectResponse, status_code=202)
def start_design(project_id: str, payload: OutlineApproveRequest, background: BackgroundTasks,
                 session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase not in {"outline_draft", "ready"} or len(project.slides_json) != 5 or any(row["status"] != "ready" or (row.get("sections_status")=="generating" or any(b["status"] == "generating" for b in row["blocks"].values())) for row in project.slides_json):
        raise HTTPException(status_code=422, detail="Complete all five slide texts before AI design")
    if project.build_mode=="model":
        try:
            get_llm_service()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="AI provider is not configured for design") from exc
    rows = deepcopy(project.slides_json)
    outline = deepcopy(project.outline_json)
    for row in rows:
        row.update(design_status="queued", design_error=None)
        item = next(item for item in outline if item["id"] == row["id"])
        item["title"] = row["blocks"]["title"]["text"]
        item["key_message"] = row["blocks"]["body"]["text"]
    updated = _change_project(session, project, payload.expected_revision, phase="designing", theme=payload.theme, slides_json=rows, outline_json=outline, workflow_json={**(project.workflow_json or {}),"stage":"design_planning","deck_design":None})
    background.add_task(run_design, project_id)
    return updated


@router.post("/{project_id}/design/slides/{slide_id}/retry", response_model=ProjectResponse, status_code=202)
def retry_design(project_id: str, slide_id: str, payload: OutlineRevisionRequest, background: BackgroundTasks,
                 session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    rows = deepcopy(project.slides_json)
    target = next((row for row in rows if row["id"] == slide_id), None)
    if project.phase not in {"outline_draft", "ready"} or not target or target.get("design_status", "none") not in {"error", "none"} or any(b["status"] == "generating" for b in target["blocks"].values()):
        raise HTTPException(status_code=422, detail="Retry a failed or outdated slide design")
    target.update(design_status="queued", design_error=None)
    updated = _change_project(session, project, payload.expected_revision, phase="designing", slides_json=rows)
    background.add_task(run_design, project_id, only_slide_id=slide_id)
    return updated


@router.post("/{project_id}/outline/generate", response_model=ProjectResponse)
def generate_outline(project_id: str, payload: OutlineGenerateRequest, session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase != "intake":
        raise HTTPException(status_code=422, detail="An outline already exists")
    if payload.mode == "model":
        candidates = source_candidates(project_id, session)
        try:
            items = generate_model_outline(project.assignment_text, project.context_pack_text, candidates)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="AI outline could not be created. Check the configured provider and retry.") from exc
    else:
        items = starter_outline(project.context_pack_text)
    outline = [item.model_dump() for item in items]
    return _change_project(session, project, payload.expected_revision, phase="outline_draft", outline_json=outline)


@router.put("/{project_id}/outline", response_model=ProjectResponse)
def save_outline(project_id: str, payload: OutlineSaveRequest, session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase != "outline_draft":
        raise HTTPException(status_code=422, detail="Only a draft outline can be edited")
    items = payload.outline
    existing_ids = {item["id"] for item in project.outline_json}
    if {item.id for item in items} != existing_ids or len(existing_ids) != 5:
        raise HTTPException(status_code=422, detail="Keep the five original slide IDs")
    if sorted(item.order for item in items) != [1, 2, 3, 4, 5]:
        raise HTTPException(status_code=422, detail="Slide order must be 1 through 5")
    if any(not item.title.strip() or not item.key_message.strip() or not item.purpose.strip() for item in items):
        raise HTTPException(status_code=422, detail="Every slide needs a purpose, title and key message")
    if any(len(item.title) > 200 or len(item.key_message) > 500 for item in items):
        raise HTTPException(status_code=422, detail="Keep titles under 200 characters and key messages under 500")
    source = repository.get_document(session, project.source_document_id) if project.source_document_id else None
    chunks = {(chunk.page_number, chunk.chunk_text[:600]) for chunk in repository.list_document_chunks(session, source.id)} if source else set()
    for item in items:
        for ref in item.evidence_refs:
            if not source or ref.document_id != source.id or ref.filename != source.filename or (ref.page_number, ref.excerpt) not in chunks:
                raise HTTPException(status_code=422, detail="Select evidence from the attached PDF")
    ordered = sorted(items, key=lambda item: item.order)
    return _change_project(session, project, payload.expected_revision,
                           outline_json=[item.model_dump() for item in ordered])


@router.post("/{project_id}/outline/approve", response_model=ProjectResponse)
def approve_outline(project_id: str, payload: OutlineApproveRequest, session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase != "outline_draft" or len(project.outline_json) != 5:
        raise HTTPException(status_code=422, detail="Complete the five-slide draft before approval")
    if project.slides_json and any(slide["status"] != "ready" or any(b["status"] == "generating" for b in slide["blocks"].values()) for slide in project.slides_json):
        raise HTTPException(status_code=422, detail="Wait for all five draft slides before approval")
    values = {"phase": "ready" if project.slides_json else "outline_approved", "theme": payload.theme}
    if project.slides_json:
        accepted = {slide["id"]: slide for slide in project.slides_json}
        outline = deepcopy(project.outline_json)
        for item in outline:
            item["title"] = accepted[item["id"]]["blocks"]["title"]["text"]
            item["key_message"] = accepted[item["id"]]["blocks"]["body"]["text"]
        values["outline_json"] = outline
    return _change_project(session, project, payload.expected_revision, **values)


@router.post("/{project_id}/build", response_model=ProjectResponse, status_code=202)
def build_project(project_id: str, payload: BuildRequest, background: BackgroundTasks,
                  session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase != "outline_approved" or len(project.outline_json) != 5:
        raise HTTPException(status_code=422, detail="Approve the five-slide outline first")
    if payload.mode == "model":
        try:
            get_llm_service()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="AI provider is not configured for slide building") from exc
    slides = [queued_slide(item).model_dump() for item in repository.project_response(session, project).outline]
    updated = _change_project(session, project, payload.expected_revision,
                              phase="building", slides_json=slides, build_mode=payload.mode)
    # Pace only the key-free demo; model calls provide their own visible progress.
    background.add_task(run_build, project_id, pause_seconds=0.8 if payload.mode == "template" else 0.0)
    return updated


@router.patch("/{project_id}/slides/{slide_id}/blocks/{block_key}", response_model=ProjectResponse)
def edit_slide_block(project_id: str, slide_id: str, block_key: str, payload: BlockEditRequest,
                     session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if block_key not in {"title", "body", "source_label"}:
        raise HTTPException(status_code=404, detail="Unknown slide block")
    text = payload.text.strip()
    if not text or (block_key in {"title", "source_label"} and len(text) > 200):
        raise HTTPException(status_code=422, detail="Block text is empty or too long")
    slides = deepcopy(project.slides_json)
    target = next((slide for slide in slides if slide["id"] == slide_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Slide not found")
    if target["status"] != "ready" and not (project.phase == "drafting" and target["blocks"][block_key]["status"] == "ready"):
        raise HTTPException(status_code=422, detail="This element is still being generated")
    if block_key == "body":
        if len(text) > 500:
            raise HTTPException(status_code=422, detail="Keep slide body text under 500 characters")
        item = next(item for item in project.outline_json if item["id"] == slide_id)
        if item["layout_type"] == "comparison" and (len(text.split("|")) != 2 or not all(part.strip() for part in text.split("|"))):
            raise HTTPException(status_code=422, detail="Comparison slides need two points separated by |")
    if block_key in {"title", "body"} and target.get("design"):
        target.update(design=None, design_status="none", design_error=None)
    if block_key == "body":
        target["visual"] = None
        target.update(sections=[],sections_status="none",sections_error=None)
    target["blocks"][block_key]["text"] = text
    target["blocks"][block_key]["status"] = "ready"
    target["blocks"][block_key]["error"] = None
    target["blocks"][block_key]["revision"] += 1
    target["revision"] += 1
    return _change_project(session, project, payload.expected_revision, slides_json=slides)


@router.post("/{project_id}/slides/{slide_id}/blocks/{block_key}/reset-from-outline", response_model=ProjectResponse)
def reset_slide_block(project_id: str, slide_id: str, block_key: str, payload: OutlineRevisionRequest,
                      session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if block_key not in {"title", "body"}:
        raise HTTPException(status_code=404, detail="Only title and body can be reset from the outline")
    item = next((item for item in project.outline_json if item["id"] == slide_id), None)
    slides = deepcopy(project.slides_json)
    target = next((slide for slide in slides if slide["id"] == slide_id), None)
    if item is None or target is None:
        raise HTTPException(status_code=404, detail="Slide not found")
    if target["status"] != "ready":
        raise HTTPException(status_code=422, detail="Slide is not ready")
    if target.get("design"):
        target.update(design=None, design_status="none", design_error=None)
    if block_key == "body":
        target["visual"] = None
        target.update(sections=[],sections_status="none",sections_error=None)
    target["blocks"][block_key]["text"] = item["title" if block_key == "title" else "key_message"]
    target["blocks"][block_key]["status"] = "ready"
    target["blocks"][block_key]["error"] = None
    target["blocks"][block_key]["revision"] += 1
    target["revision"] += 1
    return _change_project(session, project, payload.expected_revision, slides_json=slides)


@router.post("/{project_id}/slides/{slide_id}/blocks/{block_key}/regenerate", response_model=ProjectResponse, status_code=202)
def regenerate_slide_block(project_id: str, slide_id: str, block_key: str, payload: OutlineRevisionRequest,
                           background: BackgroundTasks, session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if block_key not in {"title", "body"}:
        raise HTTPException(status_code=404, detail="Only title and body can be regenerated")
    slides = deepcopy(project.slides_json)
    target = next((slide for slide in slides if slide["id"] == slide_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Slide not found")
    if target["status"] != "ready":
        raise HTTPException(status_code=422, detail="Slide is not ready")
    block = target["blocks"][block_key]
    if block["status"] == "generating":
        raise HTTPException(status_code=409, detail="This block is already regenerating. Refresh to see its progress.")
    try:
        get_llm_service()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="AI provider is not configured for regeneration") from exc
    block.update(status="generating", revision=block["revision"] + 1, error=None)
    target["revision"] += 1
    updated = _change_project(session, project, payload.expected_revision, slides_json=slides)
    background.add_task(run_regeneration, project_id, slide_id, block_key, block["revision"])
    return updated


@router.post("/{project_id}/slides/{slide_id}/retry", response_model=ProjectResponse, status_code=202)
def retry_slide(project_id: str, slide_id: str, payload: OutlineRevisionRequest,
                background: BackgroundTasks, session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    slides = deepcopy(project.slides_json)
    target = next((slide for slide in slides if slide["id"] == slide_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Slide not found")
    if target["status"] != "error":
        raise HTTPException(status_code=422, detail="Only a failed slide can be retried")
    updated = _change_project(session, project, payload.expected_revision, phase="building")
    background.add_task(run_build, project_id, only_slide_id=slide_id)
    return updated


def _require_current_design_agreement(response: ProjectResponse) -> None:
    # Legacy modular and one-shot exports never entered the staged AI design gate.
    if response.build_mode=="model" and any(slide.design for slide in response.slides):
        review=response.workflow.coherence_review
        if not review or review.get("mode")!="model" or not review.get("approved"):
            raise HTTPException(status_code=422,detail="Review slide content and speaker notes before exporting final AI designs")


@router.get("/{project_id}/export.pptx")
def export_project_pptx(project_id: str, session: Session = Depends(get_session)) -> Response:
    project = _editable_project(session, project_id)
    response = repository.project_response(session, project)
    if response.phase != "ready":
        raise HTTPException(status_code=422, detail="All slides must be ready before export")
    if any(block.status == "generating" for slide in response.slides
           for block in (slide.blocks.title, slide.blocks.body, slide.blocks.source_label)):
        raise HTTPException(status_code=422, detail="Wait for block regeneration to finish before exporting")
    _require_current_design_agreement(response)
    try:
        data = render_project_pptx(response)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="slidecraft-{project_id}.pptx"'},
    )


@router.get("/{project_id}/export.pdf")
def export_project_pdf(project_id: str, session: Session = Depends(get_session)) -> Response:
    """Fixed, presentable copy. PPTX stays the editable one."""
    project = _editable_project(session, project_id)
    response = repository.project_response(session, project)
    if response.phase != "ready":
        raise HTTPException(status_code=422, detail="All slides must be ready before export")
    if any(block.status == "generating" for slide in response.slides
           for block in (slide.blocks.title, slide.blocks.body, slide.blocks.source_label)):
        raise HTTPException(status_code=422, detail="Wait for block regeneration to finish before exporting")
    _require_current_design_agreement(response)
    try:
        data = render_project_pdf(response)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="slidecraft-{project_id}.pdf"'},
    )


@router.post("/{project_id}/slides/{slide_id}/sections/prepare", response_model=ProjectResponse, status_code=202)
def prepare_sections(project_id: str, slide_id: str, payload: OutlineRevisionRequest, background: BackgroundTasks, session: Session = Depends(get_session)):
    from app.services.semantic_sections import run_sections
    project=_editable_project(session,project_id)
    _require_revision(session,project,payload.expected_revision)
    rows=deepcopy(project.slides_json); target=next((r for r in rows if r['id']==slide_id),None)
    if project.phase not in {'outline_draft','ready'} or not target or target['status']!='ready' or target['blocks']['body']['status']!='ready' or target.get('sections_status')=='generating':
        raise HTTPException(status_code=422,detail='Wait for the slide before grouping its content')
    target.update(sections_status='generating',sections_error=None)
    result=_change_project(session,project,payload.expected_revision,slides_json=rows)
    background.add_task(run_sections,project_id,slide_id,target['blocks']['body']['revision'])
    return result


@router.patch("/{project_id}/slides/{slide_id}/sections", response_model=ProjectResponse)
def edit_sections(project_id: str, slide_id: str, payload: SectionEditRequest, session: Session = Depends(get_session)):
    project=_editable_project(session,project_id); _require_revision(session,project,payload.expected_revision)
    rows=deepcopy(project.slides_json); target=next((r for r in rows if r['id']==slide_id),None)
    if project.phase not in {'outline_draft','ready'} or not target or target['status']!='ready' or target['blocks']['body']['status']!='ready' or target.get('sections_status')=='generating':
        raise HTTPException(status_code=422,detail='Wait before editing sections')
    if next(r for r in project.outline_json if r['id']==slide_id)['layout_type']=='comparison' and len(payload.sections)!=2: raise HTTPException(status_code=422,detail='Comparison needs exactly two sections')
    if len({s.id for s in payload.sections})!=len(payload.sections): raise HTTPException(status_code=422,detail='Section ids must be unique')
    body=' | '.join(s.text for s in payload.sections) if next(r for r in project.outline_json if r['id']==slide_id)['layout_type']=='comparison' else '\n\n'.join(s.text for s in payload.sections)
    if len(body)>500: raise HTTPException(status_code=422,detail='Keep total section text under 500 characters')
    target.update(sections=[s.model_dump() for s in payload.sections],sections_status='ready',sections_error=None,design=None,design_status='none',design_stage='none',quality_issues=[])
    target['blocks']['body'].update(text=body,revision=target['blocks']['body']['revision']+1)
    target['revision']+=1
    return _change_project(session,project,payload.expected_revision,slides_json=rows,phase='outline_draft')


@router.post("/{project_id}/sections/prepare", response_model=ProjectResponse, status_code=202)
def prepare_all_sections(project_id: str, payload: OutlineRevisionRequest, background: BackgroundTasks, session: Session = Depends(get_session)):
    from app.services.semantic_sections import run_sections
    project=_editable_project(session,project_id); _require_revision(session,project,payload.expected_revision)
    if project.phase not in {'outline_draft','ready'} or any(r['status']!='ready' or r['blocks']['body']['status']!='ready' or r.get('sections_status')=='generating' for r in project.slides_json):
        raise HTTPException(status_code=422,detail='Wait for all slide text before grouping')
    rows=deepcopy(project.slides_json)
    for row in rows:
        if row.get('sections'): continue
        row.update(sections_status='generating',sections_error=None)
        background.add_task(run_sections,project_id,row['id'],row['blocks']['body']['revision'])
    return _change_project(session,project,payload.expected_revision,slides_json=rows)


@router.patch("/{project_id}/slides/{slide_id}/speaker-notes", response_model=ProjectResponse)
def edit_speaker_notes(project_id: str, slide_id: str, payload: SpeakerNotesEditRequest,
                       session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    slides = deepcopy(project.slides_json)
    target = next((row for row in slides if row["id"] == slide_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Slide not found")
    if target["status"] != "ready" or target["blocks"]["body"]["status"] == "generating":
        raise HTTPException(status_code=422, detail="Wait for slide content before editing speaker notes")
    notes = payload.speaker_notes.strip()
    if notes == target.get("speaker_notes", ""):
        return repository.project_response(session, project)
    target.update(speaker_notes=notes, revision=target["revision"] + 1,
                  design=None, design_status="none", design_error=None, design_stage="none", quality_issues=[])
    from app.services.presentation_workflow import state
    workflow = state(project)
    workflow.update(stage="review", deck_design=None, deck_design_signature=None, story_analysis=None, deck_review=None)
    return _change_project(session, project, payload.expected_revision, slides_json=slides,
                           workflow_json=workflow, phase="outline_draft" if project.phase == "ready" else project.phase)


@router.get('/{project_id}/draft/slides/{slide_id}/compositions')
def composition_previews(project_id: str, slide_id: str, session: Session = Depends(get_session)):
    from app.project_schemas import OutlineItem, ProjectSlide
    from app.services.composition_choices import persisted_choices
    project = _editable_project(session, project_id)
    slide = next((r for r in project.slides_json if r['id'] == slide_id), None)
    item = next((r for r in project.outline_json if r['id'] == slide_id), None)
    if not slide or not item or slide['status'] != 'ready':
        raise HTTPException(status_code=422, detail='Complete this slide before comparing compositions')
    return persisted_choices(project, OutlineItem.model_validate(item), ProjectSlide.model_validate(slide))


@router.post('/{project_id}/draft/slides/{slide_id}/compositions/generate', response_model=ProjectResponse, status_code=202)
def start_composition_variants(project_id: str, slide_id: str, payload: OutlineRevisionRequest,
                               background: BackgroundTasks, session: Session = Depends(get_session)):
    from app.services.composition_choices import variants_current, content_fingerprint, reserve_variants, run_composition_variants
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase not in {'outline_draft', 'ready', 'drafting'}:
        raise HTTPException(status_code=422, detail='Wait for final design before generating alternatives')
    rows = deepcopy(project.slides_json)
    slide = next((r for r in rows if r['id'] == slide_id), None)
    item = next((r for r in project.outline_json if r['id'] == slide_id), None)
    if not slide or not item or slide['status'] != 'ready' or any(b['status'] == 'generating' for b in slide['blocks'].values()):
        raise HTTPException(status_code=422, detail='Complete this slide before generating alternatives')
    if variants_current(slide, item) or (slide.get('variants_status') == 'generating' and slide.get('variants_fingerprint') == content_fingerprint(slide, item)):
        return repository.project_response(session, project)
    if project.build_mode == 'model':
        try:
            get_llm_service()
        except Exception as exc:
            raise HTTPException(status_code=503, detail='AI provider is not configured') from exc
    reserve_variants(slide, item)
    updated = _change_project(session, project, payload.expected_revision, slides_json=rows)
    background.add_task(run_composition_variants, project_id, slide_id)
    return updated


from pydantic import BaseModel, ConfigDict
from typing import Literal
class CompositionChoiceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: int
    variant_id: Literal['selected', 'alternative', 'out_of_box'] | None = None
    # Compatibility for old clients. New clients select persisted variant IDs.
    composition: Literal['balanced', 'feature', 'bands', 'poster'] | None = None


@router.patch('/{project_id}/draft/slides/{slide_id}/composition-choice', response_model=ProjectResponse)
def select_composition(project_id: str, slide_id: str, payload: CompositionChoiceRequest, session: Session = Depends(get_session)):
    from app.services.composition_choices import variants_current
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase not in {'outline_draft', 'ready'}:
        raise HTTPException(status_code=422, detail='Wait for generation before choosing a composition')
    rows = deepcopy(project.slides_json)
    slide = next((r for r in rows if r['id'] == slide_id), None)
    item = next((r for r in project.outline_json if r['id'] == slide_id), None)
    if not slide or slide['status'] != 'ready' or slide.get('sections_status') == 'generating' or any(b['status'] == 'generating' for b in slide['blocks'].values()):
        raise HTTPException(status_code=422, detail='Finish editing this slide before choosing a composition')
    if payload.variant_id:
        if not item or not variants_current(slide, item):
            raise HTTPException(status_code=422, detail='Generate current alternatives before choosing one')
        if slide.get('selected_variant_id') == payload.variant_id:
            return repository.project_response(session, project)
        slide.update(selected_variant_id=payload.variant_id, composition_preference=None)
    elif payload.composition:
        if item and variants_current(slide,item):
            variant=next((v for v in slide['composition_variants'] if v['design']['composition']==payload.composition),None)
            if variant is None:
                raise HTTPException(status_code=422, detail='Choose one of the three current alternatives')
            if slide.get('selected_variant_id')==variant['id']:
                return repository.project_response(session, project)
            slide.update(composition_preference=None,selected_variant_id=variant['id'])
        else:
            if project.build_mode=='model':
                raise HTTPException(status_code=422, detail='Generate current alternatives before choosing one')
            if slide.get('composition_preference') == payload.composition and not slide.get('selected_variant_id'):
                return repository.project_response(session, project)
            slide.update(composition_preference=payload.composition, selected_variant_id=None)
    else:
        raise HTTPException(status_code=422, detail='Choose an existing variant')
    slide.update(design=None, design_status='none', design_error=None,
                 design_stage='none', quality_issues=[], quality_attempts=0, revision=slide['revision'] + 1)
    workflow = deepcopy(project.workflow_json or {})
    workflow.update(stage='review', deck_design=None, deck_design_signature=None, deck_review=None)
    return _change_project(session, project, payload.expected_revision, slides_json=rows,
                           workflow_json=workflow, phase='outline_draft')
