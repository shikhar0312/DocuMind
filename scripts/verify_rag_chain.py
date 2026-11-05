"""Verification script for RAG chain with live Gemini Chat and Embeddings."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.documents import Document
from src.vector_store import get_vector_store, add_documents_to_store, clear_vector_store
from src.rag_chain import ask_rag


def main() -> int:
    print("=== RAG Chain Live Verification with Gemini ===")

    store = get_vector_store()
    clear_vector_store(store)
    store = get_vector_store()

    # Step 1: Ingest unique reference content
    print("\n[1/3] Ingesting reference document...")
    doc = Document(
        page_content=(
            "Project Europa-Horizon was initiated in 2038 to explore subterranean oceans on Europa. "
            "The mission Commander was Captain Maya Lin, and the Lead Astrobiologist was Dr. Aris Thorne. "
            "The primary propulsion system relied on an ion-drive powered by a modular thorium reactor."
        ),
        metadata={
            "source": "europa_horizon_mission_brief.pdf",
            "page": 7,
            "file_type": "pdf",
            "chunk_id": "eh_c1",
        },
    )
    add_documents_to_store([doc], vector_store=store)
    print("      Ingested document: europa_horizon_mission_brief.pdf (Page 7)")

    # Step 2: Test answerable question grounded in content
    print("\n[2/3] Asking question supported by the document...")
    q1 = "Who was the Lead Astrobiologist for Project Europa-Horizon, and what reactor was used?"
    print(f"      Question: {q1}")
    resp1 = ask_rag(q1, vector_store=store)
    print(f"      Answer:\n      {resp1.answer}")
    print(f"      Sources: {resp1.sources}")
    print(f"      Has sufficient context: {resp1.has_sufficient_context}")

    assert resp1.has_sufficient_context is True
    assert "Aris Thorne" in resp1.answer
    assert "thorium" in resp1.answer.lower()
    assert len(resp1.sources) > 0
    assert resp1.sources[0]["source"] == "europa_horizon_mission_brief.pdf"
    assert resp1.sources[0]["page"] == 7

    # Step 3: Test question unsupported by the document (hallucination defense)
    print("\n[3/3] Asking question NOT supported by the document...")
    q2 = "What is the capital of Australia and what was its population in 1900?"
    print(f"      Question: {q2}")
    resp2 = ask_rag(q2, vector_store=store)
    print(f"      Answer:\n      {resp2.answer}")
    print(f"      Has sufficient context: {resp2.has_sufficient_context}")

    assert resp2.has_sufficient_context is False
    assert (
        "not have enough information" in resp2.answer.lower()
        or "does not contain" in resp2.answer.lower()
        or "not mentioned" in resp2.answer.lower()
    )

    # Cleanup
    clear_vector_store(store)
    print("\n[PASS] RAG chain grounding, citation packaging, and hallucination defense verified!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
