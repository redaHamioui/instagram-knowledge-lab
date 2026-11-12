# Data Handling & Scope

This document explicitly states what Instagram Knowledge Lab stores, why, and
what it does NOT store. It exists to clarify that the project processes only
the user's own Instagram export and only public fields from that export.

## What this project stores (all from the user's own export)

From the user's own Instagram data export ZIP (downloaded by the user from
Meta), the tool extracts and stores locally:

- `url` — the public permalink of each post (already public on instagram.com)
- `creator` — the public handle of the post author (already public)
- `caption` — the public caption text (already public)
- `hashtags` — hashtags found inside the public caption
- `timestamp` — when the user saved or liked the post (the user's own action)
- `saved` / `liked` — boolean flags for the user's own action

Every field above is either public data (visible to anyone on instagram.com)
or the user's own behavioral data (their own saved/liked choices). No field
describes another person's private life.

## What this project does NOT store

- No direct messages (DMs)
- No follower or following lists
- No personal information about other users beyond their public handle
- No private-account content (private accounts don't appear in exports)
- No location data beyond what appears in public captions
- No email addresses, phone numbers, or contact data
- No profile pictures, no biometric data, no images of faces

## What this project does NOT do

- No scraping of Instagram (no browser automation, no session cookies)
- No connection to Instagram's servers (works entirely offline on a ZIP)
- No uploading of any data (no server, no telemetry, no cloud)
- No sharing with third parties
- No AI training, no model fine-tuning, no dataset creation
- No processing of any data not explicitly downloaded by the user themselves

## Privacy by design

- The `data/` folder (export, database, generated files) is `.gitignore`d.
- Nothing personal is ever committed to the repository.
- The repository contains only code and synthetic test fixtures with clearly
  fake handles (`fake_creator_1`, `someone`, `creator_a`, etc.).
- No real Instagram data is required to run the tests.

## BYOP compliance

This project is not in BYOP's exclusion list:
- It does not process other people's personal data — it processes public
  posts plus the user's own saved/liked behavior.
- It does not process regulated data (no health, financial, or legal records).
- It is not security tooling, not AI training, not model infrastructure.
- It is personal infrastructure built by its owner for their own use.

## User's rights

The user owns their Instagram export (exported by themselves from Meta,
subject to GDPR/CCPA data portability rights). The user owns this repository.
The user owns the generated library. No one else has access to any of it.
