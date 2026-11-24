import html
import json
import os
import re
import urllib.request

NOVEL_URL = "https://satorri12.github.io/nags-novel/"
OUT_DIR = "nags-site"
CH_DIR = os.path.join(OUT_DIR, "chapters")
BUNDLE_DIR = os.path.join(OUT_DIR, "bundles")
os.makedirs(CH_DIR, exist_ok=True)
os.makedirs(BUNDLE_DIR, exist_ok=True)

raw_html = urllib.request.urlopen(NOVEL_URL).read().decode("utf-8")
start = raw_html.find("[", raw_html.find("/*_DATA_START_*/"))
chapters, _ = json.JSONDecoder().raw_decode(raw_html, start)

used_slugs = set()
BUNDLE_SIZE = 5


def parse_info(title: str, idx: int):
    m_part = re.search(r"\b(\d+)\b.*?\bpart\s*(\d+)\b", title, re.I)
    m_num = re.search(r"\b(\d+)\b", title)
    ch_num = int(m_num.group(1)) if m_num else None

    if m_part:
        slug = f"{m_part.group(1)}-part-{m_part.group(2)}"
    elif m_num:
        slug = m_num.group(1)
    else:
        slug = f"extra-{idx + 1}"

    base = slug
    counter = 2
    while slug in used_slugs:
        slug = f"{base}-{counter}"
        counter += 1
    used_slugs.add(slug)

    if ch_num is not None and ch_num >= 1:
        b_start = ((ch_num - 1) // BUNDLE_SIZE) * BUNDLE_SIZE + 1
        bundle_name = f"{b_start}-{b_start + BUNDLE_SIZE - 1}"
    else:
        bundle_name = "extras"

    return slug, bundle_name


items = []
bundles_map = {}

for i, ch in enumerate(chapters):
    title = str(ch.get("title") or f"Chapter {i + 1}").strip()
    content = str(ch.get("content") or "").strip()
    slug, b_name = parse_info(title, i)
    item = {
        "title": title,
        "content": content,
        "file": f"{slug}.html",
        "bundle": b_name,
        "bundle_file": f"{b_name}.html",
    }
    items.append(item)
    bundles_map.setdefault(b_name, []).append(item)

toc_items = []
for i, item in enumerate(items):
    prev_link = f'<a href="{items[i-1]["file"]}">&larr; Trước</a>' if i > 0 else ""
    next_link = f'<a href="{items[i+1]["file"]}">Sau &rarr;</a>' if i < len(items) - 1 else ""
    b_link = f'<a href="../bundles/{item["bundle_file"]}">Cụm {item["bundle"]}</a>'

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(item["title"])}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 780px; margin: 40px auto; padding: 0 16px; line-height: 1.7; background: #18181b; color: #e4e4e7; }}
    nav {{ display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; margin: 24px 0; padding: 12px 0; border-top: 1px solid #3f3f46; border-bottom: 1px solid #3f3f46; }}
    a {{ color: #60a5fa; text-decoration: none; }}
    article {{ white-space: pre-wrap; font-size: 17px; }}
  </style>
</head>
<body>
  <nav><a href="../index.html">Mục lục</a> {b_link} {prev_link} {next_link}</nav>
  <h1>{html.escape(item["title"])}</h1>
  <article>{html.escape(item["content"])}</article>
  <nav><a href="../index.html">Mục lục</a> {b_link} {prev_link} {next_link}</nav>
</body>
</html>"""
    with open(os.path.join(CH_DIR, item["file"]), "w", encoding="utf-8") as f:
        f.write(page_html)

    toc_items.append(
        f'<li><a href="chapters/{item["file"]}">{html.escape(item["title"])}</a> '
        f'<a class="btag" href="bundles/{item["bundle_file"]}">[Cụm {item["bundle"]}]</a></li>'
    )

bundle_keys = list(bundles_map.keys())
bundle_links = []
for b_i, b_name in enumerate(bundle_keys):
    chunk = bundles_map[b_name]
    b_file = f"{b_name}.html"
    prev_b = f'<a href="{bundle_keys[b_i-1]}.html">&larr; Cụm trước</a>' if b_i > 0 else ""
    next_b = f'<a href="{bundle_keys[b_i+1]}.html">Cụm sau &rarr;</a>' if b_i < len(bundle_keys) - 1 else ""

    sections = [
        f"<section><h2>{html.escape(ch['title'])}</h2><article>{html.escape(ch['content'])}</article></section>"
        for ch in chunk
    ]
    bundle_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NAGS Cụm {html.escape(b_name)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 780px; margin: 40px auto; padding: 0 16px; line-height: 1.7; background: #18181b; color: #e4e4e7; }}
    nav {{ display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; margin: 20px 0; padding: 12px 0; border-top: 1px solid #3f3f46; border-bottom: 1px solid #3f3f46; }}
    section {{ margin-bottom: 48px; padding-bottom: 32px; border-bottom: 2px solid #3f3f46; }}
    article {{ white-space: pre-wrap; font-size: 17px; }}
    a {{ color: #60a5fa; text-decoration: none; }}
  </style>
</head>
<body>
  <nav><a href="../index.html">Mục lục</a> {prev_b} {next_b}</nav>
  {"".join(sections)}
  <nav><a href="../index.html">Mục lục</a> {prev_b} {next_b}</nav>
</body>
</html>"""
    with open(os.path.join(BUNDLE_DIR, b_file), "w", encoding="utf-8") as f:
        f.write(bundle_html)
    bundle_links.append(f'<a class="chip" href="bundles/{b_file}">{b_name}</a>')

index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NAGS - Danh sách Chapter</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto; padding: 0 16px; background: #18181b; color: #e4e4e7; }}
    input {{ width: 100%; padding: 12px; font-size: 16px; margin-bottom: 16px; border-radius: 8px; border: 1px solid #3f3f46; background: #27272a; color: #fff; box-sizing: border-box; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px; }}
    .chip {{ background: #27272a; border: 1px solid #3f3f46; padding: 6px 10px; border-radius: 6px; font-size: 13px; color: #93c5fd; text-decoration: none; }}
    ul {{ list-style: none; padding: 0; line-height: 2.2; }}
    a {{ color: #60a5fa; text-decoration: none; }}
    .btag {{ margin-left: 8px; font-size: 13px; color: #a1a1aa; background: #27272a; padding: 2px 8px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Necromancer Academy and the Genius Summoner ({len(items)} Chapters)</h1>
  <input type="text" id="q" placeholder="Gõ số chương cần tìm (ví dụ: 623)..." oninput="filterList()">
  <ul id="list">{"".join(toc_items)}</ul>
  <h3>Tất cả các cụm 5 chương:</h3>
  <div class="chips">{"".join(bundle_links)}</div>
  <script>
    function filterList() {{
      const q = document.getElementById('q').value.toLowerCase();
      document.querySelectorAll('#list li').forEach(li => {{
        li.style.display = li.textContent.toLowerCase().includes(q) ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>"""

with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)
