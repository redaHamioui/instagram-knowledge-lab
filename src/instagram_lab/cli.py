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
            caption=row["caption"],
            hashtags=row["hashtags"],
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


# Export all posts into a searchable, responsive offline HTML library.
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
    body { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; color: #202124; }
    h1 { margin: 0 0 .4rem; }
    .totals { color: #555; margin-bottom: 1.5rem; }
    .controls { display: flex; flex-wrap: wrap; gap: .8rem; align-items: center; margin: 1.2rem 0; }
    input[type="search"], select { box-sizing: border-box; padding: .65rem; border: 1px solid #ddd; border-radius: .4rem; background: white; color: #202124; }
    input[type="search"] { flex: 1 1 280px; }
    select { flex: 0 1 220px; }
    .tabs { display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0; }
    .tab { cursor: pointer; border: 1px solid #ddd; border-radius: 999px; padding: .5rem .9rem; background: white; color: #202124; }
    .tab.active { background: #202124; color: white; border-color: #202124; }
    #result-count { color: #555; margin: 1rem 0; }
    #results { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; padding: 0; list-style: none; }
    .post { border: 1px solid #ddd; border-radius: .7rem; padding: 1rem; background: #fff; transition: box-shadow .15s ease, transform .15s ease; }
    .post:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); transform: translateY(-2px); }
    .post-head { display: flex; flex-wrap: wrap; align-items: center; gap: .55rem; margin-bottom: .7rem; }
    .creator { font-weight: 700; }
    .date { color: #666; font-size: .9rem; }
    .chip, .hashtag { display: inline-block; border-radius: 999px; padding: .18rem .6rem; font-size: .82rem; }
    .chip { background: #eee; }
    .chip.saved { background: #e7f2ff; }
    .chip.liked { background: #ffe8ec; }
    .caption { line-height: 1.45; margin: .6rem 0; overflow-wrap: anywhere; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; line-clamp: 3; overflow: hidden; }
    .hashtags { display: flex; flex-wrap: wrap; gap: .35rem; margin: .6rem 0; }
    .hashtag { background: #f1f1f1; }
    .post-link { display: inline-block; overflow-wrap: anywhere; margin-top: .3rem; }
    .empty { color: #555; padding: 1.5rem 0; }
  </style>
</head>
<body>
  <h1>Instagram Knowledge Library</h1>
  <p id="totals" class="totals"></p>
  <div class="tabs" role="tablist" aria-label="Post type">
    <button class="tab active" type="button" data-filter="all" aria-selected="true">All</button>
    <button class="tab" type="button" data-filter="saved" aria-selected="false">Saved only</button>
    <button class="tab" type="button" data-filter="liked" aria-selected="false">Liked only</button>
    <button class="tab" type="button" data-filter="both" aria-selected="false">Both</button>
  </div>
  <section class="controls" aria-label="Search, hashtag and sort">
    <input id="search" type="search" placeholder="Search creator, caption, hashtags or URL" autocomplete="off">
    <select id="hashtag"><option value="">All hashtags</option></select>
    <select id="sort" aria-label="Sort posts">
      <option value="newest">Newest first</option>
      <option value="oldest">Oldest first</option>
      <option value="creator">Creator A-Z</option>
    </select>
  </section>
  <p id="result-count" aria-live="polite"></p>
  <ul id="results"></ul>
  <script>
    const ROWS = __ROWS__;
    const totals = document.getElementById("totals");
    const savedCount = ROWS.filter((row) => row.saved).length;
    const likedCount = ROWS.filter((row) => row.liked).length;
    const bothCount = ROWS.filter((row) => row.saved && row.liked).length;
    totals.textContent = `${ROWS.length} posts · ${savedCount} saved · ${likedCount} liked · ${bothCount} both`;

    const hashtagCounts = new Map();
    ROWS.forEach((row) => (row.hashtags || "").split(",").filter(Boolean).forEach((tag) => {
      const normalized = tag.trim().toLocaleLowerCase();
      if (normalized) hashtagCounts.set(normalized, (hashtagCounts.get(normalized) || 0) + 1);
    }));
    const hashtagSelect = document.getElementById("hashtag");
    [...hashtagCounts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 50)
      .forEach(([tag]) => {
        const option = document.createElement("option");
        option.value = tag;
        option.textContent = `#${tag}`;
        hashtagSelect.appendChild(option);
      });

    let activeFilter = "all";
    const searchInput = document.getElementById("search");
    const sortSelect = document.getElementById("sort");

    // Render matching records and build each card without inserting HTML strings.
    function renderResults() {
      const query = searchInput.value.trim().toLocaleLowerCase();
      const selectedTag = hashtagSelect.value;
      const filtered = ROWS.filter((row) => {
        const categoryMatches = activeFilter === "all" ||
          (activeFilter === "saved" && row.saved && !row.liked) ||
          (activeFilter === "liked" && row.liked && !row.saved) ||
          (activeFilter === "both" && row.saved && row.liked);
        const searchText = [row.creator, row.caption, row.hashtags, row.url]
          .join(" ").toLocaleLowerCase();
        const rowTags = (row.hashtags || "").split(",").map((tag) => tag.trim().toLocaleLowerCase());
        return categoryMatches && searchText.includes(query) && (!selectedTag || rowTags.includes(selectedTag));
      });

      const sortMode = sortSelect.value;
      filtered.sort((a, b) => {
        if (sortMode === "creator") return a.creator.localeCompare(b.creator, undefined, {sensitivity: "base"});
        const aTime = a.date === "unknown" ? 0 : Date.parse(a.date) || 0;
        const bTime = b.date === "unknown" ? 0 : Date.parse(b.date) || 0;
        return sortMode === "oldest" ? aTime - bTime : bTime - aTime;
      });

      const results = document.getElementById("results");
      results.replaceChildren();
      document.getElementById("result-count").textContent = `Showing ${filtered.length} of ${ROWS.length} posts`;
      if (ROWS.length === 0) {
        const empty = document.createElement("li");
        empty.className = "empty";
        empty.textContent = "No posts to display.";
        results.appendChild(empty);
        return;
      }

      filtered.forEach((row) => {
        const card = document.createElement("li");
        card.className = "post";
        const head = document.createElement("div");
        head.className = "post-head";
        const creator = document.createElement("span");
        creator.className = "creator";
        creator.textContent = row.creator || "unknown";
        head.appendChild(creator);
        const date = document.createElement("span");
        date.className = "date";
        date.textContent = row.date || "unknown";
        head.appendChild(date);
        if (row.saved) {
          const chip = document.createElement("span");
          chip.className = "chip saved";
          chip.textContent = "saved";
          head.appendChild(chip);
        }
        if (row.liked) {
          const chip = document.createElement("span");
          chip.className = "chip liked";
          chip.textContent = "liked";
          head.appendChild(chip);
        }
        card.appendChild(head);

        const caption = document.createElement("p");
        caption.className = "caption";
        caption.textContent = row.caption || (() => {
          try { const parsed = new URL(row.url); return (parsed.host + parsed.pathname).slice(0, 180); }
          catch (_) { return (row.url || "").slice(0, 180); }
        })();
        card.appendChild(caption);

        const tagList = document.createElement("div");
        tagList.className = "hashtags";
        (row.hashtags || "").split(",").filter(Boolean).forEach((tagText) => {
          const tag = document.createElement("span");
          tag.className = "hashtag";
          tag.textContent = `#${tagText.trim()}`;
          tagList.appendChild(tag);
        });
        card.appendChild(tagList);

        const link = document.createElement("a");
        link.className = "post-link";
        link.textContent = row.url || "";
        link.href = row.url || "#";
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        card.appendChild(link);
        results.appendChild(card);
      });
    }

    document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
      activeFilter = tab.dataset.filter;
      document.querySelectorAll(".tab").forEach((item) => {
        const isActive = item === tab;
        item.classList.toggle("active", isActive);
        item.setAttribute("aria-selected", String(isActive));
      });
      renderResults();
    }));
    searchInput.addEventListener("input", renderResults);
    hashtagSelect.addEventListener("change", renderResults);
    sortSelect.addEventListener("change", renderResults);
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
