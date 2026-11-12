import sqlite3

from src.instagram_lab import database


# Create a temporary SQLite posts table and point the database helper at it.
def _build_temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "stats.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(database.SCHEMA)
        conn.executemany(
            """
            INSERT INTO posts (url, creator, timestamp, saved, liked)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("https://example.com/1", "creator_a", 1704067200, 1, 0),
                ("https://example.com/2", "creator_a", 1735689600, 0, 1),
                ("https://example.com/3", "creator_b", 1767225600, 1, 1),
            ],
        )
    return db_path


# Check that stats totals, creator ranking, and year counts reflect the temporary database.
def test_stats_runs(tmp_path, monkeypatch):
    _build_temp_db(tmp_path, monkeypatch)

    stats = database.get_stats()

    assert stats["total"] == 3
    assert stats["saved_only"] == 1
    assert stats["liked_only"] == 1
    assert stats["both"] == 1
    assert stats["top_creators"] == [("creator_a", 2), ("creator_b", 1)]
    assert stats["per_year"] == {"2024": 1, "2025": 1, "2026": 1}
