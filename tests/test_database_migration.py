import sqlite3

from src.instagram_lab import database
from src.instagram_lab.models import Post


# Verify connect() migrates the old posts schema and upsert persists caption metadata.
def test_database_migration_adds_caption_and_hashtags(tmp_path, monkeypatch):
    db_path = tmp_path / "old-schema.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE posts (
                url TEXT PRIMARY KEY,
                creator TEXT NOT NULL,
                timestamp INTEGER,
                saved INTEGER NOT NULL DEFAULT 0,
                liked INTEGER NOT NULL DEFAULT 0
            )
            """
        )

    conn = database.connect()
    columns = {row[1] for row in conn.execute("PRAGMA table_info(posts)")}
    conn.close()
    assert {"caption", "hashtags"} <= columns

    post = Post(
        url="https://www.instagram.com/p/migration-test/",
        creator="migration_creator",
        timestamp=1704067200,
        interaction="liked",
        caption="hello #python",
        hashtags="python",
    )
    database.upsert_posts([post])

    with database.connect() as conn:
        row = conn.execute(
            "SELECT caption, hashtags FROM posts WHERE url = ?", (post.url,)
        ).fetchone()
    assert row["caption"] == "hello #python"
    assert row["hashtags"] == "python"
