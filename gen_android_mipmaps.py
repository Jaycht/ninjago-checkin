#!/usr/bin/env python3
"""一次性生成 Android mipmap 图标，提交进仓库。

CI 的 ci_patch_android.py 只做纯文件拷贝（stdlib shutil），不依赖 Pillow，
从根本上避免 'No module named PIL' 导致构建失败。

图标策略（v6.19.2 起）：直接使用用户提供的原始 game.png 作为标准启动图标，
不拼背景色、不做自适应合成——所见即用户原图。同时 CI 补丁会删除安卓自适应
anydpi 目录，强制系统使用标准 mipmap（= 原始 game.png）。

源图：src-tauri/icons/game.png（192 方形、带透明通道）。
"""
import pathlib
import shutil
from PIL import Image

ROOT = pathlib.Path('src-tauri/icons')
SRC = ROOT / 'game.png'
OUT = ROOT / 'mipmaps'

im = Image.open(SRC).convert('RGBA')
print('source', im.size)

# 同时把 1024 方形图标写回 icon.png（保证桌面/源图均为原始 game.png）
icon1024 = im.resize((1024, 1024), Image.LANCZOS)
icon1024.save(ROOT / 'icon.png', 'PNG')
print('wrote icon.png (1024 game.png)')

densities = [
    ('mipmap-mdpi', 48),
    ('mipmap-hdpi', 72),
    ('mipmap-xhdpi', 96),
    ('mipmap-xxhdpi', 144),
    ('mipmap-xxxhdpi', 192),
]

# 清空旧产物（避免残留上一版的自适应/海军蓝文件）
if OUT.exists():
    shutil.rmtree(OUT)
    print('cleaned old mipmaps')

# 只生成标准 mipmap（非自适应）：直接用原始 game.png 缩放铺满
for folder, size in densities:
    d = OUT / folder
    d.mkdir(parents=True, exist_ok=True)
    logo = im.resize((size, size), Image.LANCZOS)
    for nm in ('ic_launcher.png', 'ic_launcher_round.png'):
        logo.save(d / nm, 'PNG')
    print('wrote', folder)

print('DONE (standard game.png mipmaps, no adaptive, no navy)')
