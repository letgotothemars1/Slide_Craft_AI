"""Rebuild the two-page, entirely synthetic course-demo PDF."""

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "project-instructions" / "fixtures" / "demo-source.txt"
OUTPUT = ROOT / "project-instructions" / "fixtures" / "demo-source.pdf"


def _clean(text: str) -> str:
    return text.replace("—", "-").replace("–", "-").replace("“", '"').replace("”", '"')


def build() -> Path:
    source = _clean(SOURCE.read_text(encoding="utf-8"))
    title, remainder = source.split("PAGE 1 - SETTING AND OBSERVATIONS", 1)
    page_one, page_two = remainder.split("PAGE 2 - WORKFLOW AND LIMITS", 1)
    dark = colors.HexColor("#17243C")
    accent = colors.HexColor("#0E7490")
    pdfmetrics.registerFont(TTFont("DemoSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DemoSansBold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    title_style = ParagraphStyle("title", fontName="DemoSansBold", fontSize=19, leading=25, textColor=dark, spaceAfter=18)
    section_style = ParagraphStyle("section", fontName="DemoSansBold", fontSize=12, leading=17, textColor=accent, spaceAfter=12)
    body_style = ParagraphStyle("body", fontName="DemoSans", fontSize=11, leading=18, textColor=dark, spaceAfter=14)
    note_style = ParagraphStyle("note", fontName="DemoSansBold", fontSize=9, leading=15, textColor=colors.HexColor("#92400E"), spaceAfter=15)

    def add_paragraphs(story: list, text: str) -> None:
        for paragraph in text.strip().split("\n\n"):
            if paragraph.strip():
                story.append(Paragraph(escape(paragraph.strip()), body_style))

    story = [Paragraph(escape(title.strip()), title_style),
             Paragraph("FICTIONAL DATA - SOFTWARE DEMONSTRATION ONLY", note_style),
             Paragraph("Page 1 - Setting and observations", section_style)]
    add_paragraphs(story, page_one)
    story += [PageBreak(),
              Paragraph(escape(title.strip()), title_style),
              Paragraph("FICTIONAL DATA - SOFTWARE DEMONSTRATION ONLY", note_style),
              Paragraph("Page 2 - Workflow and limits", section_style)]
    add_paragraphs(story, page_two)

    def footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setStrokeColor(accent)
        canvas.line(58, 48, 537, 48)
        canvas.setFont("DemoSans", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(58, 32, "SlideCraft AI - team-authored synthetic source")
        canvas.drawRightString(537, 32, f"Page {doc.page} of 2")
        canvas.restoreState()

    class DemoDocTemplate(SimpleDocTemplate):
        def afterPage(self) -> None:
            footer(self.canv, self)

    document = DemoDocTemplate(str(OUTPUT), pagesize=(595.28, 841.89),
                               leftMargin=58, rightMargin=58, topMargin=64, bottomMargin=60,
                               title="Synthetic North Campus sorting pilot")
    document.build(story)
    return OUTPUT


if __name__ == "__main__":
    print(build())
