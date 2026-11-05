"""Tests for Text Splitter module."""

import pytest
from langchain_core.documents import Document

from config import settings
from src.text_splitter import get_text_splitter, split_documents, split_text


def test_get_text_splitter_defaults():
    splitter = get_text_splitter()
    assert splitter._chunk_size == settings.CHUNK_SIZE
    assert splitter._chunk_overlap == settings.CHUNK_OVERLAP


def test_get_text_splitter_invalid_overlap():
    with pytest.raises(ValueError, match="strictly less than chunk_size"):
        get_text_splitter(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError, match="strictly less than chunk_size"):
        get_text_splitter(chunk_size=100, chunk_overlap=150)


def test_split_documents_short_text():
    doc = Document(
        page_content="Short text that fits in one chunk.",
        metadata={"source": "short.txt", "page": 1, "document_id": "doc1"},
    )
    chunks = split_documents([doc], chunk_size=800, chunk_overlap=150)
    assert len(chunks) == 1
    assert chunks[0].page_content == "Short text that fits in one chunk."
    assert chunks[0].metadata["source"] == "short.txt"
    assert chunks[0].metadata["page"] == 1
    assert chunks[0].metadata["chunk_index"] == 1
    assert chunks[0].metadata["total_chunks"] == 1
    assert chunks[0].metadata["chunk_id"] == "doc1_c1"


def test_split_documents_multiple_chunks_and_metadata():
    # Construct text longer than chunk_size (100 chars per sentence, 5 sentences = 500 chars)
    sentences = [
        f"This is sentence number {i} providing detailed information for the chunking test."
        for i in range(1, 15)
    ]
    long_text = " ".join(sentences)

    doc = Document(
        page_content=long_text,
        metadata={"source": "long_doc.pdf", "page": 3, "document_id": "pdf_doc_123"},
    )

    chunk_size = 200
    chunk_overlap = 50
    chunks = split_documents([doc], chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    assert len(chunks) > 1

    # Check metadata integrity across all chunks
    for idx, chunk in enumerate(chunks, start=1):
        assert chunk.metadata["source"] == "long_doc.pdf"
        assert chunk.metadata["page"] == 3
        assert chunk.metadata["document_id"] == "pdf_doc_123"
        assert chunk.metadata["chunk_index"] == idx
        assert chunk.metadata["total_chunks"] == len(chunks)
        assert chunk.metadata["chunk_id"] == f"pdf_doc_123_c{idx}"
        assert len(chunk.page_content) <= chunk_size + 20  # splitter flexibility margin


def test_split_multiple_documents():
    doc1 = Document(
        page_content="Content for document 1. " * 20,
        metadata={"source": "doc1.txt", "document_id": "id1"},
    )
    doc2 = Document(
        page_content="Content for document 2. " * 20,
        metadata={"source": "doc2.txt", "document_id": "id2"},
    )

    chunks = split_documents([doc1, doc2], chunk_size=150, chunk_overlap=30)
    doc1_chunks = [c for c in chunks if c.metadata["source"] == "doc1.txt"]
    doc2_chunks = [c for c in chunks if c.metadata["source"] == "doc2.txt"]

    assert len(doc1_chunks) > 1
    assert len(doc2_chunks) > 1

    # Ensure chunk_index restarts per document
    assert doc1_chunks[0].metadata["chunk_index"] == 1
    assert doc1_chunks[0].metadata["chunk_id"] == "id1_c1"
    assert doc2_chunks[0].metadata["chunk_index"] == 1
    assert doc2_chunks[0].metadata["chunk_id"] == "id2_c1"


def test_split_empty_documents():
    assert split_documents([]) == []


def test_split_text_convenience():
    text = "Simple paragraph one.\n\nSimple paragraph two.\n\nSimple paragraph three."
    chunks = split_text(text, metadata={"source": "pasted_text"}, chunk_size=50, chunk_overlap=10)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.metadata["source"] == "pasted_text"
        assert "chunk_id" in c.metadata


def test_split_empty_text():
    assert split_text("") == []
    assert split_text("   \n\t  ") == []
