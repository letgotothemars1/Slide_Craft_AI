"""Read-only contract fixture for the first modular MVP milestone."""

import json
from copy import deepcopy
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy import update
from sqlalchemy.orm import Session

from app import repository
from app.db import Project, get_session
from app.project_schemas import (
    BlockEditRequest, OutlineApproveRequest, OutlineRevisionRequest, OutlineSaveRequest,
    ProjectCreateRequest, ProjectResponse, SourceRef,
)
from app.services.outline_service import starter_outline
from app.services.modular_build import queued_slide, run_build
from app.services.modular_export import render_project_pptx


router = APIRouter(prefix="/projects", tags=["projects"])
_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "project-instructions" / "fixtures" / "demo-project.json"


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


@router.post("/{project_id}/outline/generate", response_model=ProjectResponse)
def generate_outline(project_id: str, payload: OutlineRevisionRequest, session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase != "intake":
        raise HTTPException(status_code=422, detail="An outline already exists")
    outline = [item.model_dump() for item in starter_outline(project.context_pack_text)]
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
    return _change_project(session, project, payload.expected_revision,
                           phase="outline_approved", theme=payload.theme)


@router.post("/{project_id}/build", response_model=ProjectResponse, status_code=202)
def build_project(project_id: str, payload: OutlineRevisionRequest, background: BackgroundTasks,
                  session: Session = Depends(get_session)) -> ProjectResponse:
    project = _editable_project(session, project_id)
    _require_revision(session, project, payload.expected_revision)
    if project.phase != "outline_approved" or len(project.outline_json) != 5:
        raise HTTPException(status_code=422, detail="Approve the five-slide outline first")
    slides = [queued_slide(item).model_dump() for item in repository.project_response(session, project).outline]
    updated = _change_project(session, project, payload.expected_revision,
                              phase="building", slides_json=slides)
    background.add_task(run_build, project_id)
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
    if target["status"] != "ready":
        raise HTTPException(status_code=422, detail="Slide is not ready for editing")
    target["blocks"][block_key]["text"] = text
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
    target["blocks"][block_key]["text"] = item["title" if block_key == "title" else "key_message"]
    target["blocks"][block_key]["revision"] += 1
    target["revision"] += 1
    return _change_project(session, project, payload.expected_revision, slides_json=slides)


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


@router.get("/{project_id}/export.pptx")
def export_project_pptx(project_id: str, session: Session = Depends(get_session)) -> Response:
    project = _editable_project(session, project_id)
    response = repository.project_response(session, project)
    if response.phase != "ready":
        raise HTTPException(status_code=422, detail="All slides must be ready before export")
    try:
        data = render_project_pptx(response)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="slidecraft-{project_id}.pptx"'},
    )
