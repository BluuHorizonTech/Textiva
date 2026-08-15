# textiva.spec
# PyInstaller build specification for textiva
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
        "unittest",
        "email",
        "html",
        "http",
        "urllib",
        "xml",
        "pydoc",
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
    name="textiva",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                           # compress the exe (smaller download)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                      # no black console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # version info shown in Windows Explorer → Properties
    version=None,
    icon="Textiva.ico",                          # add "icon.ico" here if you have one
)