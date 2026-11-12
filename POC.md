# POC — Instagram Knowledge Lab (MVP)

**Version:** 0.1 (Proof of Concept)
**License:** MIT
**Branch:** dev

## What it does

A local-first personal knowledge tool. Reads your own Instagram data export
(ZIP from Meta), extracts every saved and liked post, stores them in a local
SQLite database, and writes one Markdown file per post. Then you can search
your 6,000+ saved/liked posts offline — by creator, URL, or keyword.

**No scraping. No login. No cookies. No cloud.** Your export stays in
`data/raw/`, which is gitignored. Nothing is uploaded.

## Why it exists

You save and like thousands of posts, then forget what they were. Instagram
doesn't let you search or filter them. This turns the export into a
queryable, greppable, browsable library.

## What it covers (v0.1 + v0.2)

- Read a Meta Instagram export ZIP (JSON format).
- Handle both export shapes: 2026 (`label_values` tree) and legacy
  (`string_list_data`).
- Deduplicate by URL across saved and liked.
- Store in SQLite (`data/db/library.db`).
- One Markdown file per unique URL (`data/knowledge/`).
- `search` — by creator or URL.
- `stats` — totals, top-10 creators, per-year counts.
- `export-html` — self-contained `index.html` with live search, saved/liked
  filters, creator dropdown. Opens offline in Firefox.

## What it doesn't cover (by design)

- No media download (photos/videos). v0.3.
- No transcription / AI summary. v0.3–v0.4.
- No MCP server. v1.0.
- No `saved_collections.json`. v0.2.x.

Keeping the MVP small is deliberate. Each version adds one capability.

## Requirements

- Ubuntu (or any Linux) or macOS
- Python 3.11+
- `uv` (https://astral.sh/uv)
- A valid Instagram data export ZIP

## Install

    sudo apt install -y python3 python3-venv git curl
    curl -LsSf https://astral.sh/uv/install.sh | sh   # reopen terminal
    cd ~/Projects
    git clone https://github.com/redaHamioui/instagram-knowledge-lab.git
    cd instagram-knowledge-lab
    uv sync

## Run

    mv ~/Downloads/instagram-*.zip data/raw/
    uv run python main.py import
    uv run python main.py list
    uv run python main.py search <keyword>
    uv run python main.py stats
    uv run python main.py export-html

## Project structure

    src/instagram_lab/
      config.py    models.py    importer.py    database.py
      markdown.py  search.py    cli.py

    tests/
      test_importer.py                # both export shapes
      test_importer_list_shape.py     # list-root regression
      test_importer_real_shape.py     # 2026 label_values regression
      test_stats.py                   # stats totals + per-year
      test_export_html.py             # HTML created, contains URL

    data/          # gitignored
      raw/         # your ZIP
      db/          # SQLite file
      knowledge/   # generated .md + index.html

## Privacy & safety

- `data/` is fully gitignored.
- No cookie, session token, or password in the repo.
- No real personal data committed. Tests use `tests/fixtures/` with fake
  creators.
- Nothing leaves your machine. No server, no telemetry.

## Verified on real data

- 6,988 raw records (365 saved + 6,623 liked)
- 6,700 unique posts after dedup (288 posts appear in both)
- Import time: < 1 second
- 6 tests passing (v0.1: 4, v0.2: 2)

## BYOP notes

This project is my own. I created it, I own it, it is not for an employer or
client. It processes only the user's own data export (which the user owns per
GDPR). No third-party data, no regulated data, no security tooling, no AI
training. Public under MIT license.

## What's next

See `ROADMAP.md`. v0.2 (stats + HTML) done; v0.3 (media + transcription),
v0.4 (AI summaries), v1.0 (multi-provider).
