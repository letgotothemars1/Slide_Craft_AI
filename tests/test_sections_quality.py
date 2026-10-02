import unittest
from app.project_schemas import ProjectSlide, SlideBlocks, SlideBlock, SlideSection, DesignPlan, SceneElement
from app.services.design_scene import build_scene
from app.services.design_quality import render_scene
from app.services.semantic_sections import validated_sections


class SectionQualityTest(unittest.TestCase):
    def test_actual_native_renderer_preserves_three_independent_sections(self):
        sections=[SlideSection(id='review',heading='Human review',text='Staff review takes 18 minutes per day.'),SlideSection(id='maintenance',heading='Maintenance',text='Camera maintenance takes two hours per week.'),SlideSection(id='scope',heading='Evaluation scope',text='The campus sample is narrow. Transfer to another site is unknown.')]
        block=lambda text:SlideBlock(text=text,status='ready',revision=1)
        slide=ProjectSlide(id='s4',status='ready',revision=1,sections=sections,blocks=SlideBlocks(title=block('Operating trade-offs'),body=block('\n\n'.join(s.text for s in sections)),source_label=block('demo.pdf, p. 2')),design=DesignPlan(layout='editorial',emphasis='quiet',arrangement='rows',rationale='Keep each trade-off separately readable.'))
        scene=build_scene(slide,'dark_tech_pitch',4)
        png,issues=render_scene(scene)
        self.assertTrue(png.startswith(b'\x89PNG')); self.assertEqual(issues,[])
        self.assertEqual([e.text for e in scene if e.section_field=='text'],[s.text for s in sections])
        self.assertEqual(len({e.section_id for e in scene if e.section_id}),3)

    def test_renderer_reports_clipping_and_small_type(self):
        png,issues=render_scene([SceneElement(kind='text',x=0,y=0,w=5,h=1,text='This accepted content cannot fit.',color='#111111',size=1,block_key='body')])
        self.assertTrue(any('overflows' in s for s in issues));self.assertTrue(any('18pt' in s for s in issues))

    def test_partition_accepts_only_exact_text_and_complete_comparison(self):
        self.assertEqual(len(validated_sections([{'heading':'Left','text':'18 minutes.'},{'heading':'Right','text':'Two hours.'}],'18 minutes. | Two hours.','s4')),2)
        with self.assertRaises(ValueError):validated_sections([{'heading':'Wrong','text':'20 minutes.'}],'18 minutes.','s4')
        with self.assertRaises(ValueError):validated_sections([{'heading':'Merged','text':'18 minutes. Two hours.'}],'18 minutes. | Two hours.','s4')
