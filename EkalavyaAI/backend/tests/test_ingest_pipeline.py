"""Test the PDF ingestion dry-run path (parse + chunk, no external services)."""
import pytest

from rag.ingestion import PDFIngestionPipeline


def _make_pdf(path):
    import fitz
    doc = fitz.open()
    for title, body in [
        ("Chapter 1: Ratio and Proportion", "A ratio compares two quantities. " * 40),
        ("Chapter 2: Indices and Logarithm", "Logarithm is the inverse of exponentiation. " * 40),
    ]:
        page = doc.new_page()
        page.insert_text((72, 72), title, fontsize=16)
        page.insert_textbox(fitz.Rect(72, 100, 520, 760), body, fontsize=11)
    doc.save(str(path))
    doc.close()


@pytest.mark.asyncio
async def test_analyze_pdf_counts(tmp_path):
    pdf = tmp_path / "sample.pdf"
    _make_pdf(pdf)

    pipeline = PDFIngestionPipeline()
    report = await pipeline.analyze_pdf(str(pdf), "CA_FOUNDATION", "Business Mathematics")

    assert report["file"] == "sample.pdf"
    assert report["exam"] == "CA_FOUNDATION"
    assert report["pages"] >= 1
    assert report["chunks"] >= 1
    assert len(report["chapters"]) >= 1
