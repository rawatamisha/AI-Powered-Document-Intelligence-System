from dataclasses import dataclass

from src.processing.chunker import ChunkRecord
from src.retrieval.vector_store import DocumentVectorStore


class _FakeEmbeddingModel:
    def encode_texts(self, texts):
        vectors = []
        for text in texts:
            vectors.append([1.0, 0.0] if "budget" in text.lower() else [0.0, 1.0])
        return vectors


def test_vector_store_add_and_query(tmp_path):
    store = DocumentVectorStore(db_dir=tmp_path / "chroma", embedding_model=_FakeEmbeddingModel())
    store.add_chunks(
        [
            ChunkRecord(
                chunk_id="doc__p1__c1",
                text="The budget was approved.",
                source_file="doc.pdf",
                page_number=1,
                section_heading="Finance",
                language="en",
            ),
            ChunkRecord(
                chunk_id="doc__p2__c2",
                text="This section discusses hiring.",
                source_file="doc.pdf",
                page_number=2,
                section_heading="HR",
                language="en",
            ),
        ]
    )

    results = store.query("budget", top_k=1)

    assert len(results) == 1
    assert "budget" in results[0].text.lower()
    assert results[0].page_number == 1
