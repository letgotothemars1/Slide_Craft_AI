"""Delayed generation cannot overwrite newer accepted edits or other blocks."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import repository
from app.db import Base
from app.project_schemas import BlockEditRequest, BuildRequest, OutlineApproveRequest, OutlineGenerateRequest, OutlineRevisionRequest, ProjectCreateRequest
from app.routers.projects import approve_outline, build_project, edit_slide_block, export_project_pptx, generate_outline, regenerate_slide_block
from app.services import modular_build, modular_regenerate


class BlockRegenerationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.directory.name) / 'blocks.db'}")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        self.patches = [patch.object(module, 'SessionLocal', self.sessions)
                        for module in (modular_build, modular_regenerate)]
        for patcher in self.patches:
            patcher.start()
        with self.sessions() as session:
            project = repository.create_project(session, ProjectCreateRequest(
                assignment_text='Make five slides', context_pack_text='Thesis: review matters.'))
            self.project_id = project.id
            draft = generate_outline(project.id, OutlineGenerateRequest(expected_revision=0), session)
            approved = approve_outline(project.id, OutlineApproveRequest(
                expected_revision=draft.revision, theme='clean_editorial'), session)
            build_project(project.id, BuildRequest(expected_revision=approved.revision), BackgroundTasks(), session)
        modular_build.run_build(self.project_id)

    def tearDown(self):
        for patcher in self.patches:
            patcher.stop()
        self.engine.dispose()
        self.directory.cleanup()

    def state(self):
        with self.sessions() as session:
            return repository.project_response(session, repository.get_project(session, self.project_id))

    def start(self, key='title'):
        state = self.state()
        with self.sessions() as session, patch('app.routers.projects.get_llm_service'):
            return regenerate_slide_block(self.project_id, 's1', key,
                OutlineRevisionRequest(expected_revision=state.revision), BackgroundTasks(), session)

    def edit(self, key, text):
        with self.sessions() as session:
            return edit_slide_block(self.project_id, 's1', key,
                BlockEditRequest(expected_revision=self.state().revision, text=text), session)

    def test_other_block_edits_survive_and_export_waits(self):
        started = self.start()
        self.assertEqual(started.slides[0].blocks.title.status, 'generating')
        with self.sessions() as session:
            with self.assertRaises(HTTPException) as caught:
                export_project_pptx(self.project_id, session)
            self.assertEqual(caught.exception.status_code, 422)
        def delayed(project, slide_id, key):
            self.edit('body', 'Accepted during title generation')
            return 'Regenerated title'
        modular_regenerate.run_regeneration(self.project_id, 's1', 'title',
            started.slides[0].blocks.title.revision, delayed)
        final = self.state()
        self.assertEqual(final.slides[0].blocks.title.text, 'Regenerated title')
        self.assertEqual(final.slides[0].blocks.body.text, 'Accepted during title generation')
        self.assertEqual(final.slides[1:], started.slides[1:])
        with self.sessions() as session:
            self.assertEqual(export_project_pptx(self.project_id, session).status_code, 200)

    def test_newer_target_edit_discards_delayed_result(self):
        started = self.start()
        def delayed(project, slide_id, key):
            self.edit('title', 'Newer human title')
            return 'Obsolete model title'
        modular_regenerate.run_regeneration(self.project_id, 's1', 'title',
            started.slides[0].blocks.title.revision, delayed)
        final = self.state()
        self.assertEqual(final.slides[0].blocks.title.text, 'Newer human title')
        self.assertEqual(final.slides[0].blocks.title.status, 'ready')
        self.assertEqual(final.slides[0].blocks.body, started.slides[0].blocks.body)

    def test_failure_keeps_text_and_can_retry(self):
        before = self.state()
        started = self.start()
        def failed(*args):
            raise ValueError('deliberate model failure')
        with patch.object(modular_regenerate.logger, 'exception'):
            modular_regenerate.run_regeneration(self.project_id, 's1', 'title',
                started.slides[0].blocks.title.revision, failed)
        final = self.state()
        self.assertEqual(final.slides[0].blocks.title.text, before.slides[0].blocks.title.text)
        self.assertEqual(final.slides[0].blocks.title.status, 'error')
        self.assertIn('previous text is kept', final.slides[0].blocks.title.error)
        retry = self.start()
        modular_regenerate.run_regeneration(self.project_id, 's1', 'title',
            retry.slides[0].blocks.title.revision, lambda *args: 'Retry succeeded')
        self.assertEqual(self.state().slides[0].blocks.title.text, 'Retry succeeded')

    def test_restart_recovers_pending_block_and_preserves_accepted_text(self):
        from app.services import modular_recovery
        started = self.start()
        with patch.object(modular_recovery, 'SessionLocal', self.sessions):
            modular_recovery.recover_interrupted_work()
        final = self.state()
        self.assertEqual(final.phase, 'ready')
        self.assertEqual(final.slides[0].blocks.title.status, 'error')
        self.assertEqual(final.slides[0].blocks.title.text, started.slides[0].blocks.title.text)
        self.assertEqual(final.slides[1:], started.slides[1:])
        self.assertIn('restart', final.slides[0].blocks.title.error)

    def test_restart_marks_unfinished_slides_retryable(self):
        from app.services import modular_recovery
        from copy import deepcopy
        before = self.state()
        with self.sessions() as session:
            project = repository.get_project(session, self.project_id)
            slides = deepcopy(project.slides_json)
            slides[1]['status'] = 'generating'
            slides[2]['status'] = 'queued'
            project.slides_json = slides
            project.phase = 'building'
            session.commit()
        with patch.object(modular_recovery, 'SessionLocal', self.sessions):
            modular_recovery.recover_interrupted_work()
        final = self.state()
        self.assertEqual(final.phase, 'error')
        self.assertEqual([slide.status for slide in final.slides], ['ready', 'error', 'error', 'ready', 'ready'])
        self.assertEqual(final.slides[0], before.slides[0])

    def test_duplicate_and_source_regeneration_rejected(self):
        self.start()
        with self.assertRaises(HTTPException) as caught:
            self.start()
        self.assertEqual(caught.exception.status_code, 409)
        with self.assertRaises(HTTPException) as caught:
            self.start('source_label')
        self.assertEqual(caught.exception.status_code, 404)
