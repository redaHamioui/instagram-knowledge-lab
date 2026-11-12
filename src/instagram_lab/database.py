"""SQLite storage. One table, simple and safe."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .models import Post
from .config import DB_PATH, ensure_dirs

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    url         TEXT PRIMARY KEY,
    creator     TEXT NOT NULL,
    timestamp   INTEGER,
    saved       INTEGER NOT NULL DEFAULT 0,
    liked       INTEGER NOT NULL DEFAULT 0,
    caption     TEXT,
    hashtags    TEXT
);
CREATE INDEX IF NOT EXISTS idx_creator ON posts(creator);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Add caption metadata columns to databases created by earlier versions."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(posts)")}
    if "caption" not in columns:
        conn.execute("ALTER TABLE posts ADD COLUMN caption TEXT")
    if "hashtags" not in columns:
        conn.execute("ALTER TABLE posts ADD COLUMN hashtags TEXT")


def connect() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
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
                INSERT INTO posts (url, creator, timestamp, saved, liked, caption, hashtags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    saved   = MAX(posts.saved, excluded.saved),
                    liked   = MAX(posts.liked, excluded.liked),
                    creator = excluded.creator,
                    timestamp = COALESCE(excluded.timestamp, posts.timestamp),
                    caption = COALESCE(excluded.caption, posts.caption),
                    hashtags = COALESCE(excluded.hashtags, posts.hashtags)
                """,
                (p.url, p.creator, p.timestamp, saved_flag, liked_flag, p.caption, p.hashtags),
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

# Return interaction totals, the ten most frequent creators, and post counts by UTC year.
def get_stats() -> dict:
    conn = sqlite3.connect(DB_PATH)
    try:
        totals = conn.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(SUM(saved = 1 AND liked = 0), 0),
                COALESCE(SUM(saved = 0 AND liked = 1), 0),
                COALESCE(SUM(saved = 1 AND liked = 1), 0)
            FROM posts
            """
        ).fetchone()
        top_creators = conn.execute(
            """
            SELECT creator, COUNT(*) AS post_count
            FROM posts
            GROUP BY creator
            ORDER BY post_count DESC, creator COLLATE NOCASE ASC
            LIMIT 10
            """
        ).fetchall()
        year_rows = conn.execute(
            """
            SELECT strftime('%Y', timestamp, 'unixepoch') AS year, COUNT(*)
            FROM posts
            WHERE timestamp IS NOT NULL
            GROUP BY year
            HAVING year IS NOT NULL
            ORDER BY year
            """
        ).fetchall()
        return {
            "total": totals[0],
            "saved_only": totals[1],
            "liked_only": totals[2],
            "both": totals[3],
            "top_creators": [(row[0], row[1]) for row in top_creators],
            "per_year": {row[0]: row[1] for row in year_rows},
        }
    finally:
        conn.close()

# Return every post as a plain dictionary with a UTC date string and boolean interaction flags.
def export_rows_as_dicts() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT url, creator, timestamp, saved, liked, caption, hashtags
            FROM posts
            ORDER BY timestamp DESC, creator COLLATE NOCASE ASC
            """
        ).fetchall()

    result = []
    for row in rows:
        url, creator, timestamp, saved, liked, caption, hashtags = row
        date = "unknown"
        if timestamp is not None:
            try:
                date = datetime.fromtimestamp(
                    int(timestamp), tz=timezone.utc
                ).strftime("%Y-%m-%d")
            except (OverflowError, OSError, TypeError, ValueError):
                pass
        result.append({
            "url": url,
            "creator": creator,
            "date": date,
            "saved": bool(saved),
            "liked": bool(liked),
            "caption": caption or "",
            "hashtags": hashtags or "",
        })
    return result
