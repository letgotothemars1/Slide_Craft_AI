"""Recover interrupted local MVP work while retaining all accepted content.

The course app uses one API worker. A restart cannot resume an in-memory task,
so expose a retry instead of leaving its slide/block permanently generating.
"""
from copy import deepcopy

from sqlalchemy import select

from app.db import Project, SessionLocal
from app.services.modular_build import _mutate


def recover_interrupted_work() -> None:
    with SessionLocal() as session:
        ids = list(session.scalars(select(Project.id)))
    for project_id in ids:
        def recover(project: Project) -> dict | None:
            slides = deepcopy(project.slides_json)
            workflow=deepcopy(project.workflow_json or {})
            changed = False
            # Every in-memory operation was lost, including edits started on a ready deck.
            for action in workflow.get("actions",[]):
                if action.get("status")=="running":
                    action["status"]="error"
                    changed=True
            if project.phase in {"designing","drafting"}:
                workflow["stage"]="error"
            for slide in slides:
                if slide.get("variants_status") == "generating":
                    slide.update(variants_status="error", variants_token=None,
                                 variants_error="Layout alternatives were interrupted. Please retry.")
                    changed = True
                if slide.get("sections_status")=="generating":
                    slide.update(sections_status="error",sections_error="Grouping interrupted by a restart. Retry with current text.")
                    changed=True
                if slide.get("design_status") in {"queued","generating"}:
                    slide.update(design_status="error", design_error="Design interrupted by a restart. Retry this slide.", revision=slide["revision"]+1)
                    changed=True
                if slide["status"] in {"queued", "generating"}:
                    slide.update(status="error", revision=slide["revision"] + 1)
                    for block in slide["blocks"].values():
                        if block["status"] == "generating":
                            block.update(status="error", revision=block["revision"] + 1,
                                         error="Generation was interrupted. Retry this slide.")
                    changed = True
                elif slide["status"] == "ready":
                    for block in slide["blocks"].values():
                        if block["status"] == "generating":
                            block.update(status="error", revision=block["revision"] + 1,
                                         error="Generation was interrupted by a restart. Your previous text is kept. Try again.")
                            slide["revision"] += 1
                            changed = True
            if project.phase == "designing":
                return {"slides_json":slides,"phase":"outline_draft","workflow_json":workflow}
            if project.phase == "drafting":
                return {"slides_json": slides, "phase": "outline_draft" if project.outline_json else "intake","workflow_json":workflow}
            if not changed:
                return None
            values = {"slides_json": slides, "workflow_json": workflow}
            if project.phase == "building":
                values["phase"] = "error" if any(row["status"] != "ready" for row in slides) else "ready"
            return values
        _mutate(project_id, recover)
