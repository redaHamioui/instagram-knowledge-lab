"""SQLite storage. One table, simple and safe."""
import sqlite3
from pathlib import Path
from .models import Post
from .config import DB_PATH, ensure_dirs

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    url         TEXT PRIMARY KEY,
    creator     TEXT NOT NULL,
    timestamp   INTEGER,
    saved       INTEGER NOT NULL DEFAULT 0,
    liked       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_creator ON posts(creator);
"""

def connect() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def upsert_posts(posts: list[Post]) -> int:
    """Insert or update posts. Returns number of rows touched."""
    with connect() as conn:
        touched = 0
        for p in posts:
            saved_flag = 1 if p.interaction == "saved" else 0
            liked_flag = 1 if p.interaction == "liked" else 0
            # Keep existing flags, OR them with the new one
            conn.execute(
                """
                INSERT INTO posts (url, creator, timestamp, saved, liked)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    saved   = MAX(posts.saved, excluded.saved),
                    liked   = MAX(posts.liked, excluded.liked),
                    creator = excluded.creator,
                    timestamp = COALESCE(excluded.timestamp, posts.timestamp)
                """,
                (p.url, p.creator, p.timestamp, saved_flag, liked_flag),
            )
            touched += 1
    return touched

def all_posts() -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute("SELECT * FROM posts ORDER BY timestamp DESC").fetchall()

def search(keyword: str) -> list[sqlite3.Row]:
    like = f"%{keyword}%"
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM posts WHERE url LIKE ? OR creator LIKE ? LIMIT 50",
            (like, like),
        ).fetchall()