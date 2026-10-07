"""Composition choices are real previews and revision-guarded presentation edits."""
import tempfile
from copy import deepcopy
import unittest
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import repository
from app.db import Base
from app.project_schemas import ProjectCreateRequest
from app.routers.projects import composition_previews, select_composition, CompositionChoiceRequest
from app.services.modular_build import build_slide_from_outline
from app.services.outline_service import starter_outline
from app.services.composition_choices import generate_composition_variants, content_fingerprint
from app.project_schemas import ProjectSlide, OutlineItem

class CompositionAPITest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.engine=create_engine(f"sqlite:///{Path(self.tmp.name)/'composition.db'}")
        Base.metadata.create_all(self.engine)
        self.sessions=sessionmaker(bind=self.engine,expire_on_commit=False)
        with self.sessions() as s:
            p=repository.create_project(s,ProjectCreateRequest(assignment_text='Explain five slides',context_pack_text='Thesis: inspect then decide.'))
            outline=starter_outline(p.context_pack_text)
            p.outline_json=[i.model_dump() for i in outline]
            slides=[build_slide_from_outline(i).model_dump() for i in outline]
            slides[0].update(speaker_notes='Explain the argument before moving to the evidence.',
                design_stage='complete',quality_issues=['Old review issue'],quality_attempts=3)
            p.slides_json=slides;p.phase='ready';s.commit();self.id=p.id
            slides=deepcopy(p.slides_json)
            item=OutlineItem.model_validate(p.outline_json[0]);slide=ProjectSlide.model_validate(slides[0])
            slides[0].update(composition_variants=generate_composition_variants(p,item,slide),
                variants_status='ready',variants_fingerprint=content_fingerprint(slide,item),
                selected_variant_id='selected',variants_origin='template')
            p.slides_json=slides;s.commit()
    def tearDown(self):
        self.engine.dispose();self.tmp.cleanup()
    def state(self):
        with self.sessions() as s:return repository.project_response(s,repository.get_project(s,self.id))
    def test_get_three_distinct_previews_with_unconventional_choice_does_not_mutate(self):
        before=self.state();slide=before.slides[0]
        with self.sessions() as s:
            previews=composition_previews(self.id,slide.id,s)
        self.assertEqual(len(previews),3)
        self.assertEqual({p['id'] for p in previews},{'selected','alternative','out_of_box'})
        self.assertEqual([p['id'] for p in previews if p['unconventional']],['out_of_box'])
        self.assertTrue(all(p['scene'] for p in previews))
        geometry=[[(e['x'],e['y'],e['w'],e['h']) for e in p['scene']] for p in previews]
        self.assertNotEqual(geometry[0],geometry[1]);self.assertNotEqual(geometry[1],geometry[2])
        for preview in previews:
            visible='\n'.join(e['text'] for e in preview['scene'] if e['kind']=='text')
            self.assertIn(slide.blocks.title.text,visible)
            self.assertIn(slide.blocks.body.text,visible)
        self.assertEqual(self.state(),before)
    def test_patch_preserves_content_notes_and_other_slides_resets_design_quality(self):
        before=self.state();slide=before.slides[0]
        with self.sessions() as s:
            after=select_composition(self.id,slide.id,CompositionChoiceRequest(expected_revision=before.revision,variant_id='out_of_box'),s)
        updated=after.slides[0]
        self.assertEqual(updated.blocks,slide.blocks)
        self.assertEqual(updated.speaker_notes,slide.speaker_notes)
        self.assertEqual(updated.sections,slide.sections)
        self.assertEqual(updated.visual,slide.visual)
        self.assertEqual(after.slides[1:],before.slides[1:])
        self.assertEqual(updated.selected_variant_id,'out_of_box')
        self.assertEqual(updated.design_stage,'none');self.assertEqual(updated.quality_issues,[])
        self.assertEqual(updated.quality_attempts,0);self.assertIsNone(updated.design)
        self.assertEqual(updated.preview_design.composition,'poster')
        self.assertNotEqual(updated.scene,slide.scene)
        self.assertEqual(after.phase,'outline_draft');self.assertEqual(after.workflow.stage,'review')
        with self.sessions() as s:
            stored=repository.get_project(s,self.id).slides_json[0]
            self.assertEqual(stored['selected_variant_id'],'out_of_box')
            self.assertIsNone(stored.get('preview_design'))
            with self.assertRaises(HTTPException) as caught:
                select_composition(self.id,slide.id,CompositionChoiceRequest(expected_revision=before.revision,variant_id='alternative'),s)
        self.assertEqual(caught.exception.status_code,409)
        self.assertEqual(self.state().slides[0].selected_variant_id,'out_of_box')

    def test_reselecting_current_variant_preserves_completed_design_and_revision(self):
        with self.sessions() as session:
            project=repository.get_project(session,self.id)
            rows=deepcopy(project.slides_json)
            rows[0].update(design=rows[0]['composition_variants'][0]['design'],design_status='ready')
            project.slides_json=rows
            session.commit()
        before=self.state()
        with self.sessions() as session:
            after=select_composition(self.id,before.slides[0].id,
                CompositionChoiceRequest(expected_revision=before.revision,variant_id='selected'),session)
        self.assertEqual(after,before)
        self.assertEqual(self.state(),before)

    def test_legacy_composition_payload_selects_an_existing_variant(self):
        from app.services.ai_design import initial_design
        before=self.state()
        with self.sessions() as session:
            after=select_composition(self.id,before.slides[0].id,
                CompositionChoiceRequest(expected_revision=before.revision,composition='poster'),session)
            project=repository.get_project(session,self.id)
            plan=initial_design(project,after.outline[0],project.slides_json[0],[])
        self.assertEqual(after.slides[0].selected_variant_id,'out_of_box')
        self.assertEqual(plan.composition,'poster')
        self.assertIsNone(after.slides[0].composition_preference)

    def test_unselected_legacy_variants_are_not_reported_as_current(self):
        from app.services.composition_choices import variants_current
        with self.sessions() as session:
            project=repository.get_project(session,self.id)
            rows=deepcopy(project.slides_json)
            rows[0]['selected_variant_id']=None
            self.assertFalse(variants_current(rows[0],project.outline_json[0]))

if __name__=='__main__':unittest.main()
