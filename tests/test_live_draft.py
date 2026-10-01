import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import BackgroundTasks
from app import repository
from app.db import Base
from app.project_schemas import ProjectCreateRequest, BuildRequest, OutlineApproveRequest, BlockEditRequest, SourceRef
from app.routers.projects import start_draft, approve_outline, edit_slide_block
from app.services import live_draft, modular_build
from app.services.modular_slide_llm import partial_body, _model_body
from app.services.llm_service import OpenAILLMService
from app.services.draft_visual import validated_visual
from app.services.outline_service import starter_outline

class LiveDraftTest(unittest.TestCase):
    def test_partial_json_and_actual_stream(self):
        self.assertEqual(partial_body('{"body":"Hello \\nwor', False), 'Hello \nwor')
        self.assertEqual(partial_body('{"left":"A","right":"B', True), 'A | B')
        service = OpenAILLMService.__new__(OpenAILLMService)
        service.model = 'test'; service.client = MagicMock()
        service.client.responses.create.return_value = iter([
            SimpleNamespace(type='response.output_text.delta',delta='{"body":"One'),
            SimpleNamespace(type='response.output_text.delta',delta=' two"}'),
            SimpleNamespace(type='response.completed')])
        chunks = []
        with patch('app.services.modular_slide_llm.get_llm_service',return_value=service):
            self.assertEqual(_model_body('s','u',False,on_partial=chunks.append),'One two')
        self.assertEqual(chunks,['One','One two'])
        self.assertTrue(service.client.responses.create.call_args.kwargs['stream'])

    def test_visual_rejects_numbers_without_pdf(self):
        item = starter_outline('Thesis: cautious')[0]
        raw = dict(kind='bars',labels=['Before','After'],values=[42,29],unit='%')
        self.assertIsNone(validated_visual(raw,item))
        item.suggested_refs = [SourceRef(document_id='d',filename='synthetic.pdf',page_number=1,excerpt='Synthetic rate: 42% before, 29% after.')]
        self.assertIsNotNone(validated_visual(raw,item))
        raw['values'] = [42,28]
        self.assertIsNone(validated_visual(raw,item))

    def test_draft_edit_survives_stream_and_approval_reuses_content(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory)/'draft.db'}")
            Base.metadata.create_all(engine); sessions = sessionmaker(bind=engine)
            with patch.object(live_draft,'SessionLocal',sessions), patch.object(modular_build,'SessionLocal',sessions):
                with sessions() as session:
                    project = repository.create_project(session,ProjectCreateRequest(assignment_text='Five slides',context_pack_text='Thesis: cautious'))
                    queued = start_draft(project.id,BuildRequest(expected_revision=0),BackgroundTasks(),session)
                def generate(current,item,on_partial,on_visual,on_sections=None):
                    on_partial('First text')
                    with sessions() as session:
                        state = repository.project_response(session,repository.get_project(session,project.id))
                        self.assertEqual(state.slides[item.order-1].blocks.body.text,'First text')
                        if item.order == 1:
                            edit_slide_block(project.id,item.id,'title',BlockEditRequest(expected_revision=state.revision,text='Accepted title'),session)
                    return 'Point A | Point B' if item.layout_type == 'comparison' else 'Completed content'
                with sessions() as session:
                    db = repository.get_project(session,project.id); db.build_mode='model'; session.commit()
                with patch.object(live_draft,'generate_model_outline',side_effect=lambda *args:starter_outline('Thesis: cautious')), patch.object(live_draft,'generate_slide_body',side_effect=generate):
                    live_draft.run_live_draft(project.id)
                with sessions() as session:
                    state = repository.project_response(session,repository.get_project(session,project.id))
                    self.assertEqual(state.phase,'outline_draft')
                    self.assertEqual(state.slides[0].blocks.title.text,'Accepted title')
                    accepted = approve_outline(project.id,OutlineApproveRequest(expected_revision=state.revision,theme='dark_tech_pitch'),session)
                    self.assertEqual(accepted.phase,'ready')
                    self.assertEqual(accepted.slides,state.slides)
                    self.assertEqual(accepted.outline[0].title,'Accepted title')
                    self.assertEqual(accepted.outline[0].key_message,'Completed content')
            engine.dispose()
