import sqlite3

from src.instagram_lab import database
from src.instagram_lab import cli


# Create a temporary SQLite posts table and point the export helper at it.
def _build_temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "export.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(database.SCHEMA)
        conn.execute(
            """
            INSERT INTO posts (url, creator, timestamp, saved, liked)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("https://example.com/known-post", "known_creator", 1704067200, 1, 0),
        )
    return db_path


# Check that the CLI writes a self-contained HTML file at the temporary output location.
def test_export_html_creates_file(tmp_path, monkeypatch):
    _build_temp_db(tmp_path, monkeypatch)
    output_dir = tmp_path / "html-output"
    monkeypatch.setattr(cli, "KNOWLEDGE_DIR", output_dir)
    monkeypatch.setattr(cli, "ensure_dirs", lambda: None)

    cli.cmd_export_html()

    output_file = output_dir / "index.html"
    assert output_file.exists()
    contents = output_file.read_text(encoding="utf-8")
    assert "<html>" in contents
    assert "https://example.com/known-post" in contents
