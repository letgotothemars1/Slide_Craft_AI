import unittest
from app.services.quality_model_options import quality_model_options


class QualityModelOptionsTest(unittest.TestCase):
    def test_verified_families_and_dated_snapshots_use_high_without_temperature(self):
        for family in ('gpt-5.4', 'gpt-5.4-mini', 'gpt-5.4-nano'):
            for model in (family, family+'-2026-03-17'):
                with self.subTest(model=model):
                    self.assertEqual(quality_model_options(model,.2),{'reasoning':{'effort':'high'}})

    def test_unverified_models_keep_existing_temperature(self):
        for model in ('mock','gpt-4.1','gpt-5-mini','gpt-5.4-pro','gpt-5.4-mini-preview',
                      'gpt-5.4-mini-2026-03-17-extra','gpt-5.4-miniature','claude-sonnet'):
            with self.subTest(model=model):
                self.assertEqual(quality_model_options(model,.3),{'temperature':.3})
