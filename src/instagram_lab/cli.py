"""CLI: `uv run python main.py <command>`."""
import sys
from .config import RAW_DIR, KNOWLEDGE_DIR, ensure_dirs
from .importer import import_export
from .database import upsert_posts, all_posts
from .markdown import write_post_row
from .search import print_results


def cmd_import() -> None:
    ensure_dirs()
    zips = sorted(RAW_DIR.glob("*.zip"))
    if not zips:
        print(f"No ZIP found in {RAW_DIR}")
        print("Put your Instagram export ZIP there first.")
        return

    for z in zips:
        print(f"Importing: {z.name}")
        posts = import_export(z)
        print(f"  Found {len(posts)} raw records")
        touched = upsert_posts(posts)
        print(f"  Saved to database: {touched}")

    rows = all_posts()
    for row in rows:
        write_post_row(
            url=row["url"],
            creator=row["creator"],
            timestamp=row["timestamp"],
            saved=bool(row["saved"]),
            liked=bool(row["liked"]),
        )
    print(f"  Markdown written: {len(rows)} files in {KNOWLEDGE_DIR}")


def cmd_list() -> None:
    rows = all_posts()
    print(f"{len(rows)} posts in library")
    for r in rows[:20]:
        tags = []
        if r["saved"]: tags.append("saved")
        if r["liked"]: tags.append("liked")
        print(f"  [{','.join(tags)}] @{r['creator']}  {r['url']}")


def cmd_search(keyword: str) -> None:
    print_results(keyword)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  uv run python main.py import")
        print("  uv run python main.py list")
        print("  uv run python main.py search <keyword>")
        return

    command = sys.argv[1]
    if command == "import":
        cmd_import()
    elif command == "list":
        cmd_list()
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: uv run python main.py search <keyword>")
            return
        cmd_search(sys.argv[2])
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
