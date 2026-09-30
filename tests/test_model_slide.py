"""Model slide building persists one draft at a time without losing approved work."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import repository
from app.db import Base
from app.project_schemas import BuildRequest, OutlineApproveRequest, OutlineGenerateRequest, OutlineRevisionRequest, ProjectCreateRequest
from app.routers.projects import approve_outline, build_project, generate_outline
from app.services import modular_build
from app.services.llm_service import OpenAILLMService
from app.services.modular_slide_llm import _model_body, generate_slide_body


class ModelSlideTest(unittest.TestCase):
    def test_comparison_requests_two_explicit_model_fields(self) -> None:
        service = OpenAILLMService.__new__(OpenAILLMService)
        service.model = "test-model"
        service.client = MagicMock()
        service.client.responses.create.return_value = SimpleNamespace(output_text='{"left":"Human review","right":"Maintenance time"}')
        with patch("app.services.modular_slide_llm.get_llm_service", return_value=service):
            body = _model_body("system", "user", comparison=True)
        self.assertEqual(body, "Human review | Maintenance time")
        schema = service.client.responses.create.call_args.kwargs["text"]["format"]["schema"]
        self.assertEqual(schema["required"], ["left", "right"])

    def test_body_validation_keeps_approved_title_and_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'model.db'}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine)
            with sessions() as session:
                project = repository.create_project(session, ProjectCreateRequest(
                    assignment_text="Five slides", context_pack_text="Thesis: cautious"))
                draft = generate_outline(project.id, OutlineGenerateRequest(expected_revision=0), session)
                comparison = draft.outline[3]
                with patch("app.services.modular_slide_llm._model_body", return_value="Human review | Maintenance time") as model:
                    body = generate_slide_body(project, comparison)
                self.assertEqual(body, "Human review | Maintenance time")
                self.assertIn("Approved title:", model.call_args.args[1])
                with patch("app.services.modular_slide_llm._model_body", return_value="Only one point"):
                    with self.assertRaises(ValueError):
                        generate_slide_body(project, comparison)
            engine.dispose()

    def test_model_mode_persists_each_slide_separately(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'model.db'}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine)
            with patch.object(modular_build, "SessionLocal", sessions):
                with sessions() as session:
                    project = repository.create_project(session, ProjectCreateRequest(
                        assignment_text="Five slides", context_pack_text="Thesis: cautious"))
                    draft = generate_outline(project.id, OutlineGenerateRequest(expected_revision=0), session)
                    approved = approve_outline(project.id, OutlineApproveRequest(
                        expected_revision=draft.revision, theme="clean_editorial"), session)
                    with patch("app.routers.projects.get_llm_service"):
                        queued = build_project(project.id, BuildRequest(
                            expected_revision=approved.revision, mode="model"), BackgroundTasks(), session)
                snapshots = []

                def after_slide(slide_id: str) -> None:
                    with sessions() as session:
                        state = repository.project_response(session, repository.get_project(session, project.id))
                        snapshots.append((slide_id, [slide.status for slide in state.slides]))

                with patch("app.services.modular_slide_llm.generate_slide_body",
                           side_effect=lambda project, item: f"Model body for slide {item.order}" if item.layout_type != "comparison" else "First point | Second point"):
                    modular_build.run_build(project.id, after_slide=after_slide)
                with sessions() as session:
                    ready = repository.project_response(session, repository.get_project(session, project.id))
                self.assertEqual(queued.build_mode, "model")
                self.assertEqual(snapshots[0][1], ["ready", "queued", "queued", "queued", "queued"])
                self.assertEqual(ready.phase, "ready")
                self.assertEqual(ready.slides[0].blocks.title.text, ready.outline[0].title)
                self.assertEqual(ready.slides[0].blocks.body.text, "Model body for slide 1")
                self.assertTrue(all(slide.status == "ready" for slide in ready.slides))
            engine.dispose()
