# textiva.spec
# PyInstaller build specification for Textiva
# Run manually:  pyinstaller textiva.spec

import os

block_cipher = None

# Read version from version.txt so it shows in the exe properties
with open("version.txt") as f:
    VERSION = f.read().strip()

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("Textiva.ico", "."),      
    ],
    hiddenimports=[
        "keyboard",
        "json",
        "threading",
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "winreg",                  
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
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
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=None,
    icon="Textiva.ico",
)