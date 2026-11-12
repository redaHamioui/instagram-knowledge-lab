# Instagram Knowledge Lab

A local-first personal library that turns your Instagram data export into a
searchable Markdown knowledge base.

## What it does

1. Reads the official Instagram data export (ZIP, JSON).
2. Extracts saved and liked posts.
3. Stores them in SQLite.
4. Generates one Markdown file per post.
5. Searches by keyword.

## Run it

    uv sync
    uv run python scripts/make_demo_zip.py
    uv run python main.py import
    uv run python main.py list
    uv run python main.py search term

## Try without real data

20 fake posts in `tests/fixtures/demo_export.json`. No Instagram login needed.

## Privacy

`data/` is gitignored. Nothing leaves your machine.

## License

MIT — see [LICENSE](./LICENSE).
