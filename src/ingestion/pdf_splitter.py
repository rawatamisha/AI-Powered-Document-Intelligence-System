"""
Splits PDFs that exceed Sarvam's per-job page limit into smaller sub-PDFs,
while tracking each sub-PDF's original page numbers so citations stay accurate
after OCR output is reassembled. See ARCHITECTURE.md §2.1 and PHASES.md Phase 1.
"""

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from config import SARVAM_OCR_MAX_PAGES_PER_JOB
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PdfBatch:
    """A sub-PDF ready to send to the OCR API, with its original page range."""
    file_path: Path
    start_page: int  # 1-indexed, inclusive, refers to the ORIGINAL document
    end_page: int    # 1-indexed, inclusive


def split_pdf(source_path: Path, output_dir: Path) -> list[PdfBatch]:
    """
    Splits `source_path` into one or more sub-PDFs of at most
    SARVAM_OCR_MAX_PAGES_PER_JOB pages each, written into `output_dir`.

    If the source PDF already fits within the limit, returns a single batch
    pointing at a copy of the original (kept consistent with the multi-batch
    case so downstream code doesn't need two code paths).

    Args:
        source_path: path to the original PDF.
        output_dir: directory to write split sub-PDFs into (created if missing).

    Returns:
        List of PdfBatch, ordered by page range, covering the whole document.

    Raises:
        FileNotFoundError: if source_path does not exist.
        ValueError: if the PDF cannot be opened (corrupted/encrypted).
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source PDF not found: {source_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(source_path)
    except Exception as exc:
        raise ValueError(f"Could not open PDF {source_path.name}: {exc}") from exc

    total_pages = doc.page_count
    logger.info("Splitting %s (%d pages) into batches of %d",
                source_path.name, total_pages, SARVAM_OCR_MAX_PAGES_PER_JOB)

    batches: list[PdfBatch] = []
    batch_index = 0

    for start in range(0, total_pages, SARVAM_OCR_MAX_PAGES_PER_JOB):
        end = min(start + SARVAM_OCR_MAX_PAGES_PER_JOB, total_pages)  # exclusive
        batch_doc = fitz.open()
        batch_doc.insert_pdf(doc, from_page=start, to_page=end - 1)

        batch_path = output_dir / f"{source_path.stem}__batch{batch_index}.pdf"
        batch_doc.save(batch_path)
        batch_doc.close()

        batches.append(
            PdfBatch(file_path=batch_path, start_page=start + 1, end_page=end)
        )
        batch_index += 1

    doc.close()
    logger.info("Created %d batch(es) for %s", len(batches), source_path.name)
    return batches
