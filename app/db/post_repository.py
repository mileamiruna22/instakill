"""Database reads for posts. The only search-related module that talks to SQLite."""
from collections.abc import Callable
from contextlib import closing
import sqlite3

from app.db.database import get_connection
from app.domain.models import Post


class SqlitePostRepository:
    def __init__(self, connect: Callable[[], sqlite3.Connection] = get_connection) -> None:
        self._connect = connect

    def list_posts(self) -> list[Post]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT id, user_id, content, created_at FROM post ORDER BY id"
            ).fetchall()
        return [Post(**dict(row)) for row in rows]