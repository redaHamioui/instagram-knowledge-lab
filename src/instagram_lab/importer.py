"""Read the Instagram export ZIP and return a list of Post objects.

Supports both shapes seen in Meta exports:
  OLD: {"title":"user","string_list_data":[{"href":"...","timestamp":N}]}
  NEW (2026): [{"timestamp":N,"fbid":"...","media":[],
                "label_values":[{"label":"URL","value":"https://..."},
                                {"dict":[{"dict":[{"label":"Name","value":"user"}]}]}]}]
"""
import json
import re
import zipfile
from pathlib import Path
from .models import Post

SAVED_PATTERNS = ("saved_posts.json",)
LIKED_PATTERNS = ("liked_posts.json",)


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
        for k, v in labels.items():
            if k.lower() == name.lower() and isinstance(v, str) and v.strip():
                return v.strip()
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


def import_export(zip_path: Path) -> list[Post]:
    posts: list[Post] = []
    with zipfile.ZipFile(zip_path) as zf:
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
