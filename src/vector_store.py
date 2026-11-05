"""ChromaDB vector store module for RAG Document Assistant.

Manages persistent local ChromaDB storage, document embedding ingestion,
collection statistics, and safe collection reset.
"""

from pathlib import Path
from typing import Any
import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config import settings
from src.embeddings import get_embeddings
from src.utils import generate_document_id


def get_chroma_client(
    persist_directory: Path | str | None = None,
) -> chromadb.PersistentClient:
    """Initialize and return a persistent ChromaDB client."""
    persist_dir = Path(persist_directory or settings.CHROMA_PERSIST_DIR)
    persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_dir))


def get_vector_store(
    persist_directory: Path | str | None = None,
    collection_name: str | None = None,
    embedding_function: Embeddings | None = None,
) -> Chroma:
    """Create or load a persistent Chroma vector store instance.

    Args:
        persist_directory: Path to persistent directory (defaults to config).
        collection_name: Name of the collection (defaults to config).
        embedding_function: Embeddings model instance (defaults to Gemini embeddings).

    Returns:
        Configured Chroma vector store.
    """
    col_name = collection_name or settings.CHROMA_COLLECTION_NAME
    embeddings = embedding_function or get_embeddings()
    client = get_chroma_client(persist_directory=persist_directory)

    return Chroma(
        client=client,
        collection_name=col_name,
        embedding_function=embeddings,
    )


def add_documents_to_store(
    documents: list[Document],
    vector_store: Chroma | None = None,
) -> list[str]:
    """Embed and insert or upsert documents into the vector store.

    Args:
        documents: List of chunk Document objects.
        vector_store: Optional vector store instance (defaults to standard store).

    Returns:
        List of document IDs added.
    """
    if not documents:
        return []

    store = vector_store or get_vector_store()

    # Ensure every chunk has an ID
    ids: list[str] = []
    for doc in documents:
        chunk_id = doc.metadata.get("chunk_id")
        if not chunk_id:
            parent_id = doc.metadata.get(
                "document_id",
                generate_document_id(
                    doc.page_content, doc.metadata.get("source", "doc")
                ),
            )
            chunk_idx = doc.metadata.get("chunk_index", 1)
            chunk_id = f"{parent_id}_c{chunk_idx}"
            doc.metadata["chunk_id"] = chunk_id
        ids.append(chunk_id)

    store.add_documents(documents=documents, ids=ids)
    return ids


def get_collection_stats(
    vector_store: Chroma | None = None,
) -> dict[str, Any]:
    """Retrieve statistics about the current vector collection.

    Returns:
        Dictionary containing total chunks, unique sources, and collection name.
    """
    store = vector_store or get_vector_store()
    collection = store._collection
    count = collection.count()

    sources: set[str] = set()
    if count > 0:
        data = collection.get(include=["metadatas"])
        metas = data.get("metadatas") or []
        for meta in metas:
            if meta and "source" in meta:
                sources.add(str(meta["source"]))

    return {
        "collection_name": store._collection.name,
        "total_chunks": count,
        "unique_sources": sorted(sources),
        "source_count": len(sources),
    }


def clear_vector_store(
    vector_store: Chroma | None = None,
) -> bool:
    """Safely clear all records from the vector store collection.

    Returns:
        True if the collection was cleared successfully.
    """
    store = vector_store or get_vector_store()
    collection_name = store._collection.name

    try:
        # Delete entire collection safely
        store.delete_collection()
        return True
    except Exception as e:
        # Fallback: if collection delete fails, delete all items by ID
        existing = store._collection.get()
        ids = existing.get("ids", [])
        if ids:
            store._collection.delete(ids=ids)
        return True


def delete_by_source(
    source_name: str,
    vector_store: Chroma | None = None,
) -> int:
    """Delete all chunks belonging to a specific source file or identifier.

    Args:
        source_name: Name of the source (e.g. filename).
        vector_store: Optional vector store instance.

    Returns:
        Number of remaining chunks in the collection.
    """
    store = vector_store or get_vector_store()
    store.delete(where={"source": source_name})
    return store._collection.count()
