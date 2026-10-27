"""Pure retrieval functions: vectors in, ordered ids and scores out.

Nothing here loads a model, reads a database, or touches HTTP. That keeps the
ranking rules (cosine similarity, deterministic top-k) easy to test with tiny
hand-made vectors.
"""
import numpy as np
from numpy.typing import ArrayLike, NDArray


def cosine_similarity(query_vector: ArrayLike, corpus_vectors: ArrayLike) -> NDArray[np.float64]:
    """Return one cosine score per row of ``corpus_vectors``.

    A zero-length query or corpus row has no direction, so its score is 0.0
    instead of NaN or infinity.
    """
    query = np.asarray(query_vector, dtype=np.float64)
    corpus = np.asarray(corpus_vectors, dtype=np.float64)
    if corpus.size == 0:
        return np.zeros(0, dtype=np.float64)

    dots = corpus @ query
    norms = np.linalg.norm(corpus, axis=1) * np.linalg.norm(query)
    scores = np.zeros_like(dots)
    np.divide(dots, norms, out=scores, where=norms > 0)
    return scores


def stable_top_k(scores: ArrayLike, post_ids: ArrayLike, k: int) -> NDArray[np.intp]:
    """Return the indices of the best ``k`` items.

    Order: score descending; equal scores are ordered by ascending post id.
    ``k`` larger than the number of items just returns all of them.
    """
    scores = np.asarray(scores, dtype=np.float64)
    post_ids = np.asarray(post_ids)
    if k <= 0 or scores.size == 0:
        return np.zeros(0, dtype=np.intp)
    # np.lexsort sorts by the LAST key first: -score ascending == score descending,
    # then post_id ascending for ties.
    order = np.lexsort((post_ids, -scores))
    return order[:k]


def top_results(
    query_vector: ArrayLike,
    corpus_vectors: ArrayLike,
    post_ids: ArrayLike,
    k: int,
) -> list[tuple[int, float]]:
    """Return up to ``k`` ``(post_id, score)`` pairs, best first."""
    post_ids = np.asarray(post_ids)
    scores = cosine_similarity(query_vector, corpus_vectors)
    indices = stable_top_k(scores, post_ids, k)
    return [(int(post_ids[i]), float(scores[i])) for i in indices]