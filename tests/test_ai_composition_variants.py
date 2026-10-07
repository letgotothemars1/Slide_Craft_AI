"""Exactly three persisted AI alternatives, content parity, cache and stale results."""
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import repository
from app.db import Base
from app.project_schemas import ProjectCreateRequest, ProjectSlide, OutlineItem, OutlineRevisionRequest
from app.routers.projects import composition_previews, select_composition, CompositionChoiceRequest, start_composition_variants
from app.services.modular_build import build_slide_from_outline
from app.services.outline_service import starter_outline
from app.services.composition_choices import (generate_composition_variants, reserve_variants,
    run_composition_variants, content_fingerprint, variants_current)

class AIVariantsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.tmp.name)/'variants.db'}")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        with self.sessions() as s:
            p = repository.create_project(s, ProjectCreateRequest(assignment_text='Explain five slides', context_pack_text='Thesis: inspect then decide.'))
            outline = starter_outline(p.context_pack_text)
            p.outline_json = [i.model_dump() for i in outline]
            p.slides_json = [build_slide_from_outline(i).model_dump() for i in outline]
            p.phase = 'outline_draft'; p.build_mode = 'model'; s.commit(); self.id=p.id
            self.slide_id = p.slides_json[0]['id']
    def tearDown(self):
        self.engine.dispose(); self.tmp.cleanup()
    def state(self):
        with self.sessions() as s:
            return repository.project_response(s, repository.get_project(s,self.id))
    def raw_model_result(self):
        return {'variants': [{'id': identifier, 'label': 'Content-specific '+identifier,
            'description': 'Make the accepted campus argument readable.',
            'design': {'layout':'hero', 'emphasis':'quiet', 'rationale':'Accepted content determines composition.',
                'arrangement':'columns', 'composition':composition, 'focal_section_id':'',
                'title_share':None,'support_share':None}}
            for identifier, composition in zip(('selected','alternative','out_of_box'),('balanced','bands','poster'))]}
    def generate(self):
        with self.sessions() as s:
            p=repository.get_project(s,self.id)
            return generate_composition_variants(p,OutlineItem.model_validate(p.outline_json[0]),ProjectSlide.model_validate(p.slides_json[0]))
    def reserve(self):
        with self.sessions() as s:
            p=repository.get_project(s,self.id);rows=deepcopy(p.slides_json)
            reserve_variants(rows[0],p.outline_json[0]);p.slides_json=rows;s.commit()
    def worker(self, callback=None):
        with patch('app.services.modular_build.SessionLocal', self.sessions), patch('app.db.SessionLocal', self.sessions), patch('app.services.deck_design.request_structured', side_effect=callback or (lambda *a,**k:self.raw_model_result())):
            run_composition_variants(self.id,self.slide_id)
    def test_single_model_call_three_unique_with_notes_no_content_rewrite(self):
        before=self.state()
        with patch('app.services.deck_design.request_structured',return_value=self.raw_model_result()) as request:
            variants=self.generate()
        self.assertEqual(request.call_count,1)
        self.assertEqual([v['id'] for v in variants],['selected','alternative','out_of_box'])
        self.assertEqual([v['unconventional'] for v in variants],[False,False,True])
        self.assertIn('speaker_notes',request.call_args.args[1])
        self.assertEqual(self.state(),before)
    def test_overlong_metadata_is_bounded_without_truncating_content(self):
        before=self.state();raw=self.raw_model_result()
        for row in raw['variants']:
            row['label']='Campus argument  ' * 20
            row['description']='A clear supporting argument with exact evidence.\n' * 20
            row['design']['rationale']='Keep the accepted argument together and readable.  ' * 20
        with patch('app.services.deck_design.request_structured',return_value=raw) as request:
            variants=self.generate()
        self.assertEqual(len(variants),3)
        for row in variants:
            self.assertLessEqual(len(row['label']),80)
            self.assertLessEqual(len(row['description']),300)
            self.assertLessEqual(len(row['design']['rationale']),300)
            self.assertNotIn('  ',row['label'])
            self.assertNotIn('\n',row['description'])
            self.assertTrue(row['label'].endswith(('Campus','argument')))
        schema=request.call_args.args[2]['properties']['variants']['items']['properties']
        self.assertEqual(schema['label']['maxLength'],80)
        self.assertEqual(schema['description']['maxLength'],300)
        self.assertEqual(schema['design']['properties']['rationale']['maxLength'],300)
        self.assertEqual(self.state(),before)

    def test_rejects_missing_fourth_duplicate_and_same_geometry(self):
        for kind in ('missing','fourth','duplicate','geometry'):
            raw=self.raw_model_result()
            if kind=='missing':raw['variants'].pop()
            if kind=='fourth':raw['variants'].append(deepcopy(raw['variants'][0]))
            if kind=='duplicate':raw['variants'][1]['id']='selected'
            if kind=='geometry':raw['variants'][1]['design']=deepcopy(raw['variants'][0]['design'])
            with patch('app.services.deck_design.request_structured',return_value=raw):
                with self.assertRaises(ValueError):self.generate()
    def test_worker_publish_main_equals_one_choice_read_cache_and_selection(self):
        before=self.state();self.reserve();self.worker();after=self.state()
        self.assertEqual(after.slides[0].blocks,before.slides[0].blocks)
        self.assertEqual(after.slides[0].speaker_notes,before.slides[0].speaker_notes)
        self.assertEqual(after.slides[0].variants_origin,'model')
        with self.sessions() as s, patch('app.services.deck_design.request_structured') as request:
            choices=composition_previews(self.id,self.slide_id,s)
            again=composition_previews(self.id,self.slide_id,s)
            self.assertEqual(request.call_count,0);self.assertEqual(choices,again)
            self.assertEqual(len(choices),3);self.assertEqual(after.slides[0].scene,[__import__('app.project_schemas',fromlist=['SceneElement']).SceneElement.model_validate(e) for e in choices[0]['scene']])
            selected=select_composition(self.id,self.slide_id,CompositionChoiceRequest(expected_revision=after.revision,variant_id='out_of_box'),s)
        self.assertEqual(selected.slides[0].preview_design.composition,'poster')
        self.assertEqual(selected.slides[0].blocks,before.slides[0].blocks)
        self.assertEqual(selected.slides[0].scene,[__import__('app.project_schemas',fromlist=['SceneElement']).SceneElement.model_validate(e) for e in choices[2]['scene']])
        with self.sessions() as s:
            with self.assertRaises(HTTPException) as error:
                select_composition(self.id,self.slide_id,CompositionChoiceRequest(expected_revision=after.revision,variant_id='alternative'),s)
        self.assertEqual(error.exception.status_code,409)
    def test_pending_result_cannot_overwrite_changed_notes_or_new_generation(self):
        for change_token in (False,True):
            self.reserve()
            def edit(*a,**k):
                with self.sessions() as s:
                    p=repository.get_project(s,self.id);rows=deepcopy(p.slides_json)
                    if change_token:rows[0]['variants_token']='new-worker'
                    else:rows[0]['speaker_notes']='Edited during generation'
                    p.slides_json=rows;s.commit()
                return self.raw_model_result()
            self.worker(edit)
            after=self.state()
            self.assertEqual(after.slides[0].composition_variants,[])
            self.assertIsNone(after.slides[0].preview_design)
    def test_current_cache_post_reserves_no_new_provider_work(self):
        self.reserve();self.worker();before=self.state();background=BackgroundTasks()
        with self.sessions() as s,patch('app.routers.projects.get_llm_service') as provider:
            after=start_composition_variants(self.id,self.slide_id,OutlineRevisionRequest(expected_revision=before.revision),background,s)
        self.assertEqual(after,before);self.assertEqual(background.tasks,[]);provider.assert_not_called()
    def test_provider_failure_is_retryable_and_retains_accepted_words(self):
        before=self.state();self.reserve()
        with patch('app.services.modular_build.SessionLocal', self.sessions), patch('app.db.SessionLocal', self.sessions), patch('app.services.deck_design.request_structured', side_effect=RuntimeError('provider unavailable')):
            run_composition_variants(self.id,self.slide_id)
        after=self.state()
        self.assertEqual(after.slides[0].variants_status,'error')
        self.assertEqual(after.slides[0].blocks,before.slides[0].blocks)
        self.assertIsNone(after.slides[0].variants_token)

    def test_restart_releases_pending_variants_and_keeps_content(self):
        from app.services.modular_recovery import recover_interrupted_work
        before=self.state();self.reserve()
        with patch('app.services.modular_recovery.SessionLocal',self.sessions),patch('app.services.modular_build.SessionLocal',self.sessions):
            recover_interrupted_work()
        after=self.state()
        self.assertEqual(after.slides[0].variants_status,'error')
        self.assertIsNone(after.slides[0].variants_token)
        self.assertEqual(after.slides[0].blocks,before.slides[0].blocks)
        background=BackgroundTasks()
        with self.sessions() as s,patch('app.routers.projects.get_llm_service'):
            response=start_composition_variants(self.id,self.slide_id,OutlineRevisionRequest(expected_revision=after.revision),background,s)
        self.assertEqual(response.slides[0].variants_status,'generating')
        self.assertEqual(len(background.tasks),1)

    def test_edit_invalidates_visible_choices_without_model_get(self):
        self.reserve();self.worker()
        with self.sessions() as s:
            p=repository.get_project(s,self.id);rows=deepcopy(p.slides_json)
            rows[0]['blocks']['body']['text']='Changed accepted argument';p.slides_json=rows;s.commit()
            with patch('app.services.deck_design.request_structured') as request:
                self.assertEqual(composition_previews(self.id,self.slide_id,s),[])
                request.assert_not_called()
        after=self.state();self.assertEqual(after.slides[0].composition_variants,[])
        self.assertEqual(after.slides[0].variants_status,'none')

if __name__=='__main__':unittest.main()
