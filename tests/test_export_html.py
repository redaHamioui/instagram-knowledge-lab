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
            INSERT INTO posts (url, creator, timestamp, saved, liked, caption, hashtags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("https://example.com/known-post", "known_creator", 1704067200, 1, 0, None, None),
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
    assert "<html" in contents
    assert "https://example.com/known-post" in contents


# Check that captions and hashtags are included in the exported offline HTML data.
def test_export_html_renders_caption(tmp_path, monkeypatch):
    db_path = _build_temp_db(tmp_path, monkeypatch)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE posts SET caption = ?, hashtags = ?",
            ("hello world", "python,flask"),
        )
    output_dir = tmp_path / "caption-html-output"
    monkeypatch.setattr(cli, "KNOWLEDGE_DIR", output_dir)
    monkeypatch.setattr(cli, "ensure_dirs", lambda: None)

    cli.cmd_export_html()

    contents = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "hello world" in contents
    assert "python,flask" in contents
