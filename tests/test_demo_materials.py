"""The synthetic demo fixture must remain page-aware and internally consistent."""

import unittest
from pathlib import Path

from pypdf import PdfReader

from app.routers.projects import demo_materials
from app.services.outline_service import starter_outline


ROOT = Path(__file__).resolve().parents[1]


class DemoMaterialsTest(unittest.TestCase):
    def test_two_page_source_and_starter_outline(self) -> None:
        materials = demo_materials()
        self.assertIn("promising, not proven", materials["assignment_text"])
        self.assertIn("synthetic", materials["context_pack_text"].lower())
        pdf = PdfReader(ROOT / "project-instructions" / "fixtures" / "demo-source.pdf")
        self.assertEqual(len(pdf.pages), 2)
        self.assertIn("42%", pdf.pages[0].extract_text())
        self.assertIn("29%", pdf.pages[0].extract_text())
        self.assertIn("18 minutes", pdf.pages[1].extract_text())
        self.assertIn("two hours", pdf.pages[1].extract_text())
        outline = starter_outline(materials["context_pack_text"])
        self.assertEqual(len(outline), 5)
        self.assertIn("North Campus", outline[0].title)
        self.assertIn("promising, not proven", outline[1].key_message)
        self.assertIn("42%", outline[2].key_message)
        self.assertIn(" | ", outline[3].key_message)
        self.assertTrue(all(not item.evidence_refs for item in outline))


if __name__ == "__main__":
    unittest.main()
