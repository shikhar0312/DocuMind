"""Document loader module for RAG Document Assistant.

Supports loading and normalizing PDF, DOCX, TXT files, and raw text
into standard LangChain Document objects with preserved metadata.
"""

import io
from pathlib import Path
from typing import BinaryIO, Union
import docx
import pypdf
from langchain_core.documents import Document

from src.utils import clean_text, generate_document_id

SourceType = Union[str, Path, BinaryIO, bytes]


def _to_bytes_io(source: SourceType) -> io.BytesIO:
    """Helper to convert various source types into a readable BytesIO stream."""
    if isinstance(source, bytes):
        return io.BytesIO(source)
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return io.BytesIO(path.read_bytes())
    if hasattr(source, "read"):
        content = source.read()
        if isinstance(content, str):
            content = content.encode("utf-8")
        return io.BytesIO(content)
    raise TypeError(f"Unsupported source type: {type(source)}")


def load_pdf(source: SourceType, filename: str = "document.pdf") -> list[Document]:
    """Extract text from each page of a PDF and return LangChain Documents.

    Args:
        source: File path, bytes, or file-like stream.
        filename: Original name of the file for metadata.

    Returns:
        List of Document objects, one per non-empty page.

    Raises:
        ValueError: If PDF has no extractable text.
    """
    stream = _to_bytes_io(source)
    try:
        reader = pypdf.PdfReader(stream)
    except Exception as e:
        raise ValueError(f"Failed to parse PDF '{filename}': {e}") from e

    documents: list[Document] = []
    total_pages = len(reader.pages)

    if total_pages == 0:
        raise ValueError(f"PDF file '{filename}' contains no pages.")

    for page_idx, page in enumerate(reader.pages, start=1):
        try:
            raw_text = page.extract_text() or ""
        except Exception:
            raw_text = ""
        text = clean_text(raw_text)
        if text:
            doc_id = generate_document_id(text, f"{filename}#p{page_idx}")
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": filename,
                        "page": page_idx,
                        "total_pages": total_pages,
                        "file_type": "pdf",
                        "document_id": doc_id,
                    },
                )
            )

    if not documents:
        raise ValueError(
            f"No extractable text found in '{filename}'. "
            "Scanned or image-only PDFs are not supported."
        )

    return documents


def load_docx(
    source: SourceType, filename: str = "document.docx"
) -> list[Document]:
    """Extract text from paragraphs and tables in a DOCX file.

    Args:
        source: File path, bytes, or file-like stream.
        filename: Original name of the file for metadata.

    Returns:
        List containing a single Document object with the combined text.

    Raises:
        ValueError: If document contains no readable text.
    """
    stream = _to_bytes_io(source)
    try:
        doc = docx.Document(stream)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX '{filename}': {e}") from e

    text_parts: list[str] = []

    # Extract paragraphs
    for para in doc.paragraphs:
        cleaned = clean_text(para.text)
        if cleaned:
            text_parts.append(cleaned)

    # Extract tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(
                clean_text(cell.text) for cell in row.cells if clean_text(cell.text)
            )
            if row_text:
                text_parts.append(row_text)

    combined_text = "\n\n".join(text_parts)
    if not combined_text:
        raise ValueError(f"No text content found in DOCX file '{filename}'.")

    doc_id = generate_document_id(combined_text, filename)
    return [
        Document(
            page_content=combined_text,
            metadata={
                "source": filename,
                "page": 1,
                "file_type": "docx",
                "document_id": doc_id,
            },
        )
    ]


def load_txt(source: SourceType, filename: str = "document.txt") -> list[Document]:
    """Load text from a plain TXT file.

    Args:
        source: File path, bytes, or file-like stream.
        filename: Original name of the file for metadata.

    Returns:
        List containing a single Document object with the file text.

    Raises:
        ValueError: If text file is empty.
    """
    stream = _to_bytes_io(source)
    raw_bytes = stream.getvalue()

    # Attempt UTF-8 first, fallback to latin-1
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = raw_bytes.decode("latin-1", errors="replace")

    cleaned = clean_text(content)
    if not cleaned:
        raise ValueError(f"TXT file '{filename}' is empty or contains only whitespace.")

    doc_id = generate_document_id(cleaned, filename)
    return [
        Document(
            page_content=cleaned,
            metadata={
                "source": filename,
                "page": 1,
                "file_type": "txt",
                "document_id": doc_id,
            },
        )
    ]


def load_manual_text(
    text: str, source_name: str = "manual_text"
) -> list[Document]:
    """Convert manually entered or pasted text into a LangChain Document.

    Args:
        text: Raw user-entered string.
        source_name: Name identifier for source metadata.

    Returns:
        List containing a single Document object.

    Raises:
        ValueError: If text is empty or only whitespace.
    """
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Manual text input is empty or contains only whitespace.")

    doc_id = generate_document_id(cleaned, source_name)
    return [
        Document(
            page_content=cleaned,
            metadata={
                "source": source_name,
                "page": 1,
                "file_type": "text",
                "document_id": doc_id,
            },
        )
    ]


def load_document(
    source: SourceType, filename: str | None = None
) -> list[Document]:
    """Inspect file format and dispatch to the appropriate document loader.

    Args:
        source: File path, bytes, or file-like stream.
        filename: Optional name of the file (inferred from path if not provided).

    Returns:
        List of LangChain Document objects with normalized metadata.

    Raises:
        ValueError: For unsupported file formats or empty content.
    """
    if filename is None:
        if isinstance(source, (str, Path)):
            filename = Path(source).name
        elif hasattr(source, "name") and isinstance(source.name, str):
            filename = source.name
        else:
            filename = "unknown_document"

    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return load_pdf(source, filename=filename)
    elif ext in (".docx", ".doc"):
        if ext == ".doc":
            raise ValueError(
                f"Legacy Word format '.doc' is not supported for '{filename}'. "
                "Please convert to '.docx'."
            )
        return load_docx(source, filename=filename)
    elif ext in (".txt", ".md", ".log"):
        return load_txt(source, filename=filename)
    else:
        raise ValueError(
            f"Unsupported file format '{ext}' for file '{filename}'. "
            "Supported formats are: .pdf, .docx, .txt"
        )
