from typing import Protocol

from app.domain.models import Post

MAX_CONTENT_LENGTH = 280


class PostServiceError(Exception):
    """Base class for expected, caller-facing errors of this service."""

    code: str = "post_service_error"

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


class ContentEmptyError(PostServiceError):
    code = "content_empty"


class ContentTooLongError(PostServiceError):
    code = "content_too_long"


class AuthorNotFoundError(PostServiceError):
    code = "author_not_found"


class AuthorDirectory(Protocol):
    """What the service needs to know about users. Implemented by the DB layer later."""

    def user_exists(self, user_id: int) -> bool: ...


class PostService:
    def __init__(self, authors: AuthorDirectory) -> None:
        self._authors = authors

    def prepare_post(self, user_id: int, content: str) -> Post:
        """Validate a post submission and return an unsaved ``Post``.

        Raises:
            ContentEmptyError: content is empty or only whitespace.
            ContentTooLongError: content exceeds MAX_CONTENT_LENGTH characters
                after surrounding whitespace is stripped.
            AuthorNotFoundError: no user with ``user_id`` exists.
        """
        cleaned = content.strip()
        if not cleaned:
            raise ContentEmptyError("content must not be empty", field="content")
        if len(cleaned) > MAX_CONTENT_LENGTH:
            raise ContentTooLongError(
                f"content must be at most {MAX_CONTENT_LENGTH} characters",
                field="content",
            )
        if not self._authors.user_exists(user_id):
            raise AuthorNotFoundError(f"user {user_id} does not exist", field="user_id")
        return Post(user_id=user_id, content=cleaned)