"""Model adapter: the only place that knows about the sentence-transformers library.

The rest of the application depends on the small ``TextEncoder`` protocol, so
tests can swap in a fake encoder and no model has to be downloaded to run them.
"""
from collections.abc import Sequence
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


class TextEncoder(Protocol):
    def encode(self, texts: Sequence[str]) -> NDArray[np.float32]:
        """Return one L2-normalized embedding row per text."""
        ...


class SentenceTransformerEncoder:
    """Pretrained encoder running on CPU. The model loads on first use."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            # Imported here so that importing the app (and running the tests)
            # does not require the heavy dependency.
            from sentence_transformers import SentenceTransformer 

            self._model = SentenceTransformer(self._model_name, device="cpu")
        return self._model

    def encode(self, texts: Sequence[str]) -> NDArray[np.float32]:
        embeddings = self._load().encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)