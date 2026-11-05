"""Retriever module for RAG Document Assistant.

Handles semantic similarity search, retrieval of relevant document chunks,
score attribution, source extraction, and context formatting for LLM prompts.
"""

from typing import Any
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from config import settings
from src.vector_store import get_vector_store


def get_retriever(
    vector_store: Chroma | None = None,
    k: int | None = None,
    search_type: str = "similarity",
) -> VectorStoreRetriever:
    """Return a standard LangChain VectorStoreRetriever instance.

    Args:
        vector_store: Optional vector store (defaults to persistent store).
        k: Optional top-k chunk count override (defaults to config).
        search_type: Search algorithm type ('similarity').
    """
    top_k = k if k is not None else settings.RETRIEVAL_K
    store = vector_store or get_vector_store()
    return store.as_retriever(
        search_type=search_type,
        search_kwargs={"k": top_k},
    )


def retrieve_relevant_chunks(
    query: str,
    vector_store: Chroma | None = None,
    k: int | None = None,
    score_threshold: float | None = None,
) -> list[Document]:
    """Retrieve top-k relevant chunks with similarity score metadata.

    Args:
        query: User question or search query string.
        vector_store: Optional vector store instance.
        k: Optional top-k chunk count.
        score_threshold: Optional maximum distance threshold (for distance metrics).

    Returns:
        List of retrieved Document objects with 'relevance_score' attached to metadata.
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    top_k = k if k is not None else settings.RETRIEVAL_K
    store = vector_store or get_vector_store()

    # If collection is empty, return early
    if store._collection.count() == 0:
        return []

    results_with_score = store.similarity_search_with_score(
        cleaned_query, k=top_k
    )

    retrieved: list[Document] = []
    for doc, score in results_with_score:
        if score_threshold is not None and score > score_threshold:
            continue
        # Attach score into metadata copy
        enriched_metadata = dict(doc.metadata)
        enriched_metadata["relevance_score"] = float(score)
        retrieved.append(
            Document(page_content=doc.page_content, metadata=enriched_metadata)
        )

    return retrieved


def format_retrieved_context(documents: list[Document]) -> str:
    """Format retrieved document chunks into a structured context string for prompt injection.

    Args:
        documents: List of retrieved Document chunks.

    Returns:
        Formatted context string with document numbers, source names, and pages.
    """
    if not documents:
        return "No relevant context found."

    formatted_entries: list[str] = []
    for idx, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page")
        page_str = f" (Page {page})" if page is not None else ""
        content = doc.page_content.strip()
        formatted_entries.append(
            f"[Source {idx}: {source}{page_str}]\n{content}"
        )

    return "\n\n".join(formatted_entries)


def extract_sources(documents: list[Document]) -> list[dict[str, Any]]:
    """Extract and deduplicate source citations from retrieved documents.

    Args:
        documents: List of retrieved Document chunks.

    Returns:
        List of distinct source dictionaries with source name, pages, and file type.
    """
    seen_keys: set[tuple[str, Any]] = set()
    sources: list[dict[str, Any]] = []

    for doc in documents:
        source_name = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page")
        file_type = doc.metadata.get("file_type", "unknown")
        key = (source_name, page)

        if key not in seen_keys:
            seen_keys.add(key)
            sources.append(
                {
                    "source": source_name,
                    "page": page,
                    "file_type": file_type,
                    "chunk_id": doc.metadata.get("chunk_id"),
                }
            )

    return sources
