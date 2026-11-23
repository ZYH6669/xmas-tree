# -*- coding: utf-8 -*-
"""
批量生成“一人一网址”的圣诞树链接
=================================
1. 编辑下面的 PEOPLE，或者在同目录建一个 people.txt（每行：名字,祝福语,配色）
2. 运行：python make_links.py
3. 它会打印每个链接，并生成一个 links.html（双击就能点开、复制、发人）

配色可选：ice 霜蓝 / gold 暖金 / rose 樱粉 / mint 薄荷 / violet 紫罗兰 / snow 初雪 / aurora 极光
"""

import html
import os
import urllib.parse

# ---------------------------------------------------------------- 改这里
BASE = "https://ZYH6669.github.io/xmas-tree/"

# 名字, 祝福语（可留空）, 配色（可留空 = ice）
PEOPLE = [
    ("小明", "圣诞快乐", "gold"),
    ("小美", "平安喜乐", "rose"),
    ("阿杰", "", "mint"),
]

# 每一行：名字|祝福语|配色（用竖线分隔，祝福语里可以有逗号）；用 # 开头是注释
PEOPLE_FILE = "people.txt"


def load_people():
    if not os.path.exists(PEOPLE_FILE):
        return PEOPLE
    rows = []
    with open(PEOPLE_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.replace("｜", "|")
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
            else:                                   # 兼容用逗号分隔，只切前两刀
                parts = [p.strip() for p in line.split(",", 2)]
            name = parts[0]
            msg = parts[1] if len(parts) > 1 else ""
            pal = parts[2] if len(parts) > 2 else ""
            rows.append((name, msg, pal))
    return rows or PEOPLE


def build_url(name, greet="", pal="", msg=""):
    q = [("to", name)]
    if greet:
        q.append(("greet", greet))
    if msg:
        q.append(("msg", msg))
    if pal:
        q.append(("pal", pal))
    return BASE + "?" + urllib.parse.urlencode(q)


def main():
    people = load_people()
    rows = []
    for name, msg, pal in people:
        url = build_url(name, msg=msg, pal=pal)
        rows.append((name, msg, pal, url))
        print(f"{name:　<6} {pal or 'ice':<7} {url}")

    body = "\n".join(
        f'<li><a href="{html.escape(u)}" target="_blank">{html.escape(n)}</a>'
        f'<span class="pal">{html.escape(p or "ice")}</span>'
        f'<span class="msg">{html.escape(m)}</span>'
        f'<code>{html.escape(u)}</code></li>'
        for n, m, p, u in rows
    )
    page = f"""<!doctype html>
<meta charset="utf-8">
<title>圣诞树链接表</title>
<style>
  body {{ background:#070b14; color:#e8f2ff; font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif; padding:32px; }}
  h1 {{ font-size:20px; font-weight:600; }}
  ul {{ list-style:none; padding:0; }}
  li {{ padding:12px 0; border-bottom:1px solid #1b2740; }}
  a {{ color:#9fe0ff; font-size:17px; text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .pal {{ color:#6f8fae; font-size:12px; margin-left:10px; }}
  .msg {{ color:#a8bdd6; margin-left:10px; }}
  code {{ display:block; margin-top:6px; color:#5f7692; font-size:12px; word-break:break-all; }}
</style>
<h1>🎄 圣诞树链接表（{len(rows)} 人）</h1>
<ul>{body}</ul>
"""
    with open("links.html", "w", encoding="utf-8") as f:
        f.write(page)
    print(f"\n共 {len(rows)} 条，已生成 links.html")


if __name__ == "__main__":
    main()
