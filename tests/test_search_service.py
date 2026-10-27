import pytest

from app.services.search_service import (
    IndexNotReadyError,
    LimitOutOfRangeError,
    QueryEmptyError,
    SearchService,
)
from tests.fakes import FakeEncoder, FakePosts, make_posts


@pytest.fixture
def service() -> SearchService:
    svc = SearchService(FakePosts(make_posts()), FakeEncoder())
    assert svc.build_index() == 4
    return svc


def test_relevant_posts_rank_first(service):
    hits = service.search("cheap dinner", limit=4)
    assert [h.post_id for h in hits[:2]] == [1, 3]
    assert hits[0].score > hits[-1].score


def test_equal_scores_break_ties_by_ascending_post_id(service):
    hits = service.search("cheap dinner near the station", limit=2)
    assert hits[0].score == hits[1].score
    assert [h.post_id for h in hits] == [1, 3]


def test_limit_caps_results(service):
    assert len(service.search("cheap dinner", limit=1)) == 1


def test_hit_carries_post_fields(service):
    hit = service.search("jazz", limit=1)[0]
    assert (hit.post_id, hit.user_id) == (2, 2)
    assert hit.content == "jazz playlist for studying"
    assert isinstance(hit.score, float)


@pytest.mark.parametrize("query", ["", "   ", "\n"])
def test_blank_query_is_rejected(service, query):
    with pytest.raises(QueryEmptyError) as exc:
        service.search(query, limit=5)
    assert (exc.value.code, exc.value.field) == ("query_empty", "q")


@pytest.mark.parametrize("limit", [0, -1, 21, 100])
def test_out_of_range_limit_is_rejected(service, limit):
    with pytest.raises(LimitOutOfRangeError) as exc:
        service.search("cheap", limit=limit)
    assert (exc.value.code, exc.value.field) == ("limit_out_of_range", "limit")


@pytest.mark.parametrize("limit", [1, 20])
def test_limit_bounds_are_inclusive(service, limit):
    service.search("cheap", limit=limit)


def test_search_before_index_is_built_fails_clearly():
    svc = SearchService(FakePosts(make_posts()), FakeEncoder())
    with pytest.raises(IndexNotReadyError):
        svc.search("cheap", limit=5)


def test_empty_database_gives_empty_results():
    svc = SearchService(FakePosts([]), FakeEncoder())
    assert svc.build_index() == 0
    assert svc.search("anything", limit=5) == []


def test_rebuilding_the_index_picks_up_new_posts():
    posts = make_posts()
    source = FakePosts(posts)
    svc = SearchService(source, FakeEncoder())
    svc.build_index()
    assert svc.search("gardening tips", limit=1)[0].post_id != 5

    from app.domain.models import Post

    posts.append(Post(id=5, user_id=1, content="gardening tips for spring"))
    svc.build_index()
    assert svc.search("gardening tips", limit=1)[0].post_id == 5