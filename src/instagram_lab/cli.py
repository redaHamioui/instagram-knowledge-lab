"""CLI: `uv run python main.py <command>`."""
import json
import sys
from .config import RAW_DIR, KNOWLEDGE_DIR, ensure_dirs
from .importer import import_export
from .database import (
    upsert_posts,
    all_posts,
    get_stats,
    export_rows_as_dicts,
)
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
        if r["saved"]:
            tags.append("saved")
        if r["liked"]:
            tags.append("liked")
        print(f"  [{','.join(tags)}] @{r['creator']}  {r['url']}")


def cmd_search(keyword: str) -> None:
    print_results(keyword)


# Print library totals, the leading creators, and counts grouped by year.
def cmd_stats() -> None:
    stats = get_stats()
    print("Instagram library statistics")
    print(f"{'Metric':<22}{'Count':>10}")
    print(f"{'Total posts':<22}{stats['total']:>10}")
    print(f"{'Saved only':<22}{stats['saved_only']:>10}")
    print(f"{'Liked only':<22}{stats['liked_only']:>10}")
    print(f"{'Both saved and liked':<22}{stats['both']:>10}")

    print("\nTop creators")
    print(f"{'Creator':<32}{'Posts':>10}")
    for creator, count in stats["top_creators"]:
        print(f"{creator:<32}{count:>10}")

    print("\nPosts per year (UTC)")
    print(f"{'Year':<22}{'Posts':>10}")
    for year, count in stats["per_year"].items():
        print(f"{year:<22}{count:>10}")


# Export the library to a single offline HTML page with live search and filters.
def cmd_export_html() -> None:
    rows = export_rows_as_dicts()
    ensure_dirs()
    output_path = KNOWLEDGE_DIR / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    embedded_rows = json.dumps(rows, ensure_ascii=False).replace("<", "\\u003c")
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Instagram Knowledge Library</title>
  <style>
    :root { color-scheme: light; font-family: system-ui, sans-serif; }
    body { max-width: 1000px; margin: 2rem auto; padding: 0 1rem; color: #202124; }
    h1 { margin-bottom: 0.3rem; }
    .controls { display: grid; gap: 0.8rem; margin: 1.5rem 0; }
    input[type="search"], select { box-sizing: border-box; width: 100%; padding: 0.7rem; }
    .checks { display: flex; flex-wrap: wrap; gap: 1rem; }
    .checks label { white-space: nowrap; }
    #result-count { color: #555; margin: 1rem 0; }
    #results { display: grid; gap: 0.7rem; padding: 0; list-style: none; }
    .post { border: 1px solid #ddd; border-radius: 0.5rem; padding: 1rem; }
    .post-line { display: flex; flex-wrap: wrap; align-items: center; gap: 0.7rem; }
    .creator { font-weight: 700; }
    .date { color: #555; }
    .tag { border-radius: 999px; padding: 0.15rem 0.6rem; background: #eee; font-size: 0.85rem; }
    .tag.saved { background: #e7f2ff; }
    .tag.liked { background: #ffe8ec; }
    a { overflow-wrap: anywhere; }
  </style>
</head>
<body>
  <h1>Instagram Knowledge Library</h1>
  <section class="controls" aria-label="Library filters">
    <label>
      Search creator or URL
      <input id="search" type="search" placeholder="Type to filter..." autocomplete="off">
    </label>
    <div class="checks">
      <label><input id="saved-only" type="checkbox" checked> Saved only</label>
      <label><input id="liked-only" type="checkbox" checked> Liked only</label>
      <label><input id="show-both" type="checkbox" checked> Both</label>
    </div>
    <label>
      Creator
      <select id="creator">
        <option value="">All creators</option>
      </select>
    </label>
  </section>
  <p id="result-count" aria-live="polite"></p>
  <ul id="results"></ul>
  <script>
    const ROWS = __ROWS__;

    const creatorCounts = new Map();
    ROWS.forEach((row) => {
      creatorCounts.set(row.creator, (creatorCounts.get(row.creator) || 0) + 1);
    });
    const creatorSelect = document.getElementById("creator");
    [...creatorCounts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 50)
      .forEach(([creator]) => {
        const option = document.createElement("option");
        option.value = creator;
        option.textContent = creator;
        creatorSelect.appendChild(option);
      });

    // Render the posts matching the current search text and filter controls.
    function renderResults() {
      const query = document.getElementById("search").value.trim().toLocaleLowerCase();
      const selectedCreator = creatorSelect.value;
      const includeSaved = document.getElementById("saved-only").checked;
      const includeLiked = document.getElementById("liked-only").checked;
      const includeBoth = document.getElementById("show-both").checked;
      const filtered = ROWS.filter((row) => {
        const matchesText =
          row.creator.toLocaleLowerCase().includes(query) ||
          row.url.toLocaleLowerCase().includes(query);
        const matchesCreator = !selectedCreator || row.creator === selectedCreator;
        const category = row.saved && row.liked
          ? "both"
          : row.saved
            ? "saved"
            : "liked";
        const matchesCategory =
          (category === "saved" && includeSaved) ||
          (category === "liked" && includeLiked) ||
          (category === "both" && includeBoth);
        return matchesText && matchesCreator && matchesCategory;
      });

      const results = document.getElementById("results");
      results.replaceChildren();
      document.getElementById("result-count").textContent =
        `${filtered.length} result${filtered.length === 1 ? "" : "s"}`;

      filtered.forEach((row) => {
        const item = document.createElement("li");
        item.className = "post";
        const line = document.createElement("div");
        line.className = "post-line";

        const creator = document.createElement("span");
        creator.className = "creator";
        creator.textContent = row.creator;
        line.appendChild(creator);

        const date = document.createElement("span");
        date.className = "date";
        date.textContent = row.date;
        line.appendChild(date);

        if (row.saved) {
          const tag = document.createElement("span");
          tag.className = "tag saved";
          tag.textContent = "saved";
          line.appendChild(tag);
        }
        if (row.liked) {
          const tag = document.createElement("span");
          tag.className = "tag liked";
          tag.textContent = "liked";
          line.appendChild(tag);
        }

        const link = document.createElement("a");
        link.textContent = row.url;
        link.href = row.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        line.appendChild(link);

        item.appendChild(line);
        results.appendChild(item);
      });
    }

    document.getElementById("search").addEventListener("input", renderResults);
    document.getElementById("saved-only").addEventListener("change", renderResults);
    document.getElementById("liked-only").addEventListener("change", renderResults);
    document.getElementById("show-both").addEventListener("change", renderResults);
    creatorSelect.addEventListener("change", renderResults);
    renderResults();
  </script>
</body>
</html>
""".replace("__ROWS__", embedded_rows)

    output_path.write_text(html, encoding="utf-8")
    print(f"HTML library written to {output_path}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  uv run python main.py import")
        print("  uv run python main.py list")
        print("  uv run python main.py search <keyword>")
        print("  uv run python main.py stats")
        print("  uv run python main.py export-html")
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
    elif command == "stats":
        cmd_stats()
    elif command == "export-html":
        cmd_export_html()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
