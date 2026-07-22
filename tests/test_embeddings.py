import numpy as np

from src.retrieval import embeddings


class _FakeSentenceTransformer:
    def __init__(self, model_name: str, device: str | None = None):
        self.model_name = model_name
        self.device = device

    def encode(
        self,
        texts,
        batch_size: int = 16,
        normalize_embeddings: bool = True,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
    ):
        return np.array([[float(len(text)), 1.0] for text in texts], dtype=float)


def test_embedding_model_encodes_texts(monkeypatch):
    monkeypatch.setattr(embeddings, "SentenceTransformer", _FakeSentenceTransformer)
    monkeypatch.setattr(embeddings, "_EMBEDDING_MODEL", None)

    model = embeddings.EmbeddingModel(model_name="fake-model", device="cpu")
    vectors = model.encode_texts(["hello", "world"])

    assert vectors == [[5.0, 1.0], [5.0, 1.0]]
