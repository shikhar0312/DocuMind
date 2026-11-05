"""RAG Chain module for RAG Document Assistant.

Orchestrates retrieved context formatting, grounded prompt construction,
Gemini chat generation, and response citation packaging.
"""

from dataclasses import dataclass, field
from typing import Any
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from config import get_chat_model, settings
from src.retriever import (
    extract_sources,
    format_retrieved_context,
    retrieve_relevant_chunks,
)
from src.vector_store import get_vector_store

RAG_SYSTEM_PROMPT = """You are DocuMind, an accurate and helpful document assistant. Your task is to answer the user's question strictly using the provided context.

Rules:
1. Strict Grounding: Base your answer exclusively on the supplied Context below. Do not use outside assumptions or external knowledge.
2. Insufficient Information: If the provided context does not contain enough information to answer the question truthfully and completely, respond with:
"I do not have enough information in the provided documents to answer this question."
Do not speculate, assume, or invent facts.
3. Citations: When answering, cite the corresponding Source filename and Page number when available in the context headers.
4. Clarity: Provide clear, concise, well-structured, and factual answers.

Context:
{context}"""


def get_rag_prompt() -> ChatPromptTemplate:
    """Return the grounded ChatPromptTemplate for RAG generation."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", "{question}"),
        ]
    )


@dataclass
class RAGResponse:
    """Container for RAG generation output."""

    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    retrieved_documents: list[Document] = field(default_factory=list)
    has_sufficient_context: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary format."""
        return {
            "answer": self.answer,
            "sources": self.sources,
            "has_sufficient_context": self.has_sufficient_context,
            "total_chunks_retrieved": len(self.retrieved_documents),
        }


def build_rag_chain(
    llm: BaseChatModel | None = None,
) -> Runnable:
    """Build a Runnable LCEL chain for context-grounded Q&A.

    Args:
        llm: Chat model instance (defaults to configured Gemini chat model).
    """
    model = llm or get_chat_model()
    prompt = get_rag_prompt()
    return prompt | model | StrOutputParser()


def ask_rag(
    question: str,
    vector_store: Chroma | None = None,
    llm: BaseChatModel | None = None,
    k: int | None = None,
) -> RAGResponse:
    """Execute complete RAG flow: retrieval -> grounded prompt -> generation -> source packaging.

    Args:
        question: User query string.
        vector_store: Optional vector store instance.
        llm: Optional chat model instance.
        k: Optional top-k chunk count override.

    Returns:
        RAGResponse containing the generated answer, source citations, and retrieved chunks.
    """
    cleaned_question = (question or "").strip()
    if not cleaned_question:
        return RAGResponse(
            answer="Please enter a question.",
            sources=[],
            retrieved_documents=[],
            has_sufficient_context=False,
        )

    store = vector_store or get_vector_store()

    # Check if vector store is empty
    if store._collection.count() == 0:
        return RAGResponse(
            answer=(
                "No documents have been uploaded yet. "
                "Please upload a document or paste text before asking questions."
            ),
            sources=[],
            retrieved_documents=[],
            has_sufficient_context=False,
        )

    # Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(
        query=cleaned_question,
        vector_store=store,
        k=k or settings.RETRIEVAL_K,
    )

    if not chunks:
        return RAGResponse(
            answer="I do not have enough information in the provided documents to answer this question.",
            sources=[],
            retrieved_documents=[],
            has_sufficient_context=False,
        )

    # Format context and extract source references
    context_str = format_retrieved_context(chunks)
    sources = extract_sources(chunks)

    # Generate answer
    chain = build_rag_chain(llm=llm)
    answer = chain.invoke(
        {
            "context": context_str,
            "question": cleaned_question,
        }
    )

    # Check if model admitted insufficient information
    answer_stripped = answer.strip()
    is_insufficient = (
        "do not have enough information" in answer_stripped.lower()
        or "does not contain enough information" in answer_stripped.lower()
        or "not mentioned in the provided" in answer_stripped.lower()
    )

    return RAGResponse(
        answer=answer_stripped,
        sources=sources if not is_insufficient else [],
        retrieved_documents=chunks,
        has_sufficient_context=not is_insufficient,
    )
