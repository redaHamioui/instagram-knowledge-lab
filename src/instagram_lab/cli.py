"""CLI: `uv run python main.py <command>`."""
import json
import sys
from .config import RAW_DIR, KNOWLEDGE_DIR, DEFAULT_MODE, ensure_dirs
from .importer import import_export
from .database import (
    upsert_posts,
    all_posts,
    get_stats,
    export_rows_as_dicts,
)
from .markdown import write_post_row
from .search import print_results


def cmd_import(mode: str = DEFAULT_MODE) -> None:
    ensure_dirs()
    zips = sorted(RAW_DIR.glob("*.zip"))
    if not zips:
        print(f"No ZIP found in {RAW_DIR}")
        print("Put your Instagram export ZIP there first.")
        return

    print(f"  Mode: {mode}")
    for z in zips:
        print(f"Importing: {z.name}")
        posts = import_export(z, mode=mode)
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
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Instagram Knowledge Library</title>
<style>
:root{color-scheme:light;font-family:system-ui,sans-serif}*{box-sizing:border-box}body{max-width:1200px;margin:2rem auto;padding:0 1rem;color:#202124}.site-header{position:sticky;top:0;z-index:5;margin:-2rem -1rem 1rem;padding:1.2rem 1rem .8rem;background:rgba(255,255,255,.97);border-bottom:1px solid #eee}h1{margin:0 0 .35rem}.totals{color:#555;margin:0 0 .75rem}.tabs{display:flex;flex-wrap:wrap;gap:.5rem}.tab{cursor:pointer;border:1px solid #ddd;border-radius:999px;padding:.45rem .85rem;background:white;color:#202124}.tab.active{background:#202124;color:white;border-color:#202124}.controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(220px,100%),1fr));gap:.7rem;margin:1.2rem 0}input,select{min-width:0;width:100%;padding:.65rem;border:1px solid #ddd;border-radius:.4rem;background:white;color:#202124}#result-count{color:#555;margin:1rem 0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr));gap:1rem;padding:0;list-style:none}.post{display:flex;flex-direction:column;gap:.6rem;min-width:0;padding:1rem;background:#fff;border:1px solid #ddd;border-radius:.5rem}.post:hover{box-shadow:0 4px 16px #0001;border-color:#aaa}.post-title{margin:0;font-size:1.05rem;line-height:1.3}.meta{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;color:#555;font-size:.88rem}.badge,.category-chip,.hashtag{display:inline-block;border-radius:999px;padding:.18rem .55rem;font-size:.8rem}.badge{background:#eee}.badge.saved{background:#e7f2ff}.badge.liked{background:#ffe8ec}.description{margin:0;color:#444;font-size:.92rem;line-height:1.45;white-space:pre-wrap;overflow-wrap:anywhere;max-height:6em;overflow:hidden}.description.expanded{max-height:none}.read-more{align-self:flex-start;border:0;background:none;color:#315f9b;cursor:pointer;font:inherit}.hashtags{display:flex;flex-wrap:wrap;gap:.35rem}.hashtag{background:#f1f1f1;color:#555}.card-footer{display:flex;align-items:center;justify-content:space-between;gap:.5rem;margin-top:auto}.category-chip{background:#e3f0ff}.post-link{overflow-wrap:anywhere;font-size:.9rem}.group-section{margin:1.6rem 0 2rem}.group-heading{border-bottom:1px solid #eee;color:#555;font-size:1.1rem}.empty{color:#555;padding:1.5rem 0}
</style>
</head>
<body><header class="site-header"><h1>Instagram Knowledge Library</h1><p id="totals" class="totals"></p><div class="tabs" role="tablist" aria-label="Post type"><button class="tab active" data-filter="all">All</button><button class="tab" data-filter="saved">Saved</button><button class="tab" data-filter="liked">Liked</button><button class="tab" data-filter="both">Both</button></div></header>
<section class="controls" aria-label="Search, category, hashtag, sort and grouping"><input id="search" type="search" placeholder="Search creator, title, caption, hashtags or URL" autocomplete="off"><select id="category"><option value="">All categories</option></select><select id="hashtag"><option value="">All hashtags</option></select><select id="sort"><option value="newest">Newest</option><option value="oldest">Oldest</option><option value="creator">Creator A-Z</option></select><select id="group"><option value="none">Group by: None</option><option value="category">Group by: By category</option><option value="type">Group by: By type</option></select></section><p id="result-count" aria-live="polite"></p><div id="results"></div>
<script>
const ROWS=__ROWS__;
const CATEGORIES=["AI / LLM","Python","Linux / DevOps","Security","Web Dev","Business","Design","Video / Content","Open Source","Maroc","Other"];
const CATEGORY_KEYWORDS={"AI / LLM":["ai","ia","gpt","chatgpt","claude","llm","openai","machinelearning","deeplearning","prompt"],Python:["python","django","flask","fastapi","pandas","numpy"],"Linux / DevOps":["linux","ubuntu","debian","docker","kubernetes","k8s","bash","shell","devops","ansible","nginx"],Security:["security","cybersecurity","hacker","hacking","hack","ctf","pentest","malware","infosec"],"Web Dev":["javascript","js","typescript","react","vue","node","html","css","frontend","backend","api"],Business:["business","entrepreneur","startup","marketing","sales","ecommerce","money"],Design:["design","ui","ux","figma","photoshop","creative"],"Video / Content":["video","youtube","reel","reels","content","tiktok","creator"],"Open Source":["opensource","github","gitlab","foss","free"],Maroc:["maroc","morocco","marocaine","rabat","casablanca","marrakech"]};
function classifyRow(row){const words=(String(row.caption||"")+" "+String(row.hashtags||"")).toLowerCase().match(/[\\p{L}\\p{N}]+/gu)||[];let best="Other",score=0;CATEGORIES.slice(0,-1).forEach(c=>{const n=CATEGORY_KEYWORDS[c].filter(w=>words.includes(w)).length;if(n>score){best=c;score=n}});row.category=best;const first=String(row.caption||"").split(/\\r?\\n/,1)[0].replace(/#\\w+/g," ").replace(/\\s+/g," ").trim();row.title=first?(first.length>90?first.slice(0,89).trimEnd()+"…":first):`@${row.creator||"unknown"} — ${row.date||"unknown"}`;row.description=row.caption||row.url||"";return row}ROWS.forEach(classifyRow);
const savedCount=ROWS.filter(r=>r.saved).length,likedCount=ROWS.filter(r=>r.liked).length,bothCount=ROWS.filter(r=>r.saved&&r.liked).length,ownCount=ROWS.filter(r=>String(r.url||"").startsWith("instagram://own/")).length,representedCategories=new Set(ROWS.map(r=>r.category));
document.getElementById("totals").textContent=`${ROWS.length} posts · ${ownCount} own · ${savedCount} saved · ${likedCount} liked · ${bothCount} both · ${representedCategories.size} categories`;
const category=document.getElementById("category"),hashtag=document.getElementById("hashtag");CATEGORIES.forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;category.appendChild(o)});const tagCounts=new Map();ROWS.forEach(r=>(r.hashtags||"").split(",").filter(Boolean).forEach(t=>tagCounts.set(t.toLowerCase(),(tagCounts.get(t.toLowerCase())||0)+1)));[...tagCounts].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).slice(0,50).forEach(([t])=>{const o=document.createElement("option");o.value=t;o.textContent="#"+t;hashtag.appendChild(o)});
let active="all";const search=document.getElementById("search"),sort=document.getElementById("sort"),group=document.getElementById("group");
function card(r){const a=document.createElement("article");a.className="post";const h=document.createElement("h2");h.className="post-title";h.textContent=r.title;a.appendChild(h);const m=document.createElement("div");m.className="meta";m.textContent=`@${r.creator||"unknown"} · ${r.date||"unknown"}`;if(r.saved){const b=document.createElement("span");b.className="badge saved";b.textContent="saved";m.appendChild(b)}if(r.liked){const b=document.createElement("span");b.className="badge liked";b.textContent="liked";m.appendChild(b)}a.appendChild(m);const d=document.createElement("p");d.className="description";d.textContent=r.description;a.appendChild(d);const more=document.createElement("button");more.className="read-more";more.textContent="Read more";more.onclick=()=>{d.classList.toggle("expanded");more.textContent=d.classList.contains("expanded")?"Show less":"Read more"};a.appendChild(more);const tags=document.createElement("div");tags.className="hashtags";(r.hashtags||"").split(",").filter(Boolean).slice(0,6).forEach(t=>{const s=document.createElement("span");s.className="hashtag";s.textContent="#"+t;tags.appendChild(s)});a.appendChild(tags);const f=document.createElement("div");f.className="card-footer";const c=document.createElement("span");c.className="category-chip";c.textContent=r.category;f.appendChild(c);const link=document.createElement("a");link.className="post-link";link.textContent="Open on Instagram →";link.href=r.url||"#";link.target="_blank";link.rel="noopener noreferrer";f.appendChild(link);a.appendChild(f);return a}
function render(){const q=search.value.trim().toLowerCase(),filtered=ROWS.filter(r=>{const type=active==="all"||(active==="saved"&&r.saved&&!r.liked)||(active==="liked"&&r.liked&&!r.saved)||(active==="both"&&r.saved&&r.liked);return type&&(!category.value||r.category===category.value)&&(!hashtag.value||(r.hashtags||"").toLowerCase().split(",").includes(hashtag.value))&&[r.creator,r.title,r.caption,r.hashtags,r.url].join(" ").toLowerCase().includes(q)});if(sort.value==="creator")filtered.sort((a,b)=>(a.creator||"").localeCompare(b.creator||"",undefined,{sensitivity:"base"}));else filtered.sort((a,b)=>{const x=Date.parse(a.date)||0,y=Date.parse(b.date)||0;return sort.value==="oldest"?x-y:y-x});const out=document.getElementById("results");out.replaceChildren();document.getElementById("result-count").textContent=`Showing ${filtered.length} of ${ROWS.length} posts`;if(!filtered.length){const p=document.createElement("p");p.className="empty";p.textContent="No posts to display.";out.appendChild(p);return}if(group.value==="none"){const grid=document.createElement("div");grid.className="cards";filtered.forEach(r=>grid.appendChild(card(r)));out.appendChild(grid);return}const groups=new Map();filtered.forEach(r=>{const key=group.value==="category"?r.category:(r.saved&&r.liked?"Both":r.saved?"Saved only":r.liked?"Liked only":"Neither");if(!groups.has(key))groups.set(key,[]);groups.get(key).push(r)});[...groups].forEach(([name,items])=>{const section=document.createElement("section");section.className="group-section";const h=document.createElement("h2");h.className="group-heading";h.textContent=`${name} · ${items.length} posts`;section.appendChild(h);const grid=document.createElement("div");grid.className="cards";items.forEach(r=>grid.appendChild(card(r)));section.appendChild(grid);out.appendChild(section)})}
document.querySelectorAll(".tab").forEach(t=>t.addEventListener("click",()=>{active=t.dataset.filter;document.querySelectorAll(".tab").forEach(x=>x.classList.toggle("active",x===t));render()}));[search,category,hashtag,sort,group].forEach(x=>x.addEventListener(x===search?"input":"change",render));render();
</script></body></html>""".replace("__ROWS__", embedded_rows)
    output_path.write_text(html, encoding="utf-8")
    print(f"HTML library written to {output_path}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  uv run python main.py import [--mode=own|all]")
        print("  uv run python main.py list")
        print("  uv run python main.py search <keyword>")
        print("  uv run python main.py stats")
        print("  uv run python main.py export-html")
        return

    command = sys.argv[1]
    if command == "import":
        mode = "all" if "--mode=all" in sys.argv else DEFAULT_MODE
        cmd_import(mode=mode)
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
