from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_pipeline import should_run_summary


def test_should_run_summary_when_forced(tmp_path: Path) -> None:
    summary_path = tmp_path / "doc_summary.md"
    assert should_run_summary(force=True, summary_path=summary_path) is True


def test_should_run_summary_when_missing(tmp_path: Path) -> None:
    summary_path = tmp_path / "doc_summary.md"
    assert should_run_summary(force=False, summary_path=summary_path) is True


def test_should_skip_summary_when_existing_and_not_forced(tmp_path: Path) -> None:
    summary_path = tmp_path / "doc_summary.md"
    summary_path.write_text("existing summary", encoding="utf-8")
    assert should_run_summary(force=False, summary_path=summary_path) is False
