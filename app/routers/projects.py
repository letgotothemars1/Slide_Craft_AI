"""Read-only contract fixture for the first modular MVP milestone."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import repository
from app.db import get_session
from app.project_schemas import ProjectCreateRequest, ProjectResponse


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
