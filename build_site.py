import html
import json
import os
import re
import urllib.request

NOVEL_URL = "https://satorri12.github.io/nags-novel/"
OUT_DIR = "nags-site"
CH_DIR = os.path.join(OUT_DIR, "chapters")
os.makedirs(CH_DIR, exist_ok=True)

print("1. Đang tải dữ liệu...")
raw_html = urllib.request.urlopen(NOVEL_URL).read().decode("utf-8")
start = raw_html.find("[", raw_html.find("/*_DATA_START_*/"))
chapters, _ = json.JSONDecoder().raw_decode(raw_html, start)

used_slugs = set()
toc_items = []


def make_slug(title: str, idx: int) -> str:
    m_part = re.search(r"\b(\d+)\b.*?\bpart\s*(\d+)\b", title, re.I)
    m_num = re.search(r"\b(\d+)\b", title)
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
    return slug


items = []
for i, ch in enumerate(chapters):
    title = str(ch.get("title") or f"Chapter {i + 1}").strip()
    content = str(ch.get("content") or "").strip()
    slug = make_slug(title, i)
    items.append({"title": title, "content": content, "file": f"{slug}.html"})

for i, item in enumerate(items):
    prev_link = f'<a href="{items[i-1]["file"]}">&larr; Trước</a>' if i > 0 else ""
    next_link = f'<a href="{items[i+1]["file"]}">Sau &rarr;</a>' if i < len(items) - 1 else ""

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(item["title"])}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 780px; margin: 40px auto; padding: 0 16px; line-height: 1.7; background: #18181b; color: #e4e4e7; }}
    nav {{ display: flex; justify-content: space-between; margin: 24px 0; padding: 12px 0; border-top: 1px solid #3f3f46; border-bottom: 1px solid #3f3f46; }}
    a {{ color: #60a5fa; text-decoration: none; }}
    article {{ white-space: pre-wrap; font-size: 17px; }}
  </style>
</head>
<body>
  <nav><a href="../index.html">Mục lục</a> {prev_link} {next_link}</nav>
  <h1>{html.escape(item["title"])}</h1>
  <article>{html.escape(item["content"])}</article>
  <nav><a href="../index.html">Mục lục</a> {prev_link} {next_link}</nav>
</body>
</html>"""

    with open(os.path.join(CH_DIR, item["file"]), "w", encoding="utf-8") as f:
        f.write(page_html)

    toc_items.append(
        f'<li><a href="chapters/{item["file"]}">{html.escape(item["title"])}</a></li>'
    )

index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NAGS - Danh sách Chapter</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto; padding: 0 16px; background: #18181b; color: #e4e4e7; }}
    input {{ width: 100%; padding: 12px; font-size: 16px; margin-bottom: 20px; border-radius: 8px; border: 1px solid #3f3f46; background: #27272a; color: #fff; box-sizing: border-box; }}
    ul {{ list-style: none; padding: 0; line-height: 2; }}
    a {{ color: #60a5fa; text-decoration: none; }}
  </style>
</head>
<body>
  <h1>Necromancer Academy and the Genius Summoner ({len(items)} Chapters)</h1>
  <input type="text" id="q" placeholder="Tìm theo số hoặc tên chapter (ví dụ: 406)..." oninput="filterList()">
  <ul id="list">
    {"".join(toc_items)}
  </ul>
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
