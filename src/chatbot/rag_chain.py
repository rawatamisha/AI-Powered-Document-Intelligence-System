"""
Retrieval-augmented question answering for the document intelligence MVP.

The chatbot answers questions using retrieved chunks from ChromaDB and returns
citation metadata derived from retrieval results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from config import RETRIEVAL_TOP_K
from src.retrieval.vector_store import DocumentVectorStore, RetrievedChunk
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ChatResponse:
    """Structured response returned to the application layer."""

    answer_text: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "general"


class AnswerProvider(Protocol):
    """Small protocol for turning retrieved chunks into a chat answer."""

    def generate_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        mode: str,
    ) -> ChatResponse:
        ...


class LocalAnswerProvider:
    """Lightweight answer generator that uses the retrieved chunks directly."""

    def generate_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        mode: str,
    ) -> ChatResponse:
        if not chunks:
            return ChatResponse(
                answer_text="I could not find relevant information in the indexed documents.",
                citations=[],
                mode=mode,
            )

        top_chunk = chunks[0]
        answer_text = (
            f"Based on the retrieved passages, the most relevant content says: {top_chunk.text}"
        )
        citations = [
            {
                "source_file": chunk.source_file,
                "page_number": chunk.page_number,
                "snippet": chunk.text,
            }
            for chunk in chunks
        ]
        return ChatResponse(answer_text=answer_text, citations=citations, mode=mode)


class RAGChatbot:
    """Simple retrieval-based chatbot wrapper for document Q&A."""

    def __init__(
        self,
        vector_store: DocumentVectorStore | None = None,
        answer_provider: AnswerProvider | None = None,
        top_k: int = RETRIEVAL_TOP_K,
    ) -> None:
        self.vector_store = vector_store
        self.answer_provider = answer_provider or LocalAnswerProvider()
        self.top_k = top_k

    def answer(
        self,
        question: str,
        source_file: str | None = None,
        top_k: int | None = None,
    ) -> ChatResponse:
        """Answers a question using the local vector store and retrieved citations."""
        if self.vector_store is None:
            raise ValueError("A vector store is required to answer questions")

        mode = "document_specific" if source_file else "general"
        chunks = self.vector_store.query(
            query_text=question,
            top_k=top_k or self.top_k,
            source_file=source_file,
        )
        logger.info(
            "Answered question '%s' with %d chunk(s) in %s mode",
            question,
            len(chunks),
            mode,
        )
        return self.answer_provider.generate_answer(question, chunks, mode)
