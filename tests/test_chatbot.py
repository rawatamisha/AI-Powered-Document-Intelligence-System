from src.chatbot.rag_chain import SarvamAnswerProvider
from src.retrieval.vector_store import RetrievedChunk


class DummyClient:
    class chat:
        class completions:
            @staticmethod
            def __call__(*args, **kwargs):
                return {"choices": [{"message": {"content": "The decision was to approve the budget."}}]}


def test_sarvam_prompt_requires_english_answer():
    provider = SarvamAnswerProvider(client=DummyClient())
    chunks = [
        RetrievedChunk(
            chunk_id="doc__p1__c1",
            text="The Cabinet approved the annual budget allocation for 2026-27.",
            source_file="doc.pdf",
            page_number=1,
            section_heading="Budget",
        )
    ]

    messages = provider._build_messages("What decision was taken?", chunks)

    assert "English" in messages[0]["content"]
    assert "strictly from the provided retrieved passages" in messages[0]["content"].lower()
