"""Tests for Retriever module."""

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from config import settings
from src.vector_store import get_vector_store, add_documents_to_store
from src.retriever import (
    get_retriever,
    retrieve_relevant_chunks,
    format_retrieved_context,
    extract_sources,
)


@pytest.fixture
def fake_embeddings():
    return DeterministicFakeEmbedding(size=32)


@pytest.fixture
def populated_vector_store(tmp_path, fake_embeddings):
    store = get_vector_store(
        persist_directory=tmp_path / "chroma_retriever",
        collection_name="retriever_test",
        embedding_function=fake_embeddings,
    )
    docs = [
        Document(
            page_content="Artificial intelligence and neural networks empower modern machines.",
            metadata={"source": "ai_primer.pdf", "page": 1, "file_type": "pdf", "chunk_id": "ai_1"},
        ),
        Document(
            page_content="Deep learning models process unstructured data such as vision and text.",
            metadata={"source": "ai_primer.pdf", "page": 2, "file_type": "pdf", "chunk_id": "ai_2"},
        ),
        Document(
            page_content="Photosynthesis is the biological process used by plants to make food.",
            metadata={"source": "biology.txt", "page": 1, "file_type": "txt", "chunk_id": "bio_1"},
        ),
    ]
    add_documents_to_store(docs, vector_store=store)
    return store


def test_get_retriever(populated_vector_store):
    retriever = get_retriever(vector_store=populated_vector_store, k=2)
    assert retriever.search_kwargs["k"] == 2
    results = retriever.invoke("neural networks")
    assert len(results) == 2


def test_retrieve_relevant_chunks_scoring(populated_vector_store):
    chunks = retrieve_relevant_chunks(
        "neural networks and machines",
        vector_store=populated_vector_store,
        k=2,
    )
    assert len(chunks) == 2
    for chunk in chunks:
        assert "relevance_score" in chunk.metadata
        assert isinstance(chunk.metadata["relevance_score"], float)


def test_retrieve_empty_query_or_empty_store(tmp_path, fake_embeddings):
    # Empty query
    assert retrieve_relevant_chunks("") == []
    assert retrieve_relevant_chunks("   ") == []

    # Empty store
    empty_store = get_vector_store(
        persist_directory=tmp_path / "empty_chroma",
        collection_name="empty",
        embedding_function=fake_embeddings,
    )
    assert retrieve_relevant_chunks("hello", vector_store=empty_store) == []


def test_format_retrieved_context():
    docs = [
        Document(
            page_content="Content snippet 1",
            metadata={"source": "doc1.pdf", "page": 4},
        ),
        Document(
            page_content="Content snippet 2",
            metadata={"source": "notes.txt"},
        ),
    ]
    formatted = format_retrieved_context(docs)
    assert "[Source 1: doc1.pdf (Page 4)]" in formatted
    assert "Content snippet 1" in formatted
    assert "[Source 2: notes.txt]" in formatted
    assert "Content snippet 2" in formatted

    empty_formatted = format_retrieved_context([])
    assert "No relevant context found" in empty_formatted


def test_extract_sources_deduplication():
    docs = [
        Document(page_content="A", metadata={"source": "doc1.pdf", "page": 1, "file_type": "pdf"}),
        Document(page_content="B", metadata={"source": "doc1.pdf", "page": 1, "file_type": "pdf"}),
        Document(page_content="C", metadata={"source": "doc1.pdf", "page": 2, "file_type": "pdf"}),
        Document(page_content="D", metadata={"source": "doc2.txt", "page": 1, "file_type": "txt"}),
    ]

    sources = extract_sources(docs)
    assert len(sources) == 3  # (doc1.pdf, 1), (doc1.pdf, 2), (doc2.txt, 1)
    sources_tuples = [(s["source"], s["page"]) for s in sources]
    assert ("doc1.pdf", 1) in sources_tuples
    assert ("doc1.pdf", 2) in sources_tuples
    assert ("doc2.txt", 1) in sources_tuples
