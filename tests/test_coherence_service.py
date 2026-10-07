import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import repository
from app.db import Base
from app.project_schemas import ProjectCreateRequest
from app.services import ai_design, modular_build, modular_recovery
from app.services.modular_build import build_slide_from_outline
from app.services.outline_service import starter_outline
from app.services.coherence_service import cached_coherence, review_coherence


def fixture():
    outline = [r.model_dump() for r in starter_outline('A synthetic pilot reduced errors from 42% to 29%.')]
    slides = [build_slide_from_outline(r).model_dump() for r in starter_outline('A synthetic pilot reduced errors from 42% to 29%.')]
    for slide in slides:
        slide['speaker_notes'] = 'Explain the synthetic pilot cautiously; errors changed from 42% to 29%, not proof of causation.'
    return SimpleNamespace(assignment_text='Explain a pilot.', context_pack_text='Synthetic four-week pilot: errors changed from 42% to 29%.',
        outline_json=outline, slides_json=slides, build_mode='model', workflow_json={})


class CoherenceServiceTest(unittest.TestCase):
    def test_numeric_contradiction_blocks_even_inconsistent_approval(self):
        p = fixture()
        p.slides_json[0]['speaker_notes'] = 'Errors fell from 42% to 9% in a real study.'
        raw = {'approved': True, 'summary': 'A material numeric and evidence-status discrepancy.', 'findings': [{
            'slide_id': 's1', 'severity': 'blocking', 'category': 'contradiction',
            'issue': 'Notes say 9% and a real study; supplied evidence says 29% and synthetic.'}]}
        before = deepcopy(p.slides_json)
        with patch('app.services.deck_design.request_structured', return_value=raw) as request:
            result = review_coherence(p)
        self.assertFalse(result['approved'])
        self.assertEqual(p.slides_json, before)
        self.assertIn('42% to 9%', str(request.call_args.args[1]))
        self.assertIn('qualifiers', request.call_args.args[0])

    def test_grounded_spoken_detail_does_not_require_copying_notes_to_slide(self):
        p = fixture()
        with patch('app.services.deck_design.request_structured', return_value={
            'approved': True, 'summary': 'The spoken qualification explains the visible result.', 'findings': []}) as request:
            result = review_coherence(p)
        self.assertTrue(result['approved'])
        self.assertIn('do NOT need to be copied', request.call_args.args[0])
        p.workflow_json['coherence_review'] = result
        self.assertEqual(cached_coherence(p), result)
        p.slides_json[0]['speaker_notes'] += ' A new conflicting claim.'
        self.assertIsNone(cached_coherence(p))

    def test_missing_notes_are_blocking_and_unknown_slide_is_rejected(self):
        p = fixture(); p.slides_json[0]['speaker_notes'] = ''
        with patch('app.services.deck_design.request_structured', return_value={'approved': True, 'summary': 'Agrees.', 'findings': []}):
            result = review_coherence(p)
        self.assertFalse(result['approved']); self.assertEqual(result['findings'][0]['category'], 'missing_notes')
        with patch('app.services.deck_design.request_structured', return_value={'approved': False, 'summary': 'Mismatch.', 'findings': [{
            'slide_id': 'not-existing', 'severity': 'blocking', 'category': 'contradiction', 'issue': 'Mismatch.'}]}):
            with self.assertRaises(ValueError): review_coherence(p)

    def test_cache_changes_on_context_body_sections_and_mode_but_not_theme(self):
        p = fixture()
        with patch('app.services.deck_design.request_structured', return_value={'approved': True, 'summary': 'Agrees.', 'findings': []}):
            p.workflow_json['coherence_review'] = review_coherence(p)
        p.theme = 'dark_tech'; self.assertIsNotNone(cached_coherence(p))
        for mutate in (lambda x: setattr(x, 'context_pack_text', 'New evidence'),
            lambda x: x.slides_json[0]['blocks']['body'].update(text='Changed claim'),
            lambda x: x.outline_json[0].update(evidence_refs=[{'excerpt': 'Different evidence'}]),
            lambda x: x.slides_json[0].update(sections=[{'id': 'new', 'heading': 'Claim', 'text': 'Different'}]),
            lambda x: setattr(x, 'build_mode', 'template')):
            changed = deepcopy(p); mutate(changed); self.assertIsNone(cached_coherence(changed))

    def test_template_does_not_claim_model_verification(self):
        p = fixture(); p.build_mode = 'template'
        with patch('app.services.deck_design.request_structured', side_effect=AssertionError('No model in template mode')):
            result = review_coherence(p)
        self.assertEqual(result['mode'], 'template'); self.assertIn('unavailable', result['summary'])

    def test_absent_bar_visual_blocks_optimistic_ai_and_approved_cache(self):
        from app.services.coherence_service import coherence_fingerprint
        p=fixture();p.slides_json[2]['visual']=None
        p.slides_json[2]['speaker_notes']='The bar visual helps the audience see the direction of the change quickly.'
        optimistic={'approved':True,'summary':'Content and notes agree.','findings':[]}
        with patch('app.services.deck_design.request_structured',return_value=optimistic):
            result=review_coherence(p)
        self.assertFalse(result['approved'])
        finding=next(f for f in result['findings'] if f['slide_id']=='s3')
        self.assertEqual(finding['severity'],'blocking');self.assertIn('no accepted visual',finding['issue'])
        p.workflow_json['coherence_review']={**optimistic,'fingerprint':coherence_fingerprint(p),'mode':'model'}
        self.assertIsNone(cached_coherence(p))

    def test_negated_or_proposed_chart_does_not_trigger_existing_visual_guard(self):
        p=fixture();p.slides_json[0]['visual']=None
        for notes in ('There is no bar chart on this slide.', 'We could use a chart in a later version.',
            'The chart could show the change in a future version.', 'This slide does not show a chart.',
            'Imagine the bar visual helps the audience compare the numbers.'):
            with self.subTest(notes=notes):
                p.slides_json[0]['speaker_notes']=notes
                with patch('app.services.deck_design.request_structured',return_value={'approved':True,'summary':'Agrees.','findings':[]}):
                    self.assertTrue(review_coherence(p)['approved'])

    def test_old_audit_version_cannot_reuse_approval(self):
        import hashlib,json
        from app.services.coherence_service import coherence_input
        p=fixture()
        old=hashlib.sha256(json.dumps(coherence_input(p),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        p.workflow_json['coherence_review']={'approved':True,'summary':'Previous audit.','findings':[],'fingerprint':old,'mode':'model'}
        self.assertIsNone(cached_coherence(p))

    def test_blocking_audit_stops_design_and_preserves_content(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory)/'coherence.db'}")
            Base.metadata.create_all(engine); sessions = sessionmaker(bind=engine)
            p = fixture()
            with sessions() as session:
                project = repository.create_project(session, ProjectCreateRequest(assignment_text=p.assignment_text, context_pack_text=p.context_pack_text))
                project.outline_json = p.outline_json; project.slides_json = p.slides_json
                rows = deepcopy(project.slides_json)
                for row in rows: row['design_status'] = 'queued'
                project.slides_json = rows; project.build_mode = 'model'; project.phase = 'designing'; project_id = project.id; session.commit()
            raw = {'approved': False, 'summary': 'Numeric contradiction.', 'findings': [{
                'slide_id': 's1', 'severity': 'blocking', 'category': 'contradiction', 'issue': 'Notes contradict the displayed pilot result.'}]}
            from contextlib import ExitStack
            with ExitStack() as stack:
                for module in (ai_design, modular_build, modular_recovery): stack.enter_context(patch.object(module, 'SessionLocal', sessions))
                stack.enter_context(patch('app.services.deck_design.request_structured', return_value=raw))
                design = stack.enter_context(patch('app.services.deck_design.generate_deck_design', side_effect=AssertionError('No design for contradictory notes')))
                ai_design.run_design(project_id)
            with sessions() as session:
                current = repository.get_project(session, project_id)
                self.assertEqual(current.phase, 'outline_draft')
                self.assertFalse(current.workflow_json['coherence_review']['approved'])
                self.assertEqual([r['blocks'] for r in current.slides_json], [r['blocks'] for r in p.slides_json])
                self.assertEqual([r['speaker_notes'] for r in current.slides_json], [r['speaker_notes'] for r in p.slides_json])
                self.assertTrue(all(r['design_status'] == 'error' for r in current.slides_json))
                self.assertIsNotNone(repository.project_response(session, current).workflow.coherence_review)
                changed = deepcopy(current.slides_json)
                changed[0]['speaker_notes'] += ' Edited after the agreement check.'
                current.slides_json = changed; session.commit()
                self.assertIsNone(repository.project_response(session, current).workflow.coherence_review)
            design.assert_not_called(); engine.dispose()
