from src.ingestion.language_detect import detect_language


def test_detect_language_returns_english_for_english_text():
    assert detect_language("This document contains an English sentence.") == "en"


def test_detect_language_returns_hindi_for_devanagari_text():
    assert detect_language("यह एक हिंदी वाक्य है।") == "hi"


def test_detect_language_returns_other_for_blank_text():
    assert detect_language("   ") == "other"
