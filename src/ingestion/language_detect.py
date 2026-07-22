"""
Lightweight language detection for processed OCR text.

Phase 2 uses this to route summary language and to keep metadata consistent
with the source document's primary language.
"""

from __future__ import annotations

import re

from langdetect import DetectorFactory, LangDetectException, detect

from src.utils.logger import get_logger

logger = get_logger(__name__)

DetectorFactory.seed = 0

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


def detect_language(text: str) -> str:
    """
    Detects the dominant language for a document.

    Returns:
        "hi" for Hindi, "en" for English, or "other" for everything else
        and for short/ambiguous text.
    """
    sample = text.strip()
    if not sample:
        return "other"

    devanagari_count = len(_DEVANAGARI_RE.findall(sample))
    if devanagari_count >= 1:
        return "hi"

    try:
        detected = detect(sample)
    except LangDetectException:
        logger.debug("Language detection failed for short or noisy text")
        return "other"

    if detected.startswith("hi"):
        return "hi"
    if detected.startswith("en"):
        return "en"
    return "other"
