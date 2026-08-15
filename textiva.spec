# textiva.spec
# PyInstaller build specification for Textiva
# Run manually:  pyinstaller textiva.spec

import os

block_cipher = None

# Read version from version.txt so it shows in the exe properties
with open("version.txt") as f:
    VERSION = f.read().strip()

a = Analysis(
    ["main.py"],                        # entry point
    pathex=["."],
    binaries=[],
    datas=[],                           # add extra files here if needed
    hiddenimports=[
        "keyboard",
        "json",
        "threading",
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ── SAFE to exclude ────────────────────────────────────────────
        # These are never touched by PyInstaller internals or your app
        "unittest",
        "pydoc",
        "doctest",
        "pdb",
        "difflib",
        "ftplib",
        "imaplib",
        "poplib",
        "smtplib",
        "telnetlib",
        "xmlrpc",
        "tkinter.test",
        "lib2to3",
        "turtledemo",
        "turtle",
        "idlelib",
        "antigravity",
        "cgi",
        "cgitb",

        # ── DO NOT exclude these ────────────────────────────────────────
        # "urllib"   <- PyInstaller runtime hooks need this via zipfile/pathlib
        # "email"    <- required by several stdlib modules internally
        # "html"     <- required by http and others
        # "http"     <- required internally
        # "xml"      <- required internally by several hooks
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Textiva",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                      # no black console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=None,
    icon="Textiva.ico",
)