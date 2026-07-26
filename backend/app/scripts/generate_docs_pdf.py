from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


CURRENT_PATH = Path(__file__).resolve()
ROOT_PATH = CURRENT_PATH.parents[3]
DOCS_PATH = ROOT_PATH / "data" / "docs"
MARKDOWN_PATH = DOCS_PATH / "data_story_map.md"
PDF_PATH = DOCS_PATH / "technology_2026q1_market_update.pdf"


def _paragraph_for_block(block, styles):
    if block.startswith("# "):
        return Paragraph(block[2:], styles["Title"])
    if block.startswith("## "):
        return Paragraph(block[3:], styles["Heading2"])
    return Paragraph(block.replace("\n", "<br/>"), styles["BodyText"])


def generate_pdf_from_markdown():
    markdown_text = MARKDOWN_PATH.read_text(encoding="utf-8")
    styles = getSampleStyleSheet()
    styles["BodyText"].leading = 14

    story = []
    for block in markdown_text.split("\n\n"):
        block = block.strip()
        if not block:
            continue

        story.append(_paragraph_for_block(block, styles))
        story.append(Spacer(1, 8))

    document = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48,
    )
    document.build(story)
    return PDF_PATH


def main():
    pdf_path = generate_pdf_from_markdown()
    print(pdf_path)


if __name__ == "__main__":
    main()
