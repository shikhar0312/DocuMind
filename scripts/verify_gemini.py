"""Verification script for Gemini Chat and Embeddings configuration."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings, get_chat_model, get_embeddings_model
from src.embeddings import get_embeddings


def main() -> int:
    print("=== Gemini Configuration Verification ===")
    print(f"Chat Model: {settings.GEMINI_CHAT_MODEL}")
    print(f"Embedding Model: {settings.GEMINI_EMBEDDING_MODEL}")
    print(f"Chroma Persist Dir: {settings.CHROMA_PERSIST_DIR}")
    print(f"Chunk Size / Overlap: {settings.CHUNK_SIZE} / {settings.CHUNK_OVERLAP}")
    print(f"Retrieval Top-k: {settings.RETRIEVAL_K}")

    if not settings.validate_api_key():
        print("\n[!] No API key found in environment or .env file.")
        print("    Please create a .env file with:")
        print("    GOOGLE_API_KEY=your_actual_gemini_api_key")
        return 2

    print("\n[+] API Key detected. Testing Gemini Chat Model...")
    try:
        chat = get_chat_model()
        response = chat.invoke("Respond with exactly the single word: OK")
        print(f"    Chat response: {response.content.strip()}")
    except Exception as e:
        print(f"[X] Chat Model test failed: {e}")
        return 1

    print("\n[+] Testing Gemini Embeddings Model...")
    try:
        embeddings = get_embeddings()
        vector = embeddings.embed_query("DocuMind RAG test document query")
        print(f"    Successfully generated embedding vector of dimension {len(vector)}.")
    except Exception as e:
        print(f"[X] Embeddings test failed: {e}")
        return 1

    print("\n[PASS] All Gemini configuration and API tests passed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
