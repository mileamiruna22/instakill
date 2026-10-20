import pytest

from app.domain.models import Post
from app.services.post_service import (
    MAX_CONTENT_LENGTH,
    AuthorNotFoundError,
    ContentEmptyError,
    ContentTooLongError,
    PostService,
)


class FakeAuthors:
    def __init__(self, existing: set[int]) -> None:
        self._existing = existing

    def user_exists(self, user_id: int) -> bool:
        return user_id in self._existing


@pytest.fixture
def service() -> PostService:
    return PostService(FakeAuthors({1, 2}))


def test_valid_submission_returns_unsaved_post(service):
    post = service.prepare_post(user_id=1, content="hello world")
    assert isinstance(post, Post)
    assert post.user_id == 1
    assert post.content == "hello world"
    assert post.id is None
    assert post.created_at is None


def test_content_is_stripped(service):
    assert service.prepare_post(1, "  hi there \n").content == "hi there"


def test_content_at_limit_is_accepted(service):
    post = service.prepare_post(1, "a" * MAX_CONTENT_LENGTH)
    assert len(post.content) == MAX_CONTENT_LENGTH


@pytest.mark.parametrize("content", ["", "   ", "\n\t "])
def test_empty_or_whitespace_content_is_rejected(service, content):
    with pytest.raises(ContentEmptyError) as exc:
        service.prepare_post(1, content)
    assert exc.value.code == "content_empty"
    assert exc.value.field == "content"


def test_too_long_content_is_rejected(service):
    with pytest.raises(ContentTooLongError) as exc:
        service.prepare_post(1, "a" * (MAX_CONTENT_LENGTH + 1))
    assert exc.value.code == "content_too_long"


def test_unknown_author_is_rejected(service):
    with pytest.raises(AuthorNotFoundError) as exc:
        service.prepare_post(999, "hello")
    assert exc.value.code == "author_not_found"
    assert exc.value.field == "user_id"