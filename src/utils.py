"""Utility functions for RAG Document Assistant."""

import hashlib
import re
from pathlib import Path


def generate_document_id(content: str, source: str) -> str:
    """Generate a stable deterministic ID for a document based on its source and content."""
    hasher = hashlib.sha256()
    hasher.update(source.encode("utf-8", errors="replace"))
    hasher.update(content.encode("utf-8", errors="replace"))
    return hasher.hexdigest()[:16]


def clean_text(text: str) -> str:
    """Normalize whitespace and strip null/unsupported control characters."""
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Normalize multiple newlines and carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace sequences of 3+ newlines with 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
