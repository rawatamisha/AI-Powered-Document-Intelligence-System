from dataclasses import dataclass

from src.chatbot.rag_chain import ChatResponse, LocalAnswerProvider, RAGChatbot, SarvamAnswerProvider


@dataclass
class _FakeChunk:
    chunk_id: str
    text: str
    source_file: str
    page_number: int
    section_heading: str | None
    distance: float | None = None


class _FakeVectorStore:
    def __init__(self, chunks):
        self.chunks = chunks

    def query(self, query_text, top_k, source_file=None):
        return self.chunks


class _FakeAnswerProvider:
    def generate_answer(self, question, chunks, mode):
        answer_text = f"Answered from {len(chunks)} chunk(s)."
        citations = [
            {"source_file": chunk.source_file, "page_number": chunk.page_number, "snippet": chunk.text}
            for chunk in chunks
        ]
        return ChatResponse(answer_text=answer_text, citations=citations, mode=mode)


def test_rag_chatbot_returns_cited_answer_from_retrieved_chunks():
    chunks = [
        _FakeChunk(
            chunk_id="doc__p1__c1",
            text="The budget was approved.",
            source_file="doc.pdf",
            page_number=1,
            section_heading="Finance",
        )
    ]
    chatbot = RAGChatbot(vector_store=_FakeVectorStore(chunks), answer_provider=_FakeAnswerProvider())

    response = chatbot.answer("What was approved?", source_file="doc.pdf")

    assert response.mode == "document_specific"
    assert response.answer_text == "Answered from 1 chunk(s)."
    assert response.citations[0]["source_file"] == "doc.pdf"
    assert response.citations[0]["page_number"] == 1


def test_local_answer_provider_returns_concise_evidence_based_answer():
    chunks = [
        _FakeChunk(
            chunk_id="doc__p1__c1",
            text="The document outlines the examination rules. It also lists the entry time and prohibited items.",
            source_file="doc.pdf",
            page_number=1,
            section_heading="Rules",
        )
    ]
    provider = LocalAnswerProvider()

    response = provider.generate_answer("What is this document about?", chunks, mode="document_specific")

    assert response.mode == "document_specific"
    assert response.answer_text.startswith("The documents indicate:")
    assert "examination rules" in response.answer_text.lower()
    assert response.citations[0]["source_file"] == "doc.pdf"


def test_local_answer_provider_gives_helpful_fallback_for_vague_questions():
    provider = LocalAnswerProvider()

    response = provider.generate_answer("Hello", [], mode="general")

    assert response.mode == "general"
    assert "Ask me about" in response.answer_text
    assert response.citations == []


def test_sarvam_answer_provider_uses_retrieved_context():
    chunks = [
        _FakeChunk(
            chunk_id="doc__p1__c1",
            text="The budget was approved.",
            source_file="doc.pdf",
            page_number=1,
            section_heading="Finance",
        )
    ]

    class _FakeClient:
        class _Chat:
            class _Completions:
                def __call__(self, messages, model, temperature, max_tokens, request_options):
                    assert model == "sarvam-105b"
                    assert "The budget was approved." in messages[1]["content"]
                    return {"choices": [{"message": {"content": "The budget was approved."}}]}

            completions = _Completions()

        chat = _Chat()

    provider = SarvamAnswerProvider(client=_FakeClient())
    response = provider.generate_answer("What was approved?", chunks, mode="document_specific")

    assert response.answer_text == "The budget was approved."
    assert response.citations[0]["source_file"] == "doc.pdf"
