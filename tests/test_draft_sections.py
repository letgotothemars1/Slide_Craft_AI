import unittest
from app.services.draft_sections import draft_sections
from app.services.semantic_sections import validated_sections

class DraftSectionsTest(unittest.TestCase):
    def test_mismatched_fresh_section_never_rewrites_grounded_body(self):
        body='Waste moved from 42% to 29% over the same synthetic four-week period.'
        raw=[{'heading':'Start','text':'Waste moved from42%'},{'heading':'End','text':'to 29%.'}]
        result=draft_sections(raw,body,'s3','Observation')
        self.assertEqual(len(result),1);self.assertEqual(result[0].text,body)
        with self.assertRaisesRegex(ValueError,'retain every accepted word'):
            validated_sections(raw,body,'s3')
    def test_comparison_fallback_uses_exact_two_complete_points(self):
        body='Human review remains necessary. | Maintenance creates ongoing work.'
        result=draft_sections([],body,'s2','Tradeoffs',comparison=True)
        self.assertEqual([s.text for s in result],['Human review remains necessary.','Maintenance creates ongoing work.'])
    def test_exact_numeric_sentence_is_not_fragmented_into_start_end_panels(self):
        body='The incorrect-sorting share changed from 42% to 29% across 1,000 items.'
        raw=[{'heading':'Start','text':'The incorrect-sorting share changed from 42%'}, {'heading':'End','text':'to 29% across 1,000 items.'}]
        result=draft_sections(raw,body,'s3','Observed change')
        self.assertEqual(len(result),1)
        self.assertEqual(result[0].text,body)

    def test_valid_fresh_sections_are_preserved(self):
        raw=[{'heading':'Review','text':'Review evidence.'},{'heading':'Decide','text':'Decide next steps.'}]
        result=draft_sections(raw,'Review evidence. Decide next steps.','s2','Decision')
        self.assertEqual([s.heading for s in result],['Review','Decide'])

if __name__=='__main__':unittest.main()
