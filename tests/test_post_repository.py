import sqlite3

from app.db.database import SCHEMA
from app.db.post_repository import SqlitePostRepository


def make_connect(path):
    def connect():
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn

    return connect


def test_list_posts_returns_domain_posts_ordered_by_id(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO user (username) VALUES ('alice')")
    conn.executemany(
        "INSERT INTO post (user_id, content) VALUES (1, ?)", [("second",), ("first",)]
    )
    conn.commit()
    conn.close()

    posts = SqlitePostRepository(make_connect(db)).list_posts()

    assert [p.id for p in posts] == [1, 2]
    assert [p.content for p in posts] == ["second", "first"]
    assert all(p.user_id == 1 and p.created_at is not None for p in posts)


def test_list_posts_on_empty_table(tmp_path):
    db = tmp_path / "empty.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA)
    conn.close()
    assert SqlitePostRepository(make_connect(db)).list_posts() == []