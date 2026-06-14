# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH).resolve()
APP_VERSION = "2.0.0"

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TabloraEditor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TabloraEditor",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="TabloraEditor.app",
        icon=None,
        bundle_identifier="com.tablora.editor",
        info_plist={
            "CFBundleName": "Tablora Editor",
            "CFBundleDisplayName": "Tablora Editor",
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleVersion": APP_VERSION,
        },
    )
else:
    app = coll
