"""Test doubles shared by the search tests. No model download needed."""
from collections.abc import Sequence
from zlib import crc32

import numpy as np

from app.domain.models import Post

DIM = 64


class FakeEncoder:
    """Deterministic bag-of-words encoder: shared words -> similar vectors."""

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        rows = np.zeros((len(texts), DIM), dtype=np.float32)
        for row, text in zip(rows, texts):
            for word in text.lower().split():
                row[crc32(word.encode()) % DIM] += 1.0
            norm = np.linalg.norm(row)
            if norm > 0:
                row /= norm
        return rows


class FakePosts:
    def __init__(self, posts: list[Post]) -> None:
        self._posts = posts

    def list_posts(self) -> list[Post]:
        return list(self._posts)


def make_posts() -> list[Post]:
    return [
        Post(id=1, user_id=1, content="cheap dinner near the station"),
        Post(id=2, user_id=2, content="jazz playlist for studying"),
        Post(id=3, user_id=1, content="cheap dinner near the station"),  # same text as id 1 -> tie
        Post(id=4, user_id=3, content="python type hints explained"),
    ]