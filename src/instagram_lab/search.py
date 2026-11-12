"""Tiny wrapper around database.search for the CLI."""
from .database import search

def print_results(keyword: str) -> None:
    rows = search(keyword)
    if not rows:
        print(f"No results for: {keyword}")
        return
    print(f"Found {len(rows)} result(s) for '{keyword}':\n")
    for r in rows:
        tags = []
        if r["saved"]:
            tags.append("saved")
        if r["liked"]:
            tags.append("liked")
        print(f"  [{','.join(tags)}] @{r['creator']}  {r['url']}")