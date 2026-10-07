"""The first draft must visibly retain evidence qualifications without filler."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from app.services.modular_slide_llm import generate_slide_body
from app.services.project_outline_llm import generate_model_outline, _Draft
from app.services.outline_service import starter_outline

class ContentPromptGroundingTest(unittest.TestCase):
    def test_fictional_scope_and_short_grounded_notes_in_content_prompt(self):
        outline=starter_outline('Thesis: cautious decision')
        project=SimpleNamespace(outline_json=[s.model_dump() for s in outline],assignment_text='Explain the pilot.',context_pack_text='NorthCampus is fictional. Pilot figures are synthetic.')
        with patch('app.services.modular_slide_llm._model_body',return_value='A fictional campus case exploring a cautious decision.') as call:
            generate_slide_body(project,outline[0],on_notes=lambda _:None)
        system,user=call.call_args.args[:2]
        self.assertIn('visible on the first cover body',system)
        self.assertIn('retain it alongside affected numerical claims',system)
        self.assertIn('Never label real data synthetic',system)
        self.assertIn('never pad to meet a word count',system)
        self.assertIn('rather than generic instructions',system)
        self.assertIn('NorthCampus is fictional',user)
    def test_first_outline_title_qualification_is_conditional_on_grounded_input(self):
        draft=_Draft(slides=[{'title':f'Claim {i}','purpose':'Explain an observation','key_message':'One grounded observation','layout_type':'content'} for i in range(5)])
        with patch('app.services.project_outline_llm._request_draft',return_value=draft) as call:
            generate_model_outline('Five slides','A real observed pilot, not a fabricated example.',[])
        system=call.call_args.args[0]
        self.assertIn('explicitly fictional or synthetic',system)
        self.assertIn('in the first slide title',system)
        self.assertIn('never invent an unsupported evidence label',system)

if __name__=='__main__':unittest.main()
