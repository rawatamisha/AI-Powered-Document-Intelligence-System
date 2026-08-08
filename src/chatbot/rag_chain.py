"""
Retrieval-augmented question answering for the document intelligence MVP.

The chatbot answers questions using retrieved chunks from ChromaDB and returns
citation metadata derived from retrieval results.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from dotenv import load_dotenv
from sarvamai import SarvamAI

from config import RETRIEVAL_TOP_K, SARVAM_API_TIMEOUT_SECONDS, SARVAM_CHAT_MODEL
from src.retrieval.vector_store import DocumentVectorStore, RetrievedChunk
from src.utils.logger import get_logger

load_dotenv()

_API_KEY = os.getenv("SARVAM_API_KEY")
_DEFAULT_CLIENT = SarvamAI(api_subscription_key=_API_KEY) if _API_KEY else None

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
    """Lightweight answer generator that turns retrieved chunks into concise, evidence-based answers."""

    def _summarize_chunks(self, question: str, chunks: list[RetrievedChunk]) -> str:
        relevant_texts = []
        for chunk in chunks[:3]:
            text = " ".join(chunk.text.split())
            if len(text) > 500:
                text = text[:497].rstrip() + "..."
            relevant_texts.append(text)

        if not relevant_texts:
            return "I could not find relevant information in the indexed documents."

        combined = " \n\n".join(relevant_texts)
        if len(combined) > 700:
            combined = combined[:697].rstrip() + "..."

        question_text = question.strip()
        if not question_text or len(question_text.split()) <= 2:
            return (
                "I can help answer questions about the indexed documents. "
                "Ask me about a topic, policy, notice, bill, or document section."
            )

        return (
            "The documents indicate: "
            f"{combined}"
        )

    def generate_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        mode: str,
    ) -> ChatResponse:
        if not chunks:
            return ChatResponse(
                answer_text=(
                    "I could not find relevant information in the indexed documents. "
                    "Ask me about a specific topic, policy, notice, bill, or document section."
                ),
                citations=[],
                mode=mode,
            )

        answer_text = self._summarize_chunks(question, chunks)
        citations = [
            {
                "source_file": chunk.source_file,
                "page_number": chunk.page_number,
                "snippet": chunk.text[:220].strip() + ("..." if len(chunk.text) > 220 else ""),
            }
            for chunk in chunks
        ]
        return ChatResponse(answer_text=answer_text, citations=citations, mode=mode)


class SarvamAnswerProvider:
    """Uses the Sarvam chat model to turn retrieved chunks into a more natural answer."""

    def __init__(self, client: Any | None = None, model: str | None = None) -> None:
        self.client = client or _DEFAULT_CLIENT
        self.model = model or SARVAM_CHAT_MODEL

    def _response_to_text(self, response: Any) -> str:
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            if "choices" in response:
                choice = response["choices"][0]
                if isinstance(choice, dict):
                    message = choice.get("message", {})
                    if isinstance(message, dict):
                        return str(message.get("content", ""))
            if "content" in response:
                return str(response["content"])
        choices = getattr(response, "choices", None)
        if choices:
            first_choice = choices[0]
            message = getattr(first_choice, "message", None)
            if message is not None and hasattr(message, "content"):
                return str(message.content)
            if hasattr(first_choice, "text"):
                return str(first_choice.text)
        if hasattr(response, "content"):
            return str(response.content)
        raise ValueError("Unsupported Sarvam response type")

    def _build_messages(self, question: str, chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
        context_parts = []
        for index, chunk in enumerate(chunks, start=1):
            context_parts.append(
                f"[{index}] Source: {chunk.source_file} | Page: {chunk.page_number}\n{chunk.text.strip()}"
            )
        context_text = "\n\n".join(context_parts)
        return [
            {
                "role": "system",
                "content": (
                    "You answer questions strictly from the provided retrieved passages. "
                    "Keep the answer concise, factual, and grounded in the source text. "
                    "Do not invent facts or add outside knowledge. "
                    "If the question is vague or greeting-like, respond with a short helpful prompt "
                    "that asks the user to ask about a specific document topic."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\nRetrieved passages:\n{context_text}"
                ),
            },
        ]

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

        if self.client is None:
            logger.warning("Sarvam API client is not configured; falling back to local answer generation")
            return LocalAnswerProvider().generate_answer(question, chunks, mode)

        try:
            response = self.client.chat.completions(
                messages=self._build_messages(question, chunks),
                model=self.model,
                temperature=0.2,
                max_tokens=600,
                request_options={"timeout_in_seconds": SARVAM_API_TIMEOUT_SECONDS},
            )
            answer_text = self._response_to_text(response).strip()
        except Exception as exc:
            logger.warning("Sarvam answer generation failed: %s; falling back to local answer generation", exc)
            return LocalAnswerProvider().generate_answer(question, chunks, mode)

        citations = [
            {
                "source_file": chunk.source_file,
                "page_number": chunk.page_number,
                "snippet": chunk.text[:220].strip() + ("..." if len(chunk.text) > 220 else ""),
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
        self.answer_provider = answer_provider or SarvamAnswerProvider()
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
