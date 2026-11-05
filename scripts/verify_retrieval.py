"""Verification script for Retriever with Gemini Embeddings."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.documents import Document
from src.vector_store import get_vector_store, add_documents_to_store, clear_vector_store
from src.retriever import retrieve_relevant_chunks, format_retrieved_context, extract_sources


def main() -> int:
    print("=== Retrieval Verification with Live Gemini Embeddings ===")

    store = get_vector_store()
    clear_vector_store(store)
    store = get_vector_store()

    # Step 1: Ingest distinct topic documents
    sample_docs = [
        Document(
            page_content="Quantum computing leverages superposition and entanglement to solve certain classes of mathematical problems exponentially faster than classical computers.",
            metadata={"source": "quantum_physics.pdf", "page": 1, "file_type": "pdf", "chunk_id": "qp_c1"},
        ),
        Document(
            page_content="Photosynthesis is the chemical process by which green plants convert light energy, carbon dioxide, and water into glucose and oxygen.",
            metadata={"source": "botany_textbook.docx", "page": 14, "file_type": "docx", "chunk_id": "bot_c1"},
        ),
        Document(
            page_content="Streamlit provides a pythonic way to build reactive data apps with session state and custom components without writing frontend code.",
            metadata={"source": "web_frameworks.txt", "page": 1, "file_type": "txt", "chunk_id": "web_c1"},
        ),
    ]

    print("\n[1/3] Ingesting 3 diverse topic documents...")
    add_documents_to_store(sample_docs, vector_store=store)
    print("      Ingestion complete.")

    # Step 2: Test known domain queries
    test_queries = [
        ("How do plants produce glucose and oxygen?", "botany_textbook.docx"),
        ("What computational principles use superposition?", "quantum_physics.pdf"),
        ("How do I build reactive Python web applications?", "web_frameworks.txt"),
    ]

    print("\n[2/3] Testing semantic retrieval on known queries...")
    for query, expected_source in test_queries:
        chunks = retrieve_relevant_chunks(query, vector_store=store, k=2)
        assert len(chunks) > 0, f"No chunks retrieved for query: {query}"
        top_match = chunks[0]
        actual_source = top_match.metadata.get("source")
        score = top_match.metadata.get("relevance_score")
        print(f"      Q: '{query}'")
        print(f"         -> Top Source: {actual_source} (score/distance: {score:.4f})")
        assert actual_source == expected_source, f"Expected {expected_source}, got {actual_source}"

    # Step 3: Inspect context formatting and source citations
    print("\n[3/3] Testing context formatting and source extraction...")
    results = retrieve_relevant_chunks("quantum superposition", vector_store=store, k=2)
    formatted = format_retrieved_context(results)
    sources = extract_sources(results)
    print("      Formatted Context snippet:")
    print("      " + formatted.replace("\n", "\n      "))
    print(f"      Extracted sources: {sources}")
    assert len(sources) >= 1

    # Cleanup
    clear_vector_store(store)
    print("\n[PASS] Semantic retrieval, scoring, and context formatting verified!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
