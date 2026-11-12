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


# Export all posts into a categorized, searchable offline HTML knowledge library.
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
    * { box-sizing: border-box; }
    body { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; color: #202124; }
    .site-header { position: sticky; top: 0; z-index: 5; margin: -2rem -1rem 1rem; padding: 1.2rem 1rem .8rem; background: rgba(255,255,255,.97); border-bottom: 1px solid #eee; }
    h1 { margin: 0 0 .35rem; }
    .totals { color: #555; margin: 0 0 .75rem; }
    .tabs { display: flex; flex-wrap: wrap; gap: .5rem; }
    .tab { cursor: pointer; border: 1px solid #ddd; border-radius: 999px; padding: .45rem .85rem; background: white; color: #202124; }
    .tab.active { background: #202124; color: white; border-color: #202124; }
    .controls { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr)); gap: .7rem; margin: 1.2rem 0; }
    input[type="search"], select { min-width: 0; width: 100%; padding: .65rem; border: 1px solid #ddd; border-radius: .4rem; background: white; color: #202124; }
    #result-count { color: #555; margin: 1rem 0; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr)); gap: 1rem; padding: 0; list-style: none; }
    .post { display: flex; flex-direction: column; gap: .6rem; min-width: 0; padding: 1rem; background: #fff; border: 1px solid #ddd; border-radius: .5rem; transition: box-shadow .15s ease, border-color .15s ease; }
    .post:hover { box-shadow: 0 4px 16px rgba(0,0,0,.08); border-color: #aaa; }
    .post-title { margin: 0; font-size: 1.05rem; line-height: 1.3; font-weight: 700; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; line-clamp: 2; overflow: hidden; overflow-wrap: anywhere; }
    .meta { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem; color: #555; font-size: .88rem; }
    .badge, .category-chip { display: inline-block; border-radius: 999px; padding: .18rem .55rem; font-size: .8rem; }
    .badge { background: #eee; }
    .badge.saved { background: #e7f2ff; }
    .badge.liked { background: #ffe8ec; }
    .description { margin: 0; color: #444; font-size: .92rem; line-height: 1.45; white-space: pre-wrap; overflow-wrap: anywhere; display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 4; line-clamp: 4; overflow: hidden; }
    .description.expanded { display: block; }
    .read-more { align-self: flex-start; padding: 0; border: 0; background: none; color: #315f9b; cursor: pointer; font: inherit; font-size: .88rem; }
    .hashtags { display: flex; flex-wrap: wrap; gap: .35rem; }
    .hashtag { border-radius: 999px; padding: .18rem .55rem; background: #f1f1f1; color: #555; font-size: .8rem; }
    .card-footer { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: .5rem; margin-top: auto; padding-top: .2rem; }
    .category-chip { color: #333; }
    .category-ai { background: #e3f0ff; } .category-python { background: #fff4e0; }
    .category-linux { background: #e8f5e9; } .category-security { background: #ffebee; }
    .category-web { background: #f3e5f5; } .category-business { background: #fce4ec; }
    .category-design { background: #e0f7fa; } .category-video { background: #f1f8e9; }
    .category-opensource { background: #f5f5f5; } .category-maroc { background: #fff8e1; }
    .category-other { background: #eeeeee; }
    .post-link { text-align: right; overflow-wrap: anywhere; font-size: .9rem; }
    .group-section { margin: 1.6rem 0 2rem; }
    .group-heading { margin: 0 0 .8rem; padding-bottom: .45rem; border-bottom: 1px solid #eee; color: #555; font-size: 1.1rem; font-weight: 600; }
    .empty { color: #555; padding: 1.5rem 0; list-style: none; }
  </style>
</head>
<body>
  <header class="site-header">
    <h1>Instagram Knowledge Library</h1>
    <p id="totals" class="totals"></p>
    <div class="tabs" role="tablist" aria-label="Post type">
      <button class="tab active" type="button" data-filter="all" aria-selected="true">All</button>
      <button class="tab" type="button" data-filter="saved" aria-selected="false">Saved</button>
      <button class="tab" type="button" data-filter="liked" aria-selected="false">Liked</button>
      <button class="tab" type="button" data-filter="both" aria-selected="false">Both</button>
    </div>
  </header>
  <section class="controls" aria-label="Search, category, hashtag, sort and grouping">
    <input id="search" type="search" placeholder="Search creator, title, caption, hashtags or URL" autocomplete="off">
    <select id="category" aria-label="Filter by category"><option value="">All categories</option></select>
    <select id="hashtag" aria-label="Filter by hashtag"><option value="">All hashtags</option></select>
    <select id="sort" aria-label="Sort posts">
      <option value="newest">Newest</option>
      <option value="oldest">Oldest</option>
      <option value="creator">Creator A-Z</option>
    </select>
    <select id="group" aria-label="Group posts">
      <option value="none">Group by: None</option>
      <option value="category">Group by: By category</option>
      <option value="type">Group by: By type</option>
    </select>
  </section>
  <p id="result-count" aria-live="polite"></p>
  <div id="results"></div>
  <script>
    const ROWS = __ROWS__;
    const CATEGORIES = ["AI / LLM", "Python", "Linux / DevOps", "Security", "Web Dev", "Business", "Design", "Video / Content", "Open Source", "Maroc", "Other"];
    const CATEGORY_KEYWORDS = {
      "AI / LLM": ["ai", "ia", "gpt", "chatgpt", "claude", "llm", "openai", "artificialintelligence", "machinelearning", "deeplearning", "prompt"],
      "Python": ["python", "django", "flask", "fastapi", "pandas", "numpy"],
      "Linux / DevOps": ["linux", "ubuntu", "debian", "docker", "kubernetes", "k8s", "bash", "shell", "devops", "ansible", "nginx"],
      "Security": ["security", "cybersecurity", "hacker", "hacking", "hack", "ctf", "pentest", "malware", "infosec"],
      "Web Dev": ["javascript", "js", "typescript", "react", "vue", "node", "html", "css", "frontend", "backend", "api"],
      "Business": ["business", "entrepreneur", "startup", "marketing", "sales", "ecommerce", "money"],
      "Design": ["design", "ui", "ux", "figma", "photoshop", "creative"],
      "Video / Content": ["video", "youtube", "reel", "reels", "content", "tiktok", "creator"],
      "Open Source": ["opensource", "github", "gitlab", "foss", "free"],
      "Maroc": ["maroc", "morocco", "marocaine", "rabat", "casablanca", "marrakech"]
    };
    const CATEGORY_CLASSES = {
      "AI / LLM": "category-ai", "Python": "category-python", "Linux / DevOps": "category-linux",
      "Security": "category-security", "Web Dev": "category-web", "Business": "category-business",
      "Design": "category-design", "Video / Content": "category-video", "Open Source": "category-opensource",
      "Maroc": "category-maroc", "Other": "category-other"
    };

    // Classify a row from keyword matches in its caption and hashtags.
    function classifyRow(row) {
      const tokens = (String(row.caption || "") + " " + String(row.hashtags || ""))
        .toLocaleLowerCase().match(/[\\p{L}\\p{N}]+/gu) || [];
      const tokenSet = new Set(tokens);
      let bestCategory = "Other";
      let bestScore = 0;
      CATEGORIES.slice(0, -1).forEach((category) => {
        const score = CATEGORY_KEYWORDS[category].reduce((count, keyword) => count + (tokenSet.has(keyword) ? 1 : 0), 0);
        if (score > bestScore) { bestCategory = category; bestScore = score; }
      });
      row.category = bestCategory;
      const firstLine = String(row.caption || "").split(/\\r?\\n/, 1)[0]
        .replace(/#\\w+/g, " ").replace(/\\s+/g, " ").trim();
      row.title = firstLine
        ? (firstLine.length > 90 ? firstLine.slice(0, 89).trimEnd() + "…" : firstLine)
        : `@${row.creator || "unknown"} — ${row.date || "unknown"}`;
      if (row.caption) {
        row.description = row.caption;
      } else {
        try { row.description = new URL(row.url).hostname; }
        catch (_) { row.description = row.url || ""; }
      }
      return row;
    }
    ROWS.forEach(classifyRow);

    const savedCount = ROWS.filter((row) => row.saved).length;
    const likedCount = ROWS.filter((row) => row.liked).length;
    const bothCount = ROWS.filter((row) => row.saved && row.liked).length;
    const representedCategories = new Set(ROWS.map((row) => row.category));
    document.getElementById("totals").textContent = `${ROWS.length} posts · ${savedCount} saved · ${likedCount} liked · ${bothCount} both · ${representedCategories.size} categories`;

    const categorySelect = document.getElementById("category");
    CATEGORIES.forEach((category) => {
      const option = document.createElement("option");
      option.value = category;
      option.textContent = category;
      categorySelect.appendChild(option);
    });
    const hashtagCounts = new Map();
    ROWS.forEach((row) => (row.hashtags || "").split(",").filter(Boolean).forEach((tag) => {
      const normalized = tag.trim().toLocaleLowerCase();
      if (normalized) hashtagCounts.set(normalized, (hashtagCounts.get(normalized) || 0) + 1);
    }));
    const hashtagSelect = document.getElementById("hashtag");
    [...hashtagCounts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 50).forEach(([tag]) => {
      const option = document.createElement("option");
      option.value = tag;
      option.textContent = `#${tag}`;
      hashtagSelect.appendChild(option);
    });

    let activeFilter = "all";
    const searchInput = document.getElementById("search");
    const sortSelect = document.getElementById("sort");
    const groupSelect = document.getElementById("group");

    // Sort a copy of the filtered records using the selected order.
    function sortRows(rows) {
      const sorted = rows.slice();
      if (sortSelect.value === "creator") {
        sorted.sort((a, b) => (a.creator || "").localeCompare(b.creator || "", undefined, {sensitivity: "base"}));
      } else {
        sorted.sort((a, b) => {
          const aTime = a.date === "unknown" ? 0 : Date.parse(a.date) || 0;
          const bTime = b.date === "unknown" ? 0 : Date.parse(b.date) || 0;
          return sortSelect.value === "oldest" ? aTime - bTime : bTime - aTime;
        });
      }
      return sorted;
    }

    // Build a safe rich card using DOM nodes and textContent for every record field.
    function createCard(row) {
      const card = document.createElement("article");
      card.className = "post";
      const title = document.createElement("h2");
      title.className = "post-title";
      title.textContent = row.title;
      card.appendChild(title);

      const meta = document.createElement("div");
      meta.className = "meta";
      const creator = document.createElement("span");
      creator.textContent = `@${row.creator || "unknown"}`;
      meta.appendChild(creator);
      const separator = document.createElement("span");
      separator.textContent = "·";
      meta.appendChild(separator);
      const date = document.createElement("span");
      date.textContent = row.date || "unknown";
      meta.appendChild(date);
      if (row.saved) {
        const badge = document.createElement("span"); badge.className = "badge saved"; badge.textContent = "saved"; meta.appendChild(badge);
      }
      if (row.liked) {
        const badge = document.createElement("span"); badge.className = "badge liked"; badge.textContent = "liked"; meta.appendChild(badge);
      }
      card.appendChild(meta);

      const description = document.createElement("p");
      description.className = "description";
      description.textContent = row.description;
      card.appendChild(description);
      const readMore = document.createElement("button");
      readMore.className = "read-more";
      readMore.type = "button";
      readMore.textContent = "Read more";
      readMore.addEventListener("click", () => {
        const expanded = description.classList.toggle("expanded");
        readMore.textContent = expanded ? "Show less" : "Read more";
      });
      card.appendChild(readMore);

      const hashtags = document.createElement("div");
      hashtags.className = "hashtags";
      const tagList = (row.hashtags || "").split(",").map((tag) => tag.trim()).filter(Boolean);
      tagList.slice(0, 6).forEach((tagText) => {
        const tag = document.createElement("span"); tag.className = "hashtag"; tag.textContent = `#${tagText}`; hashtags.appendChild(tag);
      });
      if (tagList.length > 6) {
        const more = document.createElement("span"); more.className = "hashtag"; more.textContent = `+${tagList.length - 6} more`; hashtags.appendChild(more);
      }
      card.appendChild(hashtags);

      const footer = document.createElement("div");
      footer.className = "card-footer";
      const category = document.createElement("span");
      category.className = `category-chip ${CATEGORY_CLASSES[row.category] || CATEGORY_CLASSES.Other}`;
      category.textContent = row.category;
      footer.appendChild(category);
      const link = document.createElement("a");
      link.className = "post-link";
      link.textContent = "Open on Instagram →";
      link.href = row.url || "#";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      footer.appendChild(link);
      card.appendChild(footer);
      return card;
    }

    // Render current filtered records as one grid or as count-sorted type/category groups.
    function renderResults() {
      const query = searchInput.value.trim().toLocaleLowerCase();
      const selectedCategory = categorySelect.value;
      const selectedTag = hashtagSelect.value;
      const filtered = ROWS.filter((row) => {
        const typeMatches = activeFilter === "all" ||
          (activeFilter === "saved" && row.saved && !row.liked) ||
          (activeFilter === "liked" && row.liked && !row.saved) ||
          (activeFilter === "both" && row.saved && row.liked);
        const searchText = [row.creator, row.title, row.caption, row.hashtags, row.url].join(" ").toLocaleLowerCase();
        const rowTags = (row.hashtags || "").split(",").map((tag) => tag.trim().toLocaleLowerCase());
        return typeMatches && (!selectedCategory || row.category === selectedCategory) &&
          searchText.includes(query) && (!selectedTag || rowTags.includes(selectedTag));
      });
      const results = document.getElementById("results");
      results.replaceChildren();
      document.getElementById("result-count").textContent = `Showing ${filtered.length} of ${ROWS.length} posts`;
      if (ROWS.length === 0) {
        const empty = document.createElement("p"); empty.className = "empty"; empty.textContent = "No posts to display."; results.appendChild(empty); return;
      }
      const sorted = sortRows(filtered);
      const mode = groupSelect.value;
      if (mode === "none") {
        const grid = document.createElement("div"); grid.className = "cards";
        sorted.forEach((row) => grid.appendChild(createCard(row)));
        results.appendChild(grid);
        return;
      }
      const groups = new Map();
      sorted.forEach((row) => {
        let key;
        if (mode === "category") key = row.category;
        else if (row.saved && row.liked) key = "Both";
        else if (row.saved) key = "Saved only";
        else if (row.liked) key = "Liked only";
        else key = "Neither";
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(row);
      });
      let groupEntries = [...groups.entries()];
      if (mode === "category") {
        groupEntries.sort((a, b) => {
          if (a[0] === "Other") return 1;
          if (b[0] === "Other") return -1;
          return b[1].length - a[1].length || CATEGORIES.indexOf(a[0]) - CATEGORIES.indexOf(b[0]);
        });
      } else {
        const typeOrder = ["Saved only", "Liked only", "Both", "Neither"];
        groupEntries.sort((a, b) => typeOrder.indexOf(a[0]) - typeOrder.indexOf(b[0]));
      }
      groupEntries.forEach(([name, groupRows]) => {
        const section = document.createElement("section"); section.className = "group-section";
        const heading = document.createElement("h2"); heading.className = "group-heading"; heading.textContent = `${name} · ${groupRows.length} posts`; section.appendChild(heading);
        const grid = document.createElement("div"); grid.className = "cards";
        groupRows.forEach((row) => grid.appendChild(createCard(row)));
        section.appendChild(grid); results.appendChild(section);
      });
    }

    document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
      activeFilter = tab.dataset.filter;
      document.querySelectorAll(".tab").forEach((item) => {
        const isActive = item === tab; item.classList.toggle("active", isActive); item.setAttribute("aria-selected", String(isActive));
      });
      renderResults();
    }));
    searchInput.addEventListener("input", renderResults);
    categorySelect.addEventListener("change", renderResults);
    hashtagSelect.addEventListener("change", renderResults);
    sortSelect.addEventListener("change", renderResults);
    groupSelect.addEventListener("change", renderResults);
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
