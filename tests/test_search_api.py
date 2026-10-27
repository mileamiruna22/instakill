import pytest
from fastapi.testclient import TestClient

from app.api.search import get_search_service
from app.main import app
from app.services.search_service import SearchService
from tests.fakes import FakeEncoder, FakePosts, make_posts


@pytest.fixture
def client():
    service = SearchService(FakePosts(make_posts()), FakeEncoder())
    service.build_index()
    app.dependency_overrides[get_search_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_search_success_shape(client):
    response = client.get("/search", params={"q": "cheap dinner", "limit": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "cheap dinner"
    assert 1 <= len(body["results"]) <= 3
    for result in body["results"]:
        assert {"post_id", "user_id", "content", "score"} <= set(result)
        assert isinstance(result["score"], float)


def test_results_are_ordered_by_score_then_post_id(client):
    results = client.get("/search", params={"q": "cheap dinner near the station"}).json()["results"]
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    assert [r["post_id"] for r in results[:2]] == [1, 3]


def test_default_limit_is_applied(client):
    assert client.get("/search", params={"q": "cheap"}).status_code == 200


def test_original_query_is_echoed_unchanged(client):
    assert client.get("/search", params={"q": "  Cheap Dinner "}).json()["query"] == "  Cheap Dinner "


@pytest.mark.parametrize("params", [{}, {"q": ""}, {"q": "   "}])
def test_missing_or_empty_q_is_a_client_error(client, params):
    response = client.get("/search", params=params)
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "query_empty", "message": "q must not be empty", "field": "q"}
    }


@pytest.mark.parametrize("limit", [0, 21, -5])
def test_out_of_range_limit_is_a_client_error(client, limit):
    response = client.get("/search", params={"q": "cheap", "limit": limit})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "limit_out_of_range"
    assert response.json()["error"]["field"] == "limit"


def test_non_numeric_limit_is_a_client_error(client):
    response = client.get("/search", params={"q": "cheap", "limit": "abc"})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request"
    assert error["field"] == "limit"


def test_index_not_ready_returns_503():
    service = SearchService(FakePosts(make_posts()), FakeEncoder())  # build_index() never called
    app.dependency_overrides[get_search_service] = lambda: service
    try:
        response = TestClient(app).get("/search", params={"q": "cheap"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "index_not_ready"


def test_health_still_works():
    assert TestClient(app).get("/health").json() == {"status": "ok"}