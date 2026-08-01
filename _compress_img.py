# -*- coding: utf-8 -*-
import os, re
from PIL import Image

ROOT = "dist/assets/themes"
HTML = "dist/index.html"

html = open(HTML, encoding="utf-8").read()

def plan(rel):
    # rel 为 assets/themes/... 形式
    if "角色图" in rel:
        return 384, 80, True   # 角色图：保留透明，较清晰
    return 1100, 62, False     # 背景图：不透明，压得更狠

mapping = {}          # 旧 html 引用 -> 新 html 引用 (.webp)
total_before = 0
total_after = 0
count = 0
fail = []

for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        ext = fn.lower().rsplit(".", 1)[-1]
        if ext not in ("jpg", "jpeg", "png"):
            continue
        old_path = os.path.join(dirpath, fn)
        rel_html = old_path.replace("\\", "/").split("dist/", 1)[-1]  # assets/themes/...
        total_before += os.path.getsize(old_path)
        try:
            img = Image.open(old_path)
            tw, tq, keep_alpha = plan(rel_html)
            if keep_alpha:
                im = img.convert("RGBA")
            else:
                im = img.convert("RGB")
            w, h = im.size
            scale = min(1.0, tw / max(w, h))
            if scale < 1.0:
                im = im.resize((max(1, round(w*scale)), max(1, round(h*scale))), Image.LANCZOS)
            base = fn.rsplit(".", 1)[0]
            new_path = os.path.join(dirpath, base + ".webp")
            im.save(new_path, "WEBP", quality=tq, method=6)
            if new_path != old_path:
                os.remove(old_path)
            total_after += os.path.getsize(new_path)
            mapping[rel_html] = rel_html.rsplit(".", 1)[0] + ".webp"
            count += 1
        except Exception as e:
            fail.append((rel_html, str(e)))

# 批量替换 HTML 引用
for old_rel, new_rel in mapping.items():
    html = html.replace(old_rel, new_rel)

open(HTML, "w", encoding="utf-8").write(html)

print("converted:", count, "fail:", len(fail))
if fail:
    for r, e in fail[:10]:
        print("  FAIL", r, e)
print("before MB: %.2f" % (total_before/1024/1024))
print("after  MB: %.2f" % (total_after/1024/1024))
print("ratio: %.1f%%" % (100*total_after/total_before if total_before else 0))
