"""Tests for RAG Chain module."""

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from src.vector_store import get_vector_store, add_documents_to_store
from src.rag_chain import get_rag_prompt, build_rag_chain, ask_rag, RAGResponse


@pytest.fixture
def fake_embeddings():
    return DeterministicFakeEmbedding(size=32)


@pytest.fixture
def populated_vector_store(tmp_path, fake_embeddings):
    store = get_vector_store(
        persist_directory=tmp_path / "chroma_rag",
        collection_name="rag_chain_test",
        embedding_function=fake_embeddings,
    )
    docs = [
        Document(
            page_content="LangChain provides modular components for building RAG applications.",
            metadata={"source": "rag_guide.pdf", "page": 3, "file_type": "pdf", "chunk_id": "c1"},
        ),
        Document(
            page_content="ChromaDB stores embeddings persistently on disk using sqlite and parquet.",
            metadata={"source": "chroma_docs.txt", "page": 1, "file_type": "txt", "chunk_id": "c2"},
        ),
    ]
    add_documents_to_store(docs, vector_store=store)
    return store


def test_rag_prompt_formatting():
    prompt = get_rag_prompt()
    messages = prompt.format_messages(
        context="Sample retrieved context",
        question="What is this document about?",
    )
    assert len(messages) == 2
    assert "Sample retrieved context" in messages[0].content
    assert "What is this document about?" in messages[1].content


def test_ask_rag_empty_question():
    resp = ask_rag("")
    assert "Please enter a question" in resp.answer
    assert resp.has_sufficient_context is False


def test_ask_rag_empty_vector_store(tmp_path, fake_embeddings):
    empty_store = get_vector_store(
        persist_directory=tmp_path / "empty_store",
        collection_name="empty",
        embedding_function=fake_embeddings,
    )
    resp = ask_rag("What is LangChain?", vector_store=empty_store)
    assert "No documents have been uploaded yet" in resp.answer
    assert resp.has_sufficient_context is False


def test_ask_rag_success_flow(populated_vector_store):
    fake_llm = FakeListChatModel(
        responses=[
            "Based on Source 1 (Page 3), LangChain provides modular components for RAG."
        ]
    )

    resp = ask_rag(
        question="What does LangChain provide?",
        vector_store=populated_vector_store,
        llm=fake_llm,
    )

    assert "modular components" in resp.answer
    assert resp.has_sufficient_context is True
    assert len(resp.sources) > 0
    rag_source = next(s for s in resp.sources if s["source"] == "rag_guide.pdf")
    assert rag_source["page"] == 3


def test_ask_rag_insufficient_context_detection(populated_vector_store):
    fake_llm = FakeListChatModel(
        responses=[
            "I do not have enough information in the provided documents to answer this question."
        ]
    )

    resp = ask_rag(
        question="What is the capital of France?",
        vector_store=populated_vector_store,
        llm=fake_llm,
    )

    assert "do not have enough information" in resp.answer
    assert resp.has_sufficient_context is False
    assert resp.sources == []


def test_rag_response_to_dict():
    response = RAGResponse(
        answer="Test answer",
        sources=[{"source": "test.txt", "page": 1}],
        retrieved_documents=[Document(page_content="Content")],
        has_sufficient_context=True,
    )
    d = response.to_dict()
    assert d["answer"] == "Test answer"
    assert d["has_sufficient_context"] is True
    assert d["total_chunks_retrieved"] == 1
