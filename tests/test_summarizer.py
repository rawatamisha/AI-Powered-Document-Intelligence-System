from pathlib import Path
from types import SimpleNamespace

from src.processing import summarizer


class _FakeChatClient:
    def completions(self, **kwargs):
        payload = {
            "source_file": "sample.pdf",
            "language": "en",
            "purpose": "The document explains a budget approval.",
            "key_decisions": ["Budget approved"],
            "dates": ["2026"],
            "amounts": ["1000"],
            "responsible_departments": ["Finance"],
            "action_items": ["Issue the order"],
            "not_found_fields": [],
        }
        content = "```json\n" + __import__("json").dumps(payload) + "\n```"
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class _FakeClient:
    def __init__(self):
        self.chat = _FakeChatClient()


def test_summarize_document_writes_summary_file_and_flags_missing_fact(monkeypatch, tmp_path):
    monkeypatch.setattr(summarizer, "_client", _FakeClient())

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    summary = summarizer.summarize_document(
        source_pdf_path=pdf_path,
        processed_text="The budget was approved by Finance in 2026.",
        language="en",
    )

    summary_path = pdf_path.with_name("sample_summary.md")

    assert summary_path.exists()
    assert "amounts" in summary.not_found_fields
    assert summary.purpose == "not found in document"


def test_summarize_document_falls_back_when_sarvam_fails(monkeypatch, tmp_path):
    def _raise_summary_error(*args, **kwargs):
        raise summarizer.SummaryTransientError("temporary failure")

    monkeypatch.setattr(summarizer, "_run_summary_job", _raise_summary_error)

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    summary = summarizer.summarize_document(
        source_pdf_path=pdf_path,
        processed_text="The document contains no clearly extractable facts.",
        language="en",
    )

    summary_path = pdf_path.with_name("sample_summary.md")

    assert summary_path.exists()
    assert summary.purpose == "not found in document"
    assert set(summary.not_found_fields) == {
        "purpose",
        "key_decisions",
        "dates",
        "amounts",
        "responsible_departments",
        "action_items",
    }
