# -*- coding: utf-8 -*-
"""
把 dist/index.html 转成真正「单文件」版本：
将其中所有 assets/themes/*.webp|png|jpg|... 图片引用内联为 base64 data URI，
poem_b64 已在 index.html 内联、favicon 已是 data:，故输出后无任何外部依赖。
输出：E:/Deployment/WorkBuddy/学习/九漫成长营-单文件版.html
"""
import os, re, base64

DIST = os.path.dirname(os.path.abspath(__file__)) + "/dist"
SRC = os.path.join(DIST, "index.html")
OUT = r"E:/Deployment/WorkBuddy/学习/九漫成长营-单文件版.html"

MIME = {"webp":"image/webp","png":"image/png","jpg":"image/jpeg",
        "jpeg":"image/jpeg","gif":"image/gif","svg":"image/svg+xml"}

html = open(SRC, encoding="utf-8").read()
pat = re.compile(r"(['\"])(assets/themes/[^'\"]+\.(?:webp|png|jpg|jpeg|gif|svg))\1")

seen = {}
def repl(m):
    q, rel = m.group(1), m.group(2)
    if rel in seen:
        return q + seen[rel] + q
    p = os.path.join(DIST, *rel.split("/"))
    ext = rel.rsplit(".", 1)[1].lower()
    try:
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
    except FileNotFoundError:
        print("!! 缺失文件:", p)
        return m.group(0)
    data = "data:%s;base64,%s" % (MIME[ext], b64)
    seen[rel] = data
    return q + data + q

html2 = pat.sub(repl, html)

themes_left = re.findall(r"assets/themes/", html2)
ext_refs = re.findall(r"""<(?:script|link)[^>]*(?:src|href)=["'](?!data:)[^"']+["']""", html2)
print("内联主题图片数:", len(seen))
print("替换后仍含字面量 assets/themes/ (应为0):", len(themes_left))
print("剩余非 data: 外部 <script>/<link> 引用 (应为0):", ext_refs)

open(OUT, "w", encoding="utf-8").write(html2)
print("写出:", OUT, "大小: %.2f MB" % (os.path.getsize(OUT)/1024/1024))
