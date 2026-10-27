import sys
import types

import numpy as np

from app.adapters.encoder import SentenceTransformerEncoder


def test_encoder_loads_lazily_on_cpu_and_requests_normalized_vectors(monkeypatch):
    calls = {}

    class FakeModel:
        def __init__(self, name, device=None):
            calls["init"] = (name, device)

        def encode(self, texts, **kwargs):
            calls["encode"] = (texts, kwargs)
            return np.ones((len(texts), 3), dtype=np.float64)

    fake_module = types.SimpleNamespace(SentenceTransformer=FakeModel)
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)

    encoder = SentenceTransformerEncoder("some-model")
    assert "init" not in calls  # nothing loaded yet

    out = encoder.encode(["a", "b"])
    assert calls["init"] == ("some-model", "cpu")
    assert calls["encode"][1]["normalize_embeddings"] is True
    assert out.shape == (2, 3) and out.dtype == np.float32