# -*- coding: utf-8 -*-
"""
把 dist/index.html 转成真正「单文件」版本：
将其中所有 assets/themes/*.webp|png|jpg|... 图片引用内联为 base64 data URI，
poem_b64 已在 index.html 内联、favicon 已是 data:，故输出后无任何外部依赖。

并在生成阶段对所有图片 data URI 做一次「有损但可控」的再压缩，
使单文件版体积更小（仅影响本脚本产出的 HTML，不改 dist/index.html 本体）：
  - webp 主题图：webp q=58
  - jpeg 背景图：转 webp q=62，宽>900 等比缩到 900
  - png 图标/logo：转 webp q=80（保留透明）
  - 任何图片若压缩后不小于原体积，则保留原样（防越压越大）
输出：E:/Deployment/WorkBuddy/学习/九漫成长营-单文件版.html
"""
import os, re, base64, io
from PIL import Image

DIST = os.path.dirname(os.path.abspath(__file__)) + "/dist"
SRC = os.path.join(DIST, "index.html")
OUT = r"E:/Deployment/WorkBuddy/学习/九漫成长营-单文件版.html"

MIME = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg",
        "jpeg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml"}

# ---- 1) 把 assets/themes 引用内联为 base64（先不压缩，后续统一压缩） ----
html = open(SRC, encoding="utf-8").read()
pat = re.compile(r"(['\"])(assets/themes/[^'\"]+\.(?:webp|png|jpg|jpeg|gif|svg))\1")
seen = {}

def inline(m):
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

html2 = pat.sub(inline, html)

# ---- 2) 全局压缩所有图片 data URI（含 index.html 已内联的 jpeg/png） ----
IMG_RE = re.compile(r"(data:image/(?:webp|jpeg|jpg|png);base64,)([A-Za-z0-9+/=]+)")

def optimize(m):
    prefix, b64 = m.group(1), m.group(2)
    orig_len = len(b64)
    try:
        raw = base64.b64decode(b64)
        if prefix.startswith("data:image/jpeg") or prefix.startswith("data:image/jpg"):
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            q, out_w = 62, 900
        elif prefix.startswith("data:image/png"):
            im = Image.open(io.BytesIO(raw)).convert("RGBA")
            q, out_w = 80, None
        else:  # webp 主题图
            im = Image.open(io.BytesIO(raw)).convert("RGBA")
            q, out_w = 50, 1000
    except Exception as e:
        return m.group(0)
    w, h = im.size
    if out_w and w > out_w:
        r = out_w / w
        im = im.resize((out_w, max(1, int(h * r))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=q, method=4)
    new_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    # 保护：压缩后体积不小于原体积则保留原样
    if len(new_b64) >= orig_len:
        return m.group(0)
    return "data:image/webp;base64," + new_b64

html2 = IMG_RE.sub(optimize, html2)

# ---- 3) 给 body 打单文件版标记，便于 JS 识别并提示持久化方案 ----
html2 = html2.replace('<body>', '<body data-standalone="1">', 1)

# ---- 4) 校验无残留外部引用 ----
themes_left = re.findall(r"assets/themes/", html2)
ext_refs = re.findall(r"""<(?:script|link)[^>]*(?:src|href)=["'](?!data:)[^"']+["']""", html2)
print("内联主题图片数:", len(seen))
print("替换后仍含字面量 assets/themes/ (应为0):", len(themes_left))
print("剩余非 data: 外部 <script>/<link> 引用 (应为0):", ext_refs)

open(OUT, "w", encoding="utf-8").write(html2)
print("写出:", OUT, "大小: %.2f MB" % (os.path.getsize(OUT) / 1024 / 1024))
