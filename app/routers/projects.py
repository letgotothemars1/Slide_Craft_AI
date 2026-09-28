"""Read-only contract fixture for the first modular MVP milestone."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.project_schemas import ProjectResponse


router = APIRouter(prefix="/projects", tags=["projects"])
_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "project-instructions" / "fixtures" / "demo-project.json"


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_fixture(project_id: str) -> ProjectResponse:
    """Expose only the demo fixture until M02 adds persisted projects."""
    if project_id != "demo-project":
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(json.loads(_FIXTURE_PATH.read_text(encoding="utf-8")))
