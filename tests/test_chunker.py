from src.processing.chunker import chunk_document


def test_chunk_document_preserves_page_numbers_and_headings():
    text = """<!-- page: 1 -->
# Introduction

alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu

<!-- page: 2 -->
# Details

one two three four five six seven eight nine ten eleven twelve
"""

    chunks = chunk_document(
        text=text,
        source_file="sample.pdf",
        language="en",
        chunk_size_words=8,
        chunk_overlap_words=2,
    )

    assert len(chunks) >= 2
    assert chunks[0].source_file == "sample.pdf"
    assert chunks[0].page_number == 1
    assert chunks[0].section_heading == "Introduction"
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
