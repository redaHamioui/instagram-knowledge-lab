"""Generate one .md file per unique URL inside data/knowledge/."""
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from pathlib import Path
from .config import KNOWLEDGE_DIR, ensure_dirs


def _slug(url: str) -> str:
    path = urlparse(url).path
    parts = [p for p in path.split("/") if p]
    tail = parts[-1] if parts else "post"
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", tail)
    return safe or "post"


def write_post_row(url: str, creator: str, timestamp: int | None,
                   saved: bool, liked: bool) -> Path:
    ensure_dirs()
    filename = f"{_slug(url)}.md"
    path = KNOWLEDGE_DIR / filename

    date_str = "unknown"
    if timestamp:
        try:
            date_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
        except (ValueError, OSError):
            pass

    tags = []
    if saved: tags.append("saved")
    if liked: tags.append("liked")
    interaction = "+".join(tags) or "unknown"

    content = f"""---
url: {url}
creator: {creator}
date: {date_str}
saved: {str(saved).lower()}
liked: {str(liked).lower()}
---

# @{creator} — {interaction}

- **URL:** {url}
- **Creator:** @{creator}
- **Date:** {date_str}
- **Saved:** {saved}
- **Liked:** {liked}

## Notes

(Write here why you saved or liked this post.)
"""
    path.write_text(content, encoding="utf-8")
    return path
