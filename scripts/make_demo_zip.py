#!/usr/bin/env python3
"""Build a demo ZIP that mimics an Instagram export layout.

Reads tests/fixtures/demo_export.json and writes data/raw/demo_export.zip
with the same folder structure Meta uses:

    your_instagram_activity/likes/liked_posts.json
    your_instagram_activity/saved/saved_posts.json

The importer only cares that filenames end with `liked_posts.json` or
`saved_posts.json`, so the extra folder levels are safe.
"""
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "demo_export.json"
OUTPUT = ROOT / "data" / "raw" / "demo_export.zip"


def main() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()

    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "your_instagram_activity/likes/liked_posts.json",
            json.dumps({"likes_media_likes": data["likes_media_likes"]}, indent=2),
        )
        zf.writestr(
            "your_instagram_activity/saved/saved_posts.json",
            json.dumps({"saved_posts": data["saved_posts"]}, indent=2),
        )

    liked = len(data["likes_media_likes"])
    saved = len(data["saved_posts"])
    print(f"Built: {OUTPUT.relative_to(ROOT)}")
    print(f"  liked : {liked}")
    print(f"  saved : {saved}")
    print(f"  total : {liked + saved}")


if __name__ == "__main__":
    main()
