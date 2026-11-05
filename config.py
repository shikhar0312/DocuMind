"""Configuration module for RAG Document Assistant.

Centralizes all environment variables, model identifiers, persistence paths,
and RAG tuning parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Settings:
    """Application settings and defaults."""

    # API Keys
    GOOGLE_API_KEY: str = (
        os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    ).strip()

    # Gemini Models
    GEMINI_CHAT_MODEL: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv(
        "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"
    )
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))

    # Vector Database & Persistence
    CHROMA_PERSIST_DIR: Path = Path(
        os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma_db"))
    )
    CHROMA_COLLECTION_NAME: str = os.getenv(
        "CHROMA_COLLECTION_NAME", "rag_documents"
    )

    # Chunking Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))

    # Retrieval Configuration
    RETRIEVAL_K: int = int(os.getenv("RETRIEVAL_K", "4"))

    @classmethod
    def validate_api_key(cls) -> bool:
        """Return True if an API key is configured and non-empty."""
        return bool(cls.GOOGLE_API_KEY)


settings = Settings()


def get_chat_model(
    model_name: str | None = None,
    temperature: float | None = None,
) -> ChatGoogleGenerativeAI:
    """Initialize and return a ChatGoogleGenerativeAI instance.

    Args:
        model_name: Optional override for chat model identifier.
        temperature: Optional override for generation temperature.

    Raises:
        ValueError: If GOOGLE_API_KEY is not set.
    """
    if not settings.validate_api_key():
        raise ValueError(
            "Google Gemini API key not found. Please set GOOGLE_API_KEY in your .env file."
        )

    return ChatGoogleGenerativeAI(
        model=model_name or settings.GEMINI_CHAT_MODEL,
        temperature=temperature
        if temperature is not None
        else settings.GEMINI_TEMPERATURE,
        google_api_key=settings.GOOGLE_API_KEY,
    )


def get_embeddings_model(
    model_name: str | None = None,
) -> GoogleGenerativeAIEmbeddings:
    """Initialize and return a GoogleGenerativeAIEmbeddings instance.

    Args:
        model_name: Optional override for embedding model identifier.

    Raises:
        ValueError: If GOOGLE_API_KEY is not set.
    """
    if not settings.validate_api_key():
        raise ValueError(
            "Google Gemini API key not found. Please set GOOGLE_API_KEY in your .env file."
        )

    return GoogleGenerativeAIEmbeddings(
        model=model_name or settings.GEMINI_EMBEDDING_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
    )
