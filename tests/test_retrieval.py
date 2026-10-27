import numpy as np

from app.retrieval.similarity import cosine_similarity, stable_top_k, top_results


def test_cosine_similarity_matches_hand_computed_values():
    corpus = np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.0], [0.0, 0.0]])
    scores = cosine_similarity(np.array([1.0, 0.0]), corpus)
    assert np.allclose(scores, [1.0, 0.0, 1.0, 0.0])


def test_zero_query_vector_gives_finite_scores():
    corpus = np.array([[1.0, 0.0], [0.0, 1.0]])
    scores = cosine_similarity(np.array([0.0, 0.0]), corpus)
    assert np.isfinite(scores).all()
    assert list(scores) == [0.0, 0.0]


def test_empty_corpus_gives_no_scores():
    assert cosine_similarity(np.array([1.0, 0.0]), np.zeros((0, 2))).size == 0


def test_ties_use_ascending_post_id():
    indices = stable_top_k(np.array([0.7, 0.9, 0.9]), np.array([7, 5, 2]), k=2)
    assert list(indices) == [2, 1]


def test_k_larger_than_corpus_returns_everything():
    assert len(stable_top_k(np.array([0.1, 0.2]), np.array([1, 2]), k=50)) == 2


def test_non_positive_k_returns_nothing():
    assert len(stable_top_k(np.array([0.1, 0.2]), np.array([1, 2]), k=0)) == 0


def test_top_results_returns_post_ids_and_python_floats():
    corpus = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    results = top_results(np.array([1.0, 0.0]), corpus, np.array([10, 20, 30]), k=2)
    assert [post_id for post_id, _ in results] == [10, 30]
    assert all(type(score) is float for _, score in results)
    assert results[0][1] >= results[1][1]


def test_equal_scores_ordered_by_post_id_regardless_of_row_order():
    corpus = np.array([[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]])
    results = top_results(np.array([1.0, 0.0]), corpus, np.array([9, 3, 5]), k=3)
    assert [post_id for post_id, _ in results] == [3, 5, 9]