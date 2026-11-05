"""Text splitter module for RAG Document Assistant.

Splits normalized documents into overlapping chunks using RecursiveCharacterTextSplitter,
retaining parent metadata and assigning unique chunk identifiers.
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings
from src.utils import generate_document_id


def get_text_splitter(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> RecursiveCharacterTextSplitter:
    """Create and return a configured RecursiveCharacterTextSplitter instance.

    Args:
        chunk_size: Optional override for character count per chunk.
        chunk_overlap: Optional override for overlap character count.
    """
    size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
    overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

    if overlap >= size:
        raise ValueError(
            f"chunk_overlap ({overlap}) must be strictly less than chunk_size ({size})."
        )

    return RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )


def split_documents(
    documents: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """Split a list of documents into chunks while preserving and enriching metadata.

    Args:
        documents: List of input Document objects.
        chunk_size: Optional character chunk size override.
        chunk_overlap: Optional character chunk overlap override.

    Returns:
        List of chunked Document objects with unique chunk_id and chunk_index metadata.
    """
    if not documents:
        return []

    splitter = get_text_splitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    chunked_documents: list[Document] = []

    # Process documents individually to assign per-document chunk indexing
    for doc in documents:
        raw_chunks = splitter.split_documents([doc])
        total_chunks = len(raw_chunks)
        parent_doc_id = doc.metadata.get(
            "document_id",
            generate_document_id(doc.page_content, doc.metadata.get("source", "doc")),
        )

        for idx, chunk in enumerate(raw_chunks, start=1):
            chunk_content = chunk.page_content.strip()
            if not chunk_content:
                continue

            # Copy parent metadata and add chunk-specific attributes
            metadata = dict(chunk.metadata)
            metadata["chunk_index"] = idx
            metadata["total_chunks"] = total_chunks
            metadata["chunk_id"] = f"{parent_doc_id}_c{idx}"

            chunked_documents.append(
                Document(page_content=chunk_content, metadata=metadata)
            )

    return chunked_documents


def split_text(
    text: str,
    metadata: dict | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """Convenience helper to split raw text directly into chunk Document objects.

    Args:
        text: Input string.
        metadata: Optional base metadata dictionary for the chunks.
        chunk_size: Optional chunk size override.
        chunk_overlap: Optional chunk overlap override.

    Returns:
        List of chunked Document objects.
    """
    if not text or not text.strip():
        return []

    base_metadata = dict(metadata or {})
    if "source" not in base_metadata:
        base_metadata["source"] = "raw_text"

    doc = Document(page_content=text.strip(), metadata=base_metadata)
    return split_documents(
        [doc], chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
