# POC — Instagram Knowledge Lab (MVP)

**Version:** 0.1 (Proof of Concept)
**License:** MIT
**Branch:** dev

## What this project does

A local-first personal knowledge tool. It reads your own Instagram data export
(ZIP file downloaded from Meta), extracts every saved post and liked post, stores
them in a local SQLite database, and writes one Markdown file per post. You can
then search your 6,000+ saved/liked posts offline, by creator, by URL, by keyword.

**No scraping. No login. No cookies. No cloud.** Your export stays in `data/raw/`,
which is `.gitignore`d. Nothing is uploaded.

## Why it exists

You save and like thousands of Instagram posts, then forget what they were.
Instagram's UI doesn't let you search or filter them. This tool turns the export
into a queryable, greppable, browsable library.

## What it covers (v0.1)

- Read a Meta Instagram export ZIP (JSON format).
- Extract saved posts and liked posts from both export formats:
  - 2026 shape (`label_values` tree)
  - legacy shape (`string_list_data`)
- Deduplicate by URL across saved and liked.
- Store in SQLite (`data/db/library.db`).
- Generate one Markdown file per unique URL (`data/knowledge/`).
- Search by creator or URL.

## What it doesn't cover (by design)

- No media download (photos/videos). v0.3.
- No transcription or AI summary. v0.3–v0.4.
- No MCP server. v1.0.
- No `saved_collections.json` yet. v0.2.x.

Keeping the MVP small is deliberate. Each later version adds one capability.

## Requirements

- Ubuntu (or any Linux) or macOS
- Python 3.11+
- `uv` (https://astral.sh/uv)
- A valid Instagram data export ZIP

## Install

    sudo apt install -y python3 python3-venv git curl
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # reopen terminal
    cd ~/Projects
    git clone https://github.com/redaHamioui/instagram-knowledge-lab.git
    cd instagram-knowledge-lab
    uv sync

## Run

    # Put your export ZIP in data/raw/
    mv ~/Downloads/instagram-*.zip data/raw/

    uv run python main.py import
    uv run python main.py list
    uv run python main.py search <keyword>

## Project structure

    src/instagram_lab/
      config.py       # paths
      models.py       # Post dataclass
      importer.py     # reads the ZIP, handles both export shapes
      database.py     # SQLite, dedup via ON CONFLICT
      markdown.py     # one .md per unique URL
      search.py       # keyword search
      cli.py          # import / list / search

    tests/
      test_importer.py                # both shapes
      test_importer_list_shape.py     # list-root regression
      test_importer_real_shape.py     # 2026 label_values regression

    data/            # gitignored — never committed
      raw/           # your ZIP
      db/            # SQLite file
      knowledge/     # generated .md files

## Privacy & safety

- `data/` is fully gitignored.
- No cookie, no session token, no password in the repo.
- No real personal data committed. Tests use `tests/fixtures/` with fake creators.
- Nothing leaves your machine. No server, no telemetry.

## Verified on real data

- 6,988 raw records (365 saved + 6,623 liked)
- 6,700 unique posts after dedup (288 posts appear in both)
- Import time: < 1 second
- 4 tests passing

## BYOP notes

This project is my own. I created it, I own it, it is not for an employer or
client. It processes only the user's own data export (which the user owns per
GDPR). No third-party data, no regulated data, no security tooling, no AI
training. Public under MIT license.

## What comes next

See `ROADMAP.md`. Planned versions: v0.2 (stats + HTML browser), v0.3 (media +
transcription), v0.4 (AI summaries), v1.0 (multi-provider).
