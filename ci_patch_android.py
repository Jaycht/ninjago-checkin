#!/usr/bin/env python3
"""
九漫成长营 Android 构建补丁
在 `npx tauri android init` 之后运行，修复/覆盖自动生成的 Android 工程配置。
"""
import re
import subprocess
import sys
import pathlib


def patch_manifest():
    manifest = pathlib.Path('src-tauri/gen/android/app/src/main/AndroidManifest.xml')
    if not manifest.exists():
        print('AndroidManifest.xml not found, skip')
        return
    t = manifest.read_text(encoding='utf-8')
    if 'xmlns:android=' not in t:
        t = t.replace('<manifest', '<manifest xmlns:android="http://schemas.android.com/apk/res/android"', 1)
    perms = ''
    if 'android.permission.INTERNET' not in t:
        perms += '    <uses-permission android:name="android.permission.INTERNET" />\n'
    if perms:
        t = t.replace('</manifest>', perms + '</manifest>')
    t2 = re.sub(r'(<activity\b[^>]*?)(\sandroid:screenOrientation="[^"]*)', r'\1 android:screenOrientation="sensor"', t, count=1, flags=re.S)
    if t2 == t:
        t2 = re.sub(r'(<activity\b)', r'\1 android:screenOrientation="sensor"', t, count=1, flags=re.S)
    manifest.write_text(t2, encoding='utf-8')
    print('AndroidManifest patched (INTERNET + sensor orientation)')


def patch_strings():
    strings = pathlib.Path('src-tauri/gen/android/app/src/main/res/values/strings.xml')
    if not strings.exists():
        print('strings.xml not found, skip')
        return
    s = strings.read_text(encoding='utf-8')
    s2 = re.sub(r'(<string name="app_name"[^>]*>)[^<]*(</string>)', r'\1九漫成长营\2', s, count=1)
    strings.write_text(s2, encoding='utf-8')
    print('app label set to 九漫成长营')


def patch_gradle():
    """删除冲突的 import java.util.Properties，Gradle Kotlin DSL 默认已导入 kotlin.properties.Properties。"""
    gradle_kts = pathlib.Path('src-tauri/gen/android/app/build.gradle.kts')
    if not gradle_kts.exists():
        print('build.gradle.kts not found, skip')
        return
    g = gradle_kts.read_text(encoding='utf-8')
    g = re.sub(r'^\s*import\s+java\.util\.Properties\s*[\r\n]+', '', g, flags=re.M)
    gradle_kts.write_text(g, encoding='utf-8')
    print('build.gradle.kts import removed (Properties ambiguous fix)')


def patch_status_bar_color():
    """将系统状态栏/窗口背景色设为 #1a0f3e，避免标题栏上方留白。"""
    for themes_path in [
        pathlib.Path('src-tauri/gen/android/app/src/main/res/values/themes.xml'),
        pathlib.Path('src-tauri/gen/android/app/src/main/res/values-night/themes.xml'),
    ]:
        if not themes_path.exists():
            continue
        tt = themes_path.read_text(encoding='utf-8')
        # statusBarColor
        if 'android:statusBarColor' in tt:
            tt = re.sub(r'(<item\s+name="android:statusBarColor">)[^<]+(</item>)',
                        r'\1#1a0f3e\2', tt, count=1)
        else:
            tt = re.sub(r'(</style>)',
                        r'        <item name="android:statusBarColor">#1a0f3e</item>\n    \1',
                        tt, count=1)
        # windowBackground (兜底，防止标题栏上方出现系统窗口背景色/白条)
        if 'android:windowBackground' in tt:
            tt = re.sub(r'(<item\s+name="android:windowBackground">)[^<]+(</item>)',
                        r'\1#1a0f3e\2', tt, count=1)
        else:
            tt = re.sub(r'(</style>)',
                        r'        <item name="android:windowBackground">#1a0f3e</item>\n    \1',
                        tt, count=1)
        themes_path.write_text(tt, encoding='utf-8')
        print(f'{themes_path.name}: statusBarColor & windowBackground set to #1a0f3e')


def ensure_pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'pillow'])
        from PIL import Image
        return Image


def patch_icons():
    """用 src-tauri/icons/icon.png 显式覆盖 Android 各密度 mipmap。"""
    Image = ensure_pillow()
    icon_src = pathlib.Path('src-tauri/icons/icon.png')
    if not icon_src.exists():
        print('src-tauri/icons/icon.png not found, skip explicit icon override')
        return

    im = Image.open(icon_src).convert('RGBA')
    res_dir = pathlib.Path('src-tauri/gen/android/app/src/main/res')
    sizes = {
        'mipmap-mdpi': 48,
        'mipmap-hdpi': 72,
        'mipmap-xhdpi': 96,
        'mipmap-xxhdpi': 144,
        'mipmap-xxxhdpi': 192,
    }

    def make_icon(src_im, size):
        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        thumb = src_im.copy()
        thumb.thumbnail((size, size), Image.LANCZOS)
        x = (size - thumb.width) // 2
        y = (size - thumb.height) // 2
        canvas.paste(thumb, (x, y), thumb)
        return canvas

    for folder, size in sizes.items():
        d = res_dir / folder
        if not d.exists():
            continue
        icon = make_icon(im, size)
        icon.save(d / 'ic_launcher.png', 'PNG')
        icon.save(d / 'ic_launcher_round.png', 'PNG')
        icon.save(d / 'ic_launcher_foreground.png', 'PNG')
        print(f'android icon {folder} -> {size}x{size}')

    anydpi = res_dir / 'mipmap-anydpi-v26'
    if anydpi.exists():
        xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
            '    <background android:drawable="@android:color/transparent"/>\n'
            '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
            '</adaptive-icon>\n'
        )
        for nm in ('ic_launcher.xml', 'ic_launcher_round.xml'):
            (anydpi / nm).write_text(xml, encoding='utf-8')
        print('adaptive icon xml updated')


def main():
    patch_manifest()
    patch_strings()
    patch_gradle()
    patch_status_bar_color()
    patch_icons()


if __name__ == '__main__':
    main()
