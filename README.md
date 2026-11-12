# Instagram Personal Archive Manager

> A local-first knowledge manager for **your own** Instagram activity —
> saved, liked, and self-authored posts. Turns your personal data export
> into a searchable, offline Markdown + SQLite library. No scraping, no
> login, no cloud. See `DATA_HANDLING.md` for the explicit data scope.

A local-first personal library that turns your Instagram data export into a
searchable Markdown knowledge base.

## What it does

1. Reads the official Instagram data export (ZIP, JSON).
2. Extracts saved and liked posts.
3. Stores them in SQLite.
4. Generates one Markdown file per post.
5. Searches by keyword.

**Default scope:** the tool imports only posts authored by the account
owner — your own posts. Saved and liked posts (which contain other
creators' handles) are opt-in via `--mode=all`. See DATA_HANDLING.md.

## Run it

    uv sync
    uv run python scripts/make_demo_zip.py
    uv run python main.py import             # default: only your OWN posts (BYOP-safe)
    uv run python main.py import --mode=all  # opt-in: also import saved + liked posts

If `--mode=own` prints "No own-posts found", your export did not
include your own posts. Use `--mode=all` to import the saved and
liked posts instead.

    uv run python main.py list
    uv run python main.py search term

## Try without real data

20 fake posts in `tests/fixtures/demo_export.json`. No Instagram login needed.

## Privacy

`data/` is gitignored. Nothing leaves your machine.

## License

MIT — see [LICENSE](./LICENSE).

## Data scope

See [DATA_HANDLING.md](./DATA_HANDLING.md) for the exact list of fields
stored and never stored.
