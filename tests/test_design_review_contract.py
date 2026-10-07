"""Check the request contract separating visible copy from spoken explanations."""
import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from app.project_schemas import DesignPlan
from app.services.llm_service import OpenAILLMService
from app.services.design_quality import review_design, review_deck


class SpokenVisibleReviewTest(unittest.TestCase):
    def setUp(self):
        self.service=OpenAILLMService.__new__(OpenAILLMService)
        self.service.model='mock';self.service.client=MagicMock()
        self.service._extract_output_text=lambda response:response.output_text
        self.notes='Explain the synthetic case aloud, then transition to the camera workflow.'
        self.context={'speaker_notes':self.notes,'body':'Contamination changed from 42% to 29%. Staff review takes 18 minutes per day; maintenance takes two hours per week.',
            'story_analysis':{'slides':[{
            'slide_id':'s1','visible_priority':'Make the 42% to 29% observation and the ongoing costs clear.',
            'spoken_explanation':self.notes}]}}
        self.plan=DesignPlan(layout='editorial',emphasis='quiet',rationale='Visible argument stays concise.')

    def assert_contract(self):
        request=self.service.client.responses.create.call_args.kwargs
        system=request['input'][0]['content']
        self.assertIn('Separate visible_priority from spoken_explanation',system)
        self.assertIn('do not require every note, transition, bridge',system)
        self.assertIn('cannot rewrite approved words',system)
        self.assertIn('notes-only explanation, including a synthetic-data qualifier',system)
        self.assertIn(self.notes,json.dumps(request['input'][1]['content']))
        self.assertIn('discoverable at presentation glance',system)
        self.assertIn('Uniform prose that hides those central metrics is a composition defect',system)
        self.assertIn('never derive a new statistic',system)
        self.assertIn('a dense limits paragraph squeezed into a narrow tower',system)
        self.assertIn('long hero title dominating multiple lines',system)
        self.assertIn('Absence of clipping alone is not approval',system)

    def test_slide_review_uses_notes_as_spoken_support_not_required_slide_copy(self):
        self.service.client.responses.create.return_value=SimpleNamespace(output_text=json.dumps({
            'approved':True,'issues':[],'arrangement':'rows'}))
        with patch('app.services.design_quality.get_llm_service',return_value=self.service):
            result=review_design(b'png',[],self.plan.model_dump(),[],context=self.context)
        self.assertTrue(result['approved']);self.assert_contract()
        self.assertIn('42%',json.dumps(self.service.client.responses.create.call_args.kwargs['input'][1]['content']))
        self.assertIn('18 minutes per day',json.dumps(self.service.client.responses.create.call_args.kwargs['input'][1]['content']))

    def test_complete_deck_review_keeps_spoken_transitions_out_of_visible_requirements(self):
        self.service.client.responses.create.return_value=SimpleNamespace(output_text=json.dumps({
            'approved':True,'slides':[]}))
        project=SimpleNamespace(outline_json=[{'id':'s1','order':1,'layout_type':'content'}],
            slides_json=[{'id':'s1','blocks':{'title':{'text':'Campus waste'},'body':{'text':'How can campus waste be reduced?'}},
                'speaker_notes':self.notes}],workflow_json={'story_analysis':self.context['story_analysis']})
        with patch('app.services.design_quality.get_llm_service',return_value=self.service):
            result=review_deck(project,[('s1',b'png')])
        self.assertTrue(result['approved']);self.assert_contract()
