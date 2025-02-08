from setuptools import setup

APP = ['ui.py']
DATA_FILES = [
    ('', ['icon.png'])  # İkon dosyasını kaynaklara ekle
]

# Entitlements dosyası oluştur
with open('entitlements.plist', 'w') as f:
    f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
</dict>
</plist>''')

OPTIONS = {
    'argv_emulation': True,
    'packages': ['PyQt6'],
    'iconfile': 'icon.png',  # İkon dosyasını belirt
    'includes': [
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'pandas',
        'numpy',
        'asyncio',
        'aiofiles',
        'pathlib',
        'zipfile',
        'xml.etree.ElementTree'
    ],
    'excludes': ['tkinter'],
    'plist': {
        'CFBundleName': 'FaturaIsleyici',
        'CFBundleDisplayName': 'Fatura Isleyici',
        'CFBundleGetInfoString': "Fatura isleme uygulamasi",
        'CFBundleIdentifier': 'com.codev.faturaisleyici',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': "Copyright © 2024, Tum haklari saklidir.",
        'LSMinimumSystemVersion': '10.15',
        'NSHighResolutionCapable': True,
    }
}

setup(
    name='FaturaIsleyici',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 