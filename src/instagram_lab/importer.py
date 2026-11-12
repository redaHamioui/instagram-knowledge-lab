"""Read the Instagram export ZIP and return a list of Post objects.

Supports both shapes seen in Meta exports:
  OLD: {"title":"user","string_list_data":[{"href":"...","timestamp":N}]}
  NEW (2026): [{"timestamp":N,"fbid":"...","media":[],"label_values":[...]}]
"""
import hashlib
import json
import re
import zipfile
from pathlib import Path
from .models import Post

SAVED_PATTERNS = ("saved_posts.json",)
LIKED_PATTERNS = ("liked_posts.json",)
OWN_PATTERNS = ("posts_1.json", "posts_2.json", "posts_3.json",
                "posts_4.json", "posts_5.json", "posts.json")


def _find_files(zf: zipfile.ZipFile, patterns: tuple[str, ...]) -> list[str]:
    return [n for n in zf.namelist() if any(n.endswith(p) for p in patterns)]


def _iter_records(data):
    if isinstance(data, list):
        for r in data:
            if isinstance(r, dict):
                yield r
        return
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                for r in v:
                    if isinstance(r, dict):
                        yield r


def _collect_labels(obj, out: dict) -> None:
    if isinstance(obj, dict):
        label = obj.get("label")
        if isinstance(label, str) and label:
            val = obj.get("value")
            if val is None or (isinstance(val, str) and not val.strip()):
                val = obj.get("href")
            if val is not None and not isinstance(val, (dict, list)):
                out.setdefault(label, val)
        for v in obj.values():
            _collect_labels(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_labels(item, out)


def _find_label(labels: dict, *names: str) -> str | None:
    for name in names:
        for key, value in labels.items():
            if key.lower() == name.lower() and isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _extract(record: dict, interaction: str) -> Post | None:
    if not isinstance(record, dict):
        return None

    if "label_values" in record:
        labels: dict = {}
        _collect_labels(record.get("label_values", []), labels)
        url = _find_label(labels, "URL", "Url", "Post URL")
        if not url:
            return None
        creator = _find_label(labels, "Name", "Username", "Title") or "unknown"
        caption = _find_label(labels, "Caption")
        if caption:
            caption = caption[:2000] or None
        hashtags = None
        if caption:
            unique_tags = list(dict.fromkeys(
                match.lower() for match in re.findall(r"#(\w+)", caption)
            ))
            hashtags = ",".join(unique_tags) or None
        ts = record.get("timestamp")
        timestamp = ts if isinstance(ts, int) else None
        try:
            return Post(
                url=url, creator=creator, timestamp=timestamp,
                interaction=interaction, caption=caption, hashtags=hashtags,
            )
        except ValueError:
            return None

    items = record.get("string_list_data") or []
    if not items:
        return None
    first = items[0]
    if not isinstance(first, dict):
        return None
    url = first.get("href")
    if not url:
        return None
    creator = record.get("title") or first.get("value") or "unknown"
    ts = first.get("timestamp")
    timestamp = ts if isinstance(ts, int) else None
    try:
        return Post(url=url, creator=creator, timestamp=timestamp, interaction=interaction)
    except ValueError:
        return None


def _extract_own(record: dict) -> Post | None:
    """Extract a Post from an own-posts record (your_instagram_activity/content)."""
    if not isinstance(record, dict):
        return None
    media = record.get("media")
    if not isinstance(media, list) or not media or not isinstance(media[0], dict):
        return None
    item = media[0]
    uri = item.get("uri")
    identity = record.get("fbid") or item.get("fbid") or uri
    if not identity:
        return None
    digest = hashlib.sha256(str(identity).encode("utf-8")).hexdigest()
    url = f"instagram://own/{digest}"
    caption = item.get("title")
    if isinstance(caption, str):
        caption = caption[:2000] or None
    else:
        caption = None
    hashtags = None
    if caption:
        unique_tags = list(dict.fromkeys(
            match.lower() for match in re.findall(r"#(\w+)", caption)
        ))
        hashtags = ",".join(unique_tags) or None
    ts = item.get("creation_timestamp")
    timestamp = ts if isinstance(ts, int) else None
    try:
        return Post(
            url=url, creator="me", timestamp=timestamp, interaction="own",
            caption=caption, hashtags=hashtags,
        )
    except ValueError:
        return None


def import_export(zip_path: Path, mode: str = "own") -> list[Post]:
    if mode not in {"own", "all"}:
        raise ValueError(f"Unknown mode: {mode}")
    posts: list[Post] = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in _find_files(zf, OWN_PATTERNS):
            try:
                data = json.loads(zf.read(name))
            except json.JSONDecodeError:
                continue
            for record in _iter_records(data):
                post = _extract_own(record)
                if post:
                    posts.append(post)
        if mode == "all":
            for patterns, interaction in (
                (SAVED_PATTERNS, "saved"),
                (LIKED_PATTERNS, "liked"),
            ):
                for name in _find_files(zf, patterns):
                    try:
                        data = json.loads(zf.read(name))
                    except json.JSONDecodeError:
                        continue
                    for record in _iter_records(data):
                        post = _extract(record, interaction)
                        if post:
                            posts.append(post)
    return posts
