import unittest
from tests.test_composition_library import sample_slide
from app.services.design_scene import build_scene


class AdaptiveGeometryTest(unittest.TestCase):
    def test_complementary_process_paths_are_forked_without_rewriting(self):
        from app.project_schemas import DraftVisual
        from app.services.design_quality import render_scene
        labels=['Scan item','Auto-route if confident','Staff review if uncertain']
        slide=sample_slide('bands',visual=DraftVisual(kind='process',labels=labels,values=[],unit=''))
        scene=build_scene(slide,'clean_editorial',2)
        nodes=[next(e for e in scene if e.text==label) for label in labels]
        self.assertEqual(nodes[1].x,nodes[2].x)
        self.assertNotEqual(nodes[1].y,nodes[2].y)
        self.assertLess(nodes[0].x,nodes[1].x)
        self.assertEqual([e.text for e in scene if e.section_field=='text'],[s.text for s in slide.sections])
        self.assertEqual(render_scene(scene)[1],[])

    def test_model_can_adjust_poster_width_without_changing_content(self):
        slide=sample_slide('poster')
        scenes=[]
        for share in (.30,.55):
            slide.design.title_share=share
            scene=build_scene(slide,'clean_editorial',1)
            self.assertEqual([e.text for e in scene if e.section_field=='text'],[s.text for s in slide.sections])
            for e in scene:
                self.assertLessEqual(e.x+e.w,100)
                self.assertGreater(e.w,0)
            scenes.append(scene)
        self.assertNotEqual([(e.x,e.w) for e in scenes[0]],[(e.x,e.w) for e in scenes[1]])

    def test_support_share_assigns_space_without_merging_sections(self):
        slide=sample_slide('feature')
        widths=[]
        for share in (.35,.70):
            slide.design.support_share=share
            scene=build_scene(slide,'clean_editorial',1)
            widths.append(next(e.w for e in scene if e.section_id=='scope' and e.section_field=='text'))
            self.assertEqual([e.text for e in scene if e.section_field=='text'],[s.text for s in slide.sections])
        self.assertGreater(widths[1],widths[0])

    def test_percentage_comparison_remains_focal_with_separate_caveat(self):
        from app.project_schemas import SlideSection
        from app.services.design_quality import render_scene
        slide=sample_slide()
        slide.sections=[SlideSection(id='observed',heading='Observed change',text='Synthetic four-week case: the observed incorrect-sorting share changed from 42% to 29% across 1,000 inspected items per week (source PDF, p. 1).'),SlideSection(id='limits',heading='Interpretation limit',text='This is an observation, not proof of causation, because the pilot had no randomized control group.')]
        geometries=[]
        for composition in ('balanced','feature','poster'):
            slide.design.composition=composition
            slide.design.focal_section_id='observed'
            scene=build_scene(slide,'clean_editorial',3)
            self.assertEqual([e.text for e in scene if e.section_field=='text'],[s.text for s in slide.sections])
            self.assertEqual([e.text for e in scene if e.text in ('42%','29%')],['42%','29%'])
            self.assertTrue(all(e.size>=2 for e in scene if e.section_field=='text'))
            self.assertEqual(render_scene(scene)[1],[])
            geometries.append([(e.kind,e.x,e.y,e.w,e.h) for e in scene])
        self.assertEqual(len({str(g) for g in geometries}),3)

    def test_daily_and_weekly_metrics_share_one_section_without_losing_hierarchy(self):
        from app.project_schemas import SlideSection
        from app.services.design_quality import render_scene
        slide=sample_slide('bands')
        slide.sections=[SlideSection(id='review',heading='Staff review',text='Staff review is the main human check: uncertain items are sent to staff instead of being decided automatically.'),SlideSection(id='load',heading='Maintenance load',text='In this synthetic case, that review takes 18 minutes per day, and camera maintenance adds two hours per week (source PDF, p. 2).')]
        scene=build_scene(slide,'clean_editorial',4)
        self.assertTrue({'18','two','minutes per day','hours per week'}<=set(e.text for e in scene))
        self.assertEqual([e.text for e in scene if e.section_field=='text'],[s.text for s in slide.sections])
        self.assertTrue(all(e.size>=2 for e in scene if e.section_field=='text'))
        self.assertEqual(render_scene(scene)[1],[])

    def test_percentage_rows_are_a_real_different_content_arrangement(self):
        from app.project_schemas import SlideSection
        from app.services.design_quality import render_scene
        slide=sample_slide('balanced')
        slide.sections=[SlideSection(id='observed',heading='Observed change',text='Synthetic four-week case: the observed incorrect-sorting share changed from 42% to 29% across 1,000 inspected items per week (source PDF, p. 1).'),SlideSection(id='limits',heading='Interpretation limit',text='This is an observation, not proof of causation, because the pilot had no randomized control group.')]
        cols=build_scene(slide,'clean_editorial',3)
        slide.design.arrangement='rows'
        rows=build_scene(slide,'clean_editorial',3)
        self.assertNotEqual([(e.x,e.y,e.w) for e in cols if e.section_field=='text'],[(e.x,e.y,e.w) for e in rows if e.section_field=='text'])
        self.assertEqual([e.text for e in rows if e.section_field=='text'],[s.text for s in slide.sections])
        self.assertTrue(all(e.size>=2 for e in rows if e.section_field=='text'))
        self.assertEqual(render_scene(rows)[1],[])
        slide.design.focal_section_id='limits'
        rows=build_scene(slide,'clean_editorial',3)
        positions={e.section_id:e.y for e in rows if e.section_field=='text'}
        self.assertLess(positions['limits'],positions['observed'])
        self.assertEqual([e.text for e in rows if e.section_field=='text'],[s.text for s in slide.sections])
