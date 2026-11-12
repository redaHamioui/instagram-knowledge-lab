# Data Handling & Scope

This document explicitly states what Instagram Knowledge Lab stores, why, and
what it does NOT store. It exists to clarify that the project processes only
the user's own Instagram export and only public fields from that export.

## What this project stores

By default (mode=own), the tool stores ONLY posts authored by the
account owner:

- own post caption (`title` field in `posts_*.json`)
- own post timestamp (`creation_timestamp`)
- own post media reference (`uri`, local file path inside the ZIP)
- a synthetic internal URL (`instagram://own/<hash>`) used as primary
  key — no external Instagram URL is stored for own posts
- hashtags derived from the owner's own caption

In mode=all (opt-in), the tool ALSO stores:
- public permalink, public creator handle, public caption, public
  hashtags from posts the user SAVED or LIKED
- the user's own saved/liked flags

Both modes store nothing about other people beyond fields already
visible publicly on instagram.com. No DMs, no followers, no private
data.

## What this project does NOT store

- No direct messages (DMs)
- No follower or following lists
- No private-account content
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

This project is personal infrastructure built by its owner for their own use.
The default import mode processes only the account owner's own posts.

## User's rights

The user owns their Instagram export (exported by themselves from Meta,
subject to GDPR/CCPA data portability rights). The user owns this repository.
The user owns the generated library. No one else has access to any of it.

## BYOP default behavior

The default execution (`import`) processes only the user's own posts.
Processing of third-party public content requires the explicit opt-in
`--mode=all` flag, never set by default, never set by tests.
