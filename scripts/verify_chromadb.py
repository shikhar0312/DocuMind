"""Integration verification script for ChromaDB with Gemini Embeddings."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.documents import Document
from config import settings
from src.vector_store import (
    get_vector_store,
    add_documents_to_store,
    get_collection_stats,
    clear_vector_store,
)


def main() -> int:
    print("=== ChromaDB Integration Verification with Gemini ===")
    print(f"Persist Directory: {settings.CHROMA_PERSIST_DIR}")
    print(f"Collection Name: {settings.CHROMA_COLLECTION_NAME}")

    # Step 1: Initialize store
    print("\n[1/5] Initializing persistent vector store...")
    store = get_vector_store()
    print("      Vector store initialized successfully.")

    # Step 2: Clear any existing test artifacts
    print("\n[2/5] Cleaning existing collection...")
    clear_vector_store(store)
    store = get_vector_store()
    stats = get_collection_stats(store)
    print(f"      Initial collection chunk count: {stats['total_chunks']}")
    assert stats["total_chunks"] == 0

    # Step 3: Add documents with real Gemini embeddings
    print("\n[3/5] Adding sample documents with Gemini embeddings...")
    sample_docs = [
        Document(
            page_content="Retrieval-Augmented Generation (RAG) grounds LLM responses in real context.",
            metadata={"source": "rag_overview.txt", "page": 1, "chunk_id": "rag_c1"},
        ),
        Document(
            page_content="ChromaDB provides local persistent vector storage with HNSW indexing.",
            metadata={"source": "chroma_overview.txt", "page": 1, "chunk_id": "chroma_c1"},
        ),
    ]
    ids = add_documents_to_store(sample_docs, vector_store=store)
    print(f"      Added {len(ids)} chunks with IDs: {ids}")

    stats = get_collection_stats(store)
    print(f"      Updated stats: {stats}")
    assert stats["total_chunks"] == 2

    # Step 4: Perform similarity search
    print("\n[4/5] Executing similarity search...")
    query = "How does local vector indexing work?"
    results = store.similarity_search(query, k=1)
    assert len(results) == 1
    print(f"      Top match for '{query}':")
    print(f"      -> Content: {results[0].page_content}")
    print(f"      -> Source: {results[0].metadata.get('source')}")
    assert "ChromaDB" in results[0].page_content

    # Step 5: Verify persistent reload
    print("\n[5/5] Verifying persistence reload (re-instantiating client)...")
    del store
    reloaded_store = get_vector_store()
    reloaded_stats = get_collection_stats(reloaded_store)
    print(f"      Reloaded collection chunk count: {reloaded_stats['total_chunks']}")
    assert reloaded_stats["total_chunks"] == 2

    # Clean up test artifacts
    clear_vector_store(reloaded_store)
    print("\n[PASS] ChromaDB persistence, embeddings integration, and reset verified!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
