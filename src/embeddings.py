"""Embeddings module for RAG Document Assistant.

Provides an initialized Google Gemini embeddings model for vector operations.
"""

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import get_embeddings_model, settings


def get_embeddings(
    model_name: str | None = None,
) -> GoogleGenerativeAIEmbeddings:
    """Return the configured Gemini embedding model instance."""
    return get_embeddings_model(model_name=model_name)
