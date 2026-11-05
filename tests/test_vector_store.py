"""Tests for ChromaDB vector store module."""

from pathlib import Path
import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from src.vector_store import (
    get_chroma_client,
    get_vector_store,
    add_documents_to_store,
    get_collection_stats,
    clear_vector_store,
    delete_by_source,
)


@pytest.fixture
def fake_embeddings():
    return DeterministicFakeEmbedding(size=32)


@pytest.fixture
def temp_vector_store(tmp_path, fake_embeddings):
    return get_vector_store(
        persist_directory=tmp_path / "chroma",
        collection_name="test_collection",
        embedding_function=fake_embeddings,
    )


def test_add_and_query_documents(temp_vector_store):
    docs = [
        Document(
            page_content="LangChain provides modular RAG abstractions.",
            metadata={"source": "langchain.txt", "page": 1, "chunk_id": "lc_c1"},
        ),
        Document(
            page_content="Streamlit creates reactive web applications easily.",
            metadata={"source": "streamlit.txt", "page": 1, "chunk_id": "st_c1"},
        ),
    ]

    added_ids = add_documents_to_store(docs, vector_store=temp_vector_store)
    assert added_ids == ["lc_c1", "st_c1"]

    # Test similarity search
    results = temp_vector_store.similarity_search("reactive web app", k=1)
    assert len(results) == 1
    assert "Streamlit" in results[0].page_content
    assert results[0].metadata["source"] == "streamlit.txt"


def test_collection_stats(temp_vector_store):
    docs = [
        Document(page_content="Doc 1 chunk 1", metadata={"source": "report_a.pdf"}),
        Document(page_content="Doc 1 chunk 2", metadata={"source": "report_a.pdf"}),
        Document(page_content="Doc 2 chunk 1", metadata={"source": "notes.txt"}),
    ]

    add_documents_to_store(docs, vector_store=temp_vector_store)
    stats = get_collection_stats(temp_vector_store)

    assert stats["total_chunks"] == 3
    assert stats["source_count"] == 2
    assert sorted(stats["unique_sources"]) == ["notes.txt", "report_a.pdf"]


def test_delete_by_source(temp_vector_store):
    docs = [
        Document(page_content="Keep this chunk", metadata={"source": "keep.txt", "chunk_id": "k1"}),
        Document(page_content="Delete this chunk 1", metadata={"source": "remove.txt", "chunk_id": "r1"}),
        Document(page_content="Delete this chunk 2", metadata={"source": "remove.txt", "chunk_id": "r2"}),
    ]
    add_documents_to_store(docs, vector_store=temp_vector_store)

    remaining = delete_by_source("remove.txt", vector_store=temp_vector_store)
    assert remaining == 1

    stats = get_collection_stats(temp_vector_store)
    assert stats["total_chunks"] == 1
    assert stats["unique_sources"] == ["keep.txt"]


def test_clear_vector_store(temp_vector_store, tmp_path, fake_embeddings):
    docs = [
        Document(page_content="Sample knowledge", metadata={"source": "sample.txt"}),
    ]
    add_documents_to_store(docs, vector_store=temp_vector_store)
    assert get_collection_stats(temp_vector_store)["total_chunks"] == 1

    assert clear_vector_store(vector_store=temp_vector_store) is True

    # Reconnect and verify clean state
    reconnected = get_vector_store(
        persist_directory=tmp_path / "chroma",
        collection_name="test_collection",
        embedding_function=fake_embeddings,
    )
    assert get_collection_stats(reconnected)["total_chunks"] == 0


def test_persistence_across_restarts(tmp_path, fake_embeddings):
    persist_dir = tmp_path / "persisted_chroma"
    collection_name = "persistence_test"

    # Step 1: Write data in session 1
    store_session1 = get_vector_store(
        persist_directory=persist_dir,
        collection_name=collection_name,
        embedding_function=fake_embeddings,
    )
    doc = Document(
        page_content="Information that must persist across app reboots.",
        metadata={"source": "permanent.pdf", "page": 42, "chunk_id": "perm_c1"},
    )
    add_documents_to_store([doc], vector_store=store_session1)
    del store_session1

    # Step 2: Open a completely new session from the same directory
    store_session2 = get_vector_store(
        persist_directory=persist_dir,
        collection_name=collection_name,
        embedding_function=fake_embeddings,
    )
    stats = get_collection_stats(store_session2)
    assert stats["total_chunks"] == 1
    assert stats["unique_sources"] == ["permanent.pdf"]

    results = store_session2.similarity_search("reboots", k=1)
    assert len(results) == 1
    assert results[0].page_content == "Information that must persist across app reboots."
    assert results[0].metadata["page"] == 42
