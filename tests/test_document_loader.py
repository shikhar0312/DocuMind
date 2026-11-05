"""Tests for Document Loader module."""

import io
import pytest
from pathlib import Path
import docx
import pypdf
from reportlab.pdfgen import canvas

from src.document_loader import (
    load_pdf,
    load_docx,
    load_txt,
    load_manual_text,
    load_document,
)


def _create_sample_pdf(pages_text: list[str]) -> io.BytesIO:
    """Helper to generate an in-memory PDF with specified text per page."""
    bio = io.BytesIO()
    c = canvas.Canvas(bio)
    for text in pages_text:
        c.drawString(100, 700, text)
        c.showPage()
    c.save()
    bio.seek(0)
    return bio


def _create_sample_docx(paragraphs: list[str], table_rows: list[list[str]] | None = None) -> io.BytesIO:
    """Helper to generate an in-memory DOCX document."""
    doc = docx.Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    if table_rows:
        t = doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
        for r_idx, row in enumerate(table_rows):
            for c_idx, cell_value in enumerate(row):
                t.cell(r_idx, c_idx).text = cell_value
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio


# =================== TXT Tests ===================

def test_load_txt_success():
    content = "Hello, this is a test document for DocuMind RAG."
    docs = load_txt(content.encode("utf-8"), filename="sample.txt")
    assert len(docs) == 1
    assert docs[0].page_content == content
    assert docs[0].metadata["source"] == "sample.txt"
    assert docs[0].metadata["page"] == 1
    assert docs[0].metadata["file_type"] == "txt"
    assert "document_id" in docs[0].metadata


def test_load_txt_empty_error():
    with pytest.raises(ValueError, match="empty or contains only whitespace"):
        load_txt(b"   \n\t  ", filename="empty.txt")


# =================== Manual Text Tests ===================

def test_load_manual_text_success():
    raw_text = "   This is some manual text input.   \n\nWith multiple lines.  "
    docs = load_manual_text(raw_text, source_name="user_input")
    assert len(docs) == 1
    assert "This is some manual text input." in docs[0].page_content
    assert docs[0].metadata["source"] == "user_input"
    assert docs[0].metadata["page"] == 1
    assert docs[0].metadata["file_type"] == "text"


def test_load_manual_text_empty_error():
    with pytest.raises(ValueError, match="empty or contains only whitespace"):
        load_manual_text("    ")


# =================== DOCX Tests ===================

def test_load_docx_success():
    paragraphs = ["First paragraph of Word doc.", "Second paragraph with details."]
    table = [["Header 1", "Header 2"], ["Data A", "Data B"]]
    stream = _create_sample_docx(paragraphs, table)

    docs = load_docx(stream, filename="report.docx")
    assert len(docs) == 1
    assert "First paragraph of Word doc." in docs[0].page_content
    assert "Header 1 | Header 2" in docs[0].page_content
    assert docs[0].metadata["source"] == "report.docx"
    assert docs[0].metadata["file_type"] == "docx"


def test_load_docx_empty_error():
    stream = _create_sample_docx([])
    with pytest.raises(ValueError, match="No text content found in DOCX"):
        load_docx(stream, filename="empty.docx")


# =================== PDF Tests ===================

def test_load_pdf_multipage_success():
    pages = ["Page 1 content about machine learning.", "Page 2 content about retrieval models."]
    stream = _create_sample_pdf(pages)

    docs = load_pdf(stream, filename="paper.pdf")
    assert len(docs) == 2
    assert "Page 1 content" in docs[0].page_content
    assert docs[0].metadata["page"] == 1
    assert docs[0].metadata["total_pages"] == 2
    assert docs[0].metadata["source"] == "paper.pdf"
    assert docs[0].metadata["file_type"] == "pdf"

    assert "Page 2 content" in docs[1].page_content
    assert docs[1].metadata["page"] == 2


def test_load_pdf_empty_error():
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)
    bio = io.BytesIO()
    writer.write(bio)
    bio.seek(0)

    with pytest.raises(ValueError, match="No extractable text found"):
        load_pdf(bio, filename="scanned.pdf")


# =================== Unified load_document Dispatcher ===================

def test_load_document_dispatch():
    txt_stream = io.BytesIO(b"Document dispatch text test.")
    docs = load_document(txt_stream, filename="notes.txt")
    assert len(docs) == 1
    assert docs[0].metadata["file_type"] == "txt"

    with pytest.raises(ValueError, match="Unsupported file format"):
        load_document(io.BytesIO(b"image data"), filename="picture.png")


def test_load_from_filepath(tmp_path):
    # Test reading from an actual disk Path object
    txt_file = tmp_path / "disk_test.txt"
    txt_file.write_text("Hello from file on disk!", encoding="utf-8")

    docs = load_document(txt_file)
    assert len(docs) == 1
    assert docs[0].page_content == "Hello from file on disk!"
    assert docs[0].metadata["source"] == "disk_test.txt"
    assert docs[0].metadata["file_type"] == "txt"
