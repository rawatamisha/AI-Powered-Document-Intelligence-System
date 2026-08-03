"""
Section-aware chunking for processed OCR markdown.

The OCR layer already inserts page markers, so this chunker keeps those page
boundaries and creates retrieval-sized chunks while preserving page metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from config import CHUNK_OVERLAP_WORDS, CHUNK_SIZE_WORDS
from src.utils.logger import get_logger

logger = get_logger(__name__)

PAGE_MARKER_RE = re.compile(r"^<!-- page: (\d+) -->\s*$")


@dataclass(slots=True)
class ChunkRecord:
    """One retrieval chunk derived from processed OCR output."""

    chunk_id: str
    text: str
    source_file: str
    page_number: int
    section_heading: str | None
    language: str


@dataclass(slots=True)
class _ChunkState:
    page_number: int | None = None
    section_heading: str | None = None
    parts: list[str] = None  # type: ignore[assignment]
    words: int = 0
    chunk_start_page: int | None = None

    def __post_init__(self) -> None:
        if self.parts is None:
            self.parts = []


def _word_count(text: str) -> int:
    return len(text.split())


def _tail_words(text: str, word_limit: int) -> str:
    words = text.split()
    if word_limit <= 0 or len(words) <= word_limit:
        return text.strip()
    return " ".join(words[-word_limit:]).strip()


def _looks_like_heading(block: str) -> str | None:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    if not lines:
        return None

    first_line = lines[0]
    if first_line.startswith("#"):
        return first_line.lstrip("#").strip() or None

    if re.match(r"^Section\s+\d+[:.]?\s+.+", first_line, flags=re.IGNORECASE):
        return re.sub(r"^Section\s+\d+[:.]?\s+", "", first_line, flags=re.IGNORECASE).strip() or first_line

    if len(lines) == 1:
        short_line = len(first_line.split()) <= 12 and len(first_line) <= 90
        no_terminal_punctuation = not first_line.endswith((".", ":", ";"))
        starts_with_capital = bool(re.match(r"^[A-Z0-9]", first_line))
        mostly_alpha = sum(ch.isalpha() for ch in first_line) >= max(8, len(first_line) // 2)

        if short_line and no_terminal_punctuation and starts_with_capital and mostly_alpha:
            return first_line

    return None


def _iter_page_blocks(text: str) -> Iterable[tuple[int, str]]:
    current_page = 1
    current_lines: list[str] = []

    for line in text.splitlines():
        marker = PAGE_MARKER_RE.match(line.strip())
        if marker:
            if current_lines:
                block = "\n".join(current_lines).strip()
                if block:
                    yield current_page, block
                current_lines = []
            current_page = int(marker.group(1))
            continue

        current_lines.append(line)

    if current_lines:
        block = "\n".join(current_lines).strip()
        if block:
            yield current_page, block


def chunk_document(
    text: str,
    source_file: str | Path,
    language: str,
    chunk_size_words: int = CHUNK_SIZE_WORDS,
    chunk_overlap_words: int = CHUNK_OVERLAP_WORDS,
) -> list[ChunkRecord]:
    """
    Splits processed OCR text into retrieval-sized chunks.

    Args:
        text: OCR markdown with page markers.
        source_file: original PDF filename.
        language: detected primary language of the document.
        chunk_size_words: target max chunk size.
        chunk_overlap_words: trailing overlap carried into the next chunk.
    """
    source_name = Path(source_file).name
    chunks: list[ChunkRecord] = []
    state = _ChunkState()
    chunk_index = 1
    last_heading: str | None = None

    def flush_state() -> None:
        nonlocal chunk_index, state
        if not state.parts or state.chunk_start_page is None:
            return

        chunk_text = "\n\n".join(part.strip() for part in state.parts if part.strip()).strip()
        if not chunk_text:
            state = _ChunkState()
            return

        chunks.append(
            ChunkRecord(
                chunk_id=f"{Path(source_name).stem}__p{state.chunk_start_page}__c{chunk_index}",
                text=chunk_text,
                source_file=source_name,
                page_number=state.chunk_start_page,
                section_heading=state.section_heading,
                language=language,
            )
        )
        chunk_index += 1

        overlap_text = _tail_words(chunk_text, chunk_overlap_words)
        state = _ChunkState(
            page_number=None,
            section_heading=state.section_heading,
            parts=[overlap_text] if overlap_text else [],
            words=_word_count(overlap_text),
            chunk_start_page=None,
        )

    for page_number, block in _iter_page_blocks(text):
        block = block.strip()
        if not block:
            continue

        heading = _looks_like_heading(block)
        if heading:
            last_heading = heading

        block_words = _word_count(block)
        projected_words = state.words + block_words
        if state.parts and projected_words > chunk_size_words:
            flush_state()

        if state.chunk_start_page is None:
            state.chunk_start_page = page_number
        if state.section_heading is None:
            state.section_heading = last_heading
        state.parts.append(block)
        state.words += block_words
        state.page_number = page_number

    flush_state()
    logger.info("Chunked %s into %d chunk(s)", source_name, len(chunks))
    return chunks


def chunk_processed_file(
    processed_path: Path,
    source_file: str | None = None,
    language: str = "other",
    chunk_size_words: int = CHUNK_SIZE_WORDS,
    chunk_overlap_words: int = CHUNK_OVERLAP_WORDS,
) -> list[ChunkRecord]:
    """Loads a processed OCR file and chunks it."""
    return chunk_document(
        text=processed_path.read_text(encoding="utf-8"),
        source_file=source_file or processed_path.stem + ".pdf",
        language=language,
        chunk_size_words=chunk_size_words,
        chunk_overlap_words=chunk_overlap_words,
    )
