# -*- coding: utf-8 -*-
"""
CI 辅助：为 Tauri Android Release 构建配置签名。
Release 构建默认产物是「未签名」APK，无法直接安装；这里用 Android 标准的
debug keystore（密码 android / 别名 androiddebugkey）对 release 进行签名，
足以满足本地侧载 / 测试安装。正式上架 Play 商店时再换成自己的上传密钥即可。
"""
import os
import pathlib
import subprocess

HOME = os.path.expanduser('~')
ks = pathlib.Path(HOME) / '.android' / 'debug.keystore'
ks.parent.mkdir(parents=True, exist_ok=True)

if not ks.exists():
    print('Generating debug keystore for release signing:', ks)
    r = subprocess.run([
        'keytool', '-genkey', '-v',
        '-keystore', str(ks),
        '-storepass', 'android', '-keypass', 'android',
        '-alias', 'androiddebugkey',
        '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000',
        '-dname', 'CN=Android Debug,O=Android,C=US',
    ])
    if r.returncode != 0:
        print('WARN: keytool failed, release APK may end up unsigned')
else:
    print('debug keystore already exists:', ks)

# keystore.properties 供 app/build.gradle.kts 的 signingConfigs 读取
props = pathlib.Path('src-tauri/gen/android/keystore.properties')
props.write_text(
    'keyAlias=androiddebugkey\n'
    'keyPassword=android\n'
    'storePassword=android\n'
    f'storeFile={ks}\n',
    encoding='utf-8',
)
print('wrote', props)

gradle = pathlib.Path('src-tauri/gen/android/app/build.gradle.kts')
if gradle.exists():
    g = gradle.read_text(encoding='utf-8')
    if 'signingConfigs' not in g:
        if 'import java.io.FileInputStream' not in g:
            g = g.replace(
                'plugins {',
                'import java.io.FileInputStream\nimport java.util.Properties\n\nplugins {',
                1,
            )
        g = g.replace(
            'buildTypes {',
            'signingConfigs {\n'
            '        create("release") {\n'
            '            val keystorePropertiesFile = rootProject.file("keystore.properties")\n'
            '            val keystoreProperties = Properties()\n'
            '            if (keystorePropertiesFile.exists()) {\n'
            '                keystoreProperties.load(FileInputStream(keystorePropertiesFile))\n'
            '            }\n'
            '            keyAlias = keystoreProperties["keyAlias"] as String\n'
            '            keyPassword = keystoreProperties["keyPassword"] as String\n'
            '            storeFile = file(keystoreProperties["storeFile"] as String)\n'
            '            storePassword = keystoreProperties["storePassword"] as String\n'
            '        }\n'
            '    }\n\n'
            '    buildTypes {',
            1,
        )
        if 'getByName("release") {' in g:
            g = g.replace(
                'getByName("release") {',
                'getByName("release") {\n'
                '            signingConfig = signingConfigs.getByName("release")',
                1,
            )
        elif 'release {' in g:
            g = g.replace(
                'release {',
                'release {\n'
                '            signingConfig = signingConfigs.getByName("release")',
                1,
            )
        gradle.write_text(g, encoding='utf-8')
        print('patched build.gradle.kts for release signing')
    else:
        print('signingConfigs already present, skip')
else:
    print('WARN: build.gradle.kts not found at', gradle)
