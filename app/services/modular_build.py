"""Persist one project slide at a time from the approved outline.

The local path copies approved text without claiming model generation. A model
builder can be injected later without changing the revision-safe state loop.
"""

from __future__ import annotations

import logging
import time
from copy import deepcopy
from typing import Callable

from sqlalchemy import update

from app import repository
from app.db import Project, SessionLocal
from app.project_schemas import OutlineItem, ProjectSlide, SlideBlock, SlideBlocks

logger = logging.getLogger(__name__)
SlideBuilder = Callable[[OutlineItem], ProjectSlide]


def build_slide_from_outline(item: OutlineItem) -> ProjectSlide:
    source_label = (
        f"{item.evidence_refs[0].filename}, p. {item.evidence_refs[0].page_number}"
        if item.evidence_refs else "Source needed"
    )
    return ProjectSlide(
        id=item.id, status="ready", revision=1,
        blocks=SlideBlocks(
            title=SlideBlock(text=item.title, status="ready", revision=1),
            body=SlideBlock(text=item.key_message, status="ready", revision=1),
            source_label=SlideBlock(text=source_label, status="ready", revision=1),
        ),
    )


def queued_slide(item: OutlineItem) -> ProjectSlide:
    empty = SlideBlock(text="", status="generating", revision=0)
    return ProjectSlide(
        id=item.id, status="queued", revision=0,
        blocks=SlideBlocks(title=empty.model_copy(), body=empty.model_copy(), source_label=empty.model_copy()),
    )


def _mutate(project_id: str, change: Callable[[Project], dict | None]) -> bool:
    """Compare-and-swap the project row; retry around concurrent block edits."""
    for _ in range(12):
        with SessionLocal() as session:
            project = repository.get_project(session, project_id)
            if project is None:
                return False
            values = change(project)
            if values is None:
                return False
            revision = project.revision
            result = session.execute(
                update(Project).where(Project.id == project_id, Project.revision == revision)
                .values(revision=revision + 1, **values)
            )
            if result.rowcount == 1:
                session.commit()
                return True
            session.rollback()
    raise RuntimeError("Project changed too often during slide build")


def _set_slide(project_id: str, slide_id: str, *, status: str, ready: ProjectSlide | None = None,
               expected_slide_revision: int | None = None) -> bool:
    def change(project: Project) -> dict | None:
        slides = deepcopy(project.slides_json)
        for index, raw in enumerate(slides):
            if raw["id"] != slide_id:
                continue
            if expected_slide_revision is not None and raw["revision"] != expected_slide_revision:
                return None
            if status == "generating":
                if raw["status"] not in {"queued", "error"}:
                    return None
                raw["status"] = "generating"
                raw["revision"] += 1
            elif ready is not None:
                ready_json = ready.model_dump()
                ready_json["revision"] = raw["revision"] + 1
                slides[index] = ready_json
            else:
                raw["status"] = "error"
                raw["revision"] += 1
            return {"slides_json": slides}
        return None
    return _mutate(project_id, change)


def _finish(project_id: str) -> None:
    def change(project: Project) -> dict | None:
        if project.phase != "building":
            return None
        slides = project.slides_json
        if any(slide["status"] in {"queued", "generating"} for slide in slides):
            return None
        return {"phase": "ready" if all(slide["status"] == "ready" for slide in slides) else "error"}
    _mutate(project_id, change)


def run_build(project_id: str, builder: SlideBuilder = build_slide_from_outline,
              after_slide: Callable[[str], None] | None = None,
              only_slide_id: str | None = None, pause_seconds: float = 0.0) -> None:
    """Build eligible slides in approved order and persist each result."""
    with SessionLocal() as session:
        project = repository.get_project(session, project_id)
        if project is None:
            return
        outline = [OutlineItem.model_validate(item) for item in project.outline_json]

    for index, item in enumerate(outline):
        if only_slide_id and item.id != only_slide_id:
            continue
        if not _set_slide(project_id, item.id, status="generating"):
            continue
        with SessionLocal() as session:
            project = repository.get_project(session, project_id)
            current = next(slide for slide in project.slides_json if slide["id"] == item.id)
            started_revision = current["revision"]
        try:
            ready = builder(item)
            if ready.id != item.id or ready.status != "ready":
                raise ValueError("Slide builder returned an invalid slide")
            if not _set_slide(project_id, item.id, status="ready", ready=ready,
                              expected_slide_revision=started_revision):
                logger.info("slide.build.stale project_id=%s slide_id=%s", project_id, item.id)
        except Exception:
            logger.exception("slide.build.failed project_id=%s slide_id=%s", project_id, item.id)
            _set_slide(project_id, item.id, status="error", expected_slide_revision=started_revision)
        if after_slide:
            after_slide(item.id)
        if pause_seconds > 0 and index < len(outline) - 1 and only_slide_id is None:
            time.sleep(pause_seconds)
    _finish(project_id)
