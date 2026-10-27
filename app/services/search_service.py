"""Application service for semantic search over posts.

Coordinates three collaborators without doing their jobs itself:

* ``PostSource``  - where posts come from (SQLite repository in production),
* ``TextEncoder`` - how text becomes vectors (pretrained model adapter),
* ``app.retrieval.similarity`` - pure cosine similarity and top-k ranking.

It knows nothing about HTTP and makes no database or model-library calls.

The in-memory index is built once by ``build_index()`` (called when the
application starts). To pick up new posts later, call ``build_index()`` again:
the new index is swapped in with a single assignment, so searches never see a
half-built index.
"""
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from app.adapters.encoder import TextEncoder
from app.domain.models import Post
from app.retrieval.similarity import top_results

MIN_LIMIT = 1
MAX_LIMIT = 20


class SearchError(Exception):
    """Expected, caller-facing search errors. ``code`` is stable and documented."""

    code: str = "search_error"

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


class QueryEmptyError(SearchError):
    code = "query_empty"


class LimitOutOfRangeError(SearchError):
    code = "limit_out_of_range"


class IndexNotReadyError(SearchError):
    code = "index_not_ready"


class PostSource(Protocol):
    def list_posts(self) -> list[Post]: ...


@dataclass(frozen=True)
class SearchHit:
    post_id: int
    user_id: int
    content: str
    score: float


@dataclass(frozen=True)
class _Index:
    posts_by_id: dict[int, Post]
    post_ids: NDArray[np.int64]
    vectors: NDArray[np.float32]


class SearchService:
    def __init__(self, posts: PostSource, encoder: TextEncoder) -> None:
        self._posts = posts
        self._encoder = encoder
        self._index: _Index | None = None

    def build_index(self) -> int:
        """(Re)build the in-memory index from the current posts. Returns the post count."""
        posts = self._posts.list_posts()
        ids = [post.id for post in posts]
        if any(post_id is None for post_id in ids):
            raise ValueError("indexed posts must have ids")

        if posts:
            vectors = self._encoder.encode([post.content for post in posts])
        else:
            vectors = np.zeros((0, 0), dtype=np.float32)

        self._index = _Index(
            posts_by_id={post.id: post for post in posts},
            post_ids=np.asarray(ids, dtype=np.int64),
            vectors=vectors,
        )
        return len(posts)

    def search(self, query: str, limit: int) -> list[SearchHit]:
        """Return up to ``limit`` posts ranked by similarity to ``query``.

        Raises:
            QueryEmptyError: ``query`` is empty or only whitespace.
            LimitOutOfRangeError: ``limit`` is outside 1..20.
            IndexNotReadyError: ``build_index()`` has not run yet.
        """
        cleaned = query.strip()
        if not cleaned:
            raise QueryEmptyError("q must not be empty", field="q")
        if not MIN_LIMIT <= limit <= MAX_LIMIT:
            raise LimitOutOfRangeError(
                f"limit must be between {MIN_LIMIT} and {MAX_LIMIT}", field="limit"
            )
        index = self._index
        if index is None:
            raise IndexNotReadyError("search index has not been built yet")
        if len(index.post_ids) == 0:
            return []

        query_vector = self._encoder.encode([cleaned])[0]
        ranked = top_results(query_vector, index.vectors, index.post_ids, limit)
        hits = []
        for post_id, score in ranked:
            post = index.posts_by_id[post_id]
            hits.append(SearchHit(post_id, post.user_id, post.content, score))
        return hits