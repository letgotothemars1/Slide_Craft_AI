"""Model outlines keep stable IDs and leave source selection to the student."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import repository
from app.db import Base
from app.project_schemas import OutlineGenerateRequest, ProjectCreateRequest, SourceRef
from app.routers.projects import generate_outline
from app.services.project_outline_llm import _Draft, generate_model_outline


class ModelOutlineTest(unittest.TestCase):
    def test_model_draft_has_stable_ids_and_no_unchecked_citations(self) -> None:
        draft = _Draft.model_validate({"slides": [
            {"purpose": f"Purpose {i}", "title": f"Title {i}",
             "key_message": "Point one | Point two" if i == 4 else f"Claim {i} (PDF p. 1)",
             "layout_type": "comparison" if i == 4 else "content"}
            for i in range(1, 6)
        ]})
        source = SourceRef(document_id="doc", filename="source.pdf", page_number=2, excerpt="Observed data")
        with patch("app.services.project_outline_llm._request_draft", return_value=draft) as request:
            items = generate_model_outline("Use five slides", "Thesis: cautious", [source])
        self.assertEqual([item.id for item in items], ["s1", "s2", "s3", "s4", "s5"])
        self.assertEqual(items[0].layout_type, "title")
        self.assertEqual(items[3].layout_type, "comparison")
        self.assertTrue(all(not item.evidence_refs for item in items))
        self.assertEqual(items[1].key_message, "Claim 2")
        self.assertIn("Page 2: Observed data", request.call_args.args[1])

    def test_provider_failure_keeps_project_in_intake(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'test.db'}")
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine)
            with sessions() as session:
                project = repository.create_project(session, ProjectCreateRequest(
                    assignment_text="Make five slides", context_pack_text="Thesis: cautious"))
                with patch("app.routers.projects.generate_model_outline", side_effect=RuntimeError("provider failed")):
                    with self.assertRaises(HTTPException) as raised:
                        generate_outline(project.id, OutlineGenerateRequest(expected_revision=0, mode="model"), session)
                self.assertEqual(raised.exception.status_code, 503)
                session.expire_all()
                fresh = repository.get_project(session, project.id)
                self.assertEqual(fresh.phase, "intake")
                self.assertEqual(fresh.revision, 0)
            engine.dispose()
