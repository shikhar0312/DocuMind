"""End-to-End Application Verification Script.

Tests the complete DocuMind pipeline:
1. Ingests PDF, DOCX, TXT, and manual text into persistent ChromaDB.
2. Queries content across each document type with live Gemini generation.
3. Tests follow-up query and out-of-domain query (hallucination resistance).
4. Tests persistence across complete restart (re-loading Chroma from disk).
5. Tests clean collection reset.
"""

import io
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import docx
from reportlab.pdfgen import canvas
from src.document_loader import load_document, load_manual_text
from src.text_splitter import split_documents
from src.vector_store import (
    get_vector_store,
    add_documents_to_store,
    get_collection_stats,
    clear_vector_store,
)
from src.rag_chain import ask_rag


def create_sample_files(temp_dir: Path) -> dict[str, Path]:
    """Create sample PDF, DOCX, and TXT files for testing."""
    files = {}

    # 1. Create PDF with multiple pages
    pdf_path = temp_dir / "system_architecture.pdf"
    bio = io.BytesIO()
    c = canvas.Canvas(bio)
    # Page 1
    c.drawString(72, 750, "DocuMind Architecture Specification - Version 2.4")
    c.drawString(72, 720, "The DocuMind Neural Engine utilizes an asynchronous indexing buffer.")
    c.drawString(72, 700, "Maximum ingestion batch size is configured to 256 concurrent blocks.")
    c.showPage()
    # Page 2
    c.drawString(72, 750, "DocuMind Fault Recovery Protocol")
    c.drawString(72, 720, "In case of worker node failover, the system triggers the Phoenix recovery daemon.")
    c.drawString(72, 700, "Recovery completion SLA is strictly under 1.5 seconds.")
    c.showPage()
    c.save()
    bio.seek(0)
    pdf_path.write_bytes(bio.getvalue())
    files["pdf"] = pdf_path

    # 2. Create DOCX with table
    docx_path = temp_dir / "pricing_and_quotas.docx"
    doc = docx.Document()
    doc.add_heading("DocuMind Enterprise Quotas", level=1)
    doc.add_paragraph("This document outlines API limits and billing tiers for enterprise tenants.")
    table = doc.add_table(rows=3, cols=3)
    table_data = [
        ["Tier", "Requests Per Minute", "Dedicated GPU Memory"],
        ["Starter", "60 RPM", "8 GB"],
        ["Enterprise Platinum", "2400 RPM", "64 GB H100"],
    ]
    for r_idx, row in enumerate(table_data):
        for c_idx, cell in enumerate(row):
            table.cell(r_idx, c_idx).text = cell
    doc.save(str(docx_path))
    files["docx"] = docx_path

    # 3. Create TXT file
    txt_path = temp_dir / "security_policy.txt"
    txt_content = (
        "DocuMind Security and Encryption Standards:\n"
        "All data at rest is encrypted using AES-256-GCM with hardware security modules.\n"
        "Customer master keys are rotated automatically every 90 calendar days."
    )
    txt_path.write_text(txt_content, encoding="utf-8")
    files["txt"] = txt_path

    return files


def main() -> int:
    print("=" * 60)
    print("   DocuMind End-to-End Application Verification")
    print("=" * 60)

    # Clean existing storage
    store = get_vector_store()
    clear_vector_store(store)
    store = get_vector_store()

    temp_dir = Path("/tmp/documind_e2e")
    temp_dir.mkdir(parents=True, exist_ok=True)
    sample_files = create_sample_files(temp_dir)

    print("\n[Step 1/6] Ingesting all 4 supported document formats...")

    # Ingest PDF
    pdf_docs = load_document(sample_files["pdf"])
    pdf_chunks = split_documents(pdf_docs)
    add_documents_to_store(pdf_chunks, vector_store=store)
    print(f"  -> PDF ingested: {len(pdf_chunks)} chunks (2 pages)")

    # Ingest DOCX
    docx_docs = load_document(sample_files["docx"])
    docx_chunks = split_documents(docx_docs)
    add_documents_to_store(docx_chunks, vector_store=store)
    print(f"  -> DOCX ingested: {len(docx_chunks)} chunks")

    # Ingest TXT
    txt_docs = load_document(sample_files["txt"])
    txt_chunks = split_documents(txt_docs)
    add_documents_to_store(txt_chunks, vector_store=store)
    print(f"  -> TXT ingested: {len(txt_chunks)} chunks")

    # Ingest Manual Text
    manual_raw = (
        "Executive Strategy Meeting Notes:\n"
        "Projected release date for DocuMind v3.0 is November 18, 2026.\n"
        "Strategic focus for v3.0 is zero-latency on-device hybrid indexing."
    )
    manual_docs = load_manual_text(manual_raw, source_name="executive_meeting_notes")
    manual_chunks = split_documents(manual_docs)
    add_documents_to_store(manual_chunks, vector_store=store)
    print(f"  -> Manual text ingested: {len(manual_chunks)} chunks")

    # Verify collection counts
    stats = get_collection_stats(store)
    print(f"\n[Step 2/6] Verifying collection state: {stats}")
    assert stats["source_count"] == 4, f"Expected 4 sources, found {stats['source_count']}"
    assert stats["total_chunks"] >= 4

    print("\n[Step 3/6] Testing grounded Q&A across each format...")

    # Test PDF Query (Page 2)
    q_pdf = "What is the recovery protocol and SLA in case of a worker node failover?"
    print(f"  Q (PDF): {q_pdf}")
    r_pdf = ask_rag(q_pdf, vector_store=store)
    print(f"  A: {r_pdf.answer}")
    print(f"  Citations: {r_pdf.sources}\n")
    assert r_pdf.has_sufficient_context is True
    assert "Phoenix" in r_pdf.answer
    assert any(s["source"] == "system_architecture.pdf" for s in r_pdf.sources)
    assert any(s.get("page") == 2 for s in r_pdf.sources)

    # Test DOCX Query (Table extraction)
    q_docx = "What is the request limit and GPU memory for Enterprise Platinum tier?"
    print(f"  Q (DOCX): {q_docx}")
    r_docx = ask_rag(q_docx, vector_store=store)
    print(f"  A: {r_docx.answer}")
    print(f"  Citations: {r_docx.sources}\n")
    assert r_docx.has_sufficient_context is True
    assert "2400" in r_docx.answer or "H100" in r_docx.answer

    # Test TXT Query
    q_txt = "How often are master encryption keys rotated?"
    print(f"  Q (TXT): {q_txt}")
    r_txt = ask_rag(q_txt, vector_store=store)
    print(f"  A: {r_txt.answer}")
    print(f"  Citations: {r_txt.sources}\n")
    assert r_txt.has_sufficient_context is True
    assert "90" in r_txt.answer

    # Test Manual Text Query
    q_manual = "When is DocuMind v3.0 scheduled for release?"
    print(f"  Q (Manual Text): {q_manual}")
    r_manual = ask_rag(q_manual, vector_store=store)
    print(f"  A: {r_manual.answer}")
    print(f"  Citations: {r_manual.sources}\n")
    assert r_manual.has_sufficient_context is True
    assert "November 18" in r_manual.answer or "2026" in r_manual.answer

    # Step 4: Test out-of-domain unanswerable question
    print("[Step 4/6] Testing hallucination defense on out-of-domain query...")
    q_hallucination = "What is the exact atomic weight and boiling point of Tungsten?"
    print(f"  Q: {q_hallucination}")
    r_hallucination = ask_rag(q_hallucination, vector_store=store)
    print(f"  A: {r_hallucination.answer}")
    print(f"  Has sufficient context: {r_hallucination.has_sufficient_context}\n")
    assert r_hallucination.has_sufficient_context is False

    # Step 5: Test persistence across client reload
    print("[Step 5/6] Verifying vector database persistence across reload...")
    del store
    reloaded_store = get_vector_store()
    reloaded_stats = get_collection_stats(reloaded_store)
    assert reloaded_stats["total_chunks"] == stats["total_chunks"]
    print(f"  Reloaded chunk count matches: {reloaded_stats['total_chunks']}")

    # Re-run query on reloaded store
    r_persisted = ask_rag("What is the SLA for failover?", vector_store=reloaded_store)
    assert "1.5" in r_persisted.answer
    print("  Query on reloaded store answered successfully!")

    # Step 6: Test clean wipe
    print("\n[Step 6/6] Testing safe collection reset...")
    clear_vector_store(reloaded_store)
    cleared_stats = get_collection_stats(get_vector_store())
    assert cleared_stats["total_chunks"] == 0
    print(f"  Collection safely reset (chunks: {cleared_stats['total_chunks']})")

    print("\n" + "=" * 60)
    print("   [PASS] ALL END-TO-END VERIFICATION CHECKS SUCCEEDED!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
