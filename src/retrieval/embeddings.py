"""
Local embedding wrapper around BAAI/bge-m3.

This module keeps model loading lazy so tests can monkeypatch the model easily
and the CLI only pays the load cost when Phase 2 indexing actually runs.
"""

from __future__ import annotations

from typing import Sequence

import torch
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL_NAME
from src.utils.logger import get_logger

logger = get_logger(__name__)

_EMBEDDING_MODEL: SentenceTransformer | None = None


class EmbeddingModel:
    """Thin wrapper around SentenceTransformer for batched text encoding."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME, device: str | None = None):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Loading embedding model %s on %s", self.model_name, self.device)
        self.model = SentenceTransformer(self.model_name, device=self.device)

    def encode_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Encodes texts into normalized embedding vectors."""
        if not texts:
            return []

        vectors = self.model.encode(
            list(texts),
            batch_size=16,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()


def get_embedding_model() -> EmbeddingModel:
    """Returns a singleton embedding model instance."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        _EMBEDDING_MODEL = EmbeddingModel()
    return _EMBEDDING_MODEL


def encode_texts(texts: Sequence[str]) -> list[list[float]]:
    """Convenience helper for directly encoding text with the shared model."""
    return get_embedding_model().encode_texts(texts)
