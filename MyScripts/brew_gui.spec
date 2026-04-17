# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — run from MyScripts via build.ps1 (sets cwd).

from pathlib import Path

spec_dir = Path(SPEC).resolve().parent
pieces_dir = spec_dir.parent / "pieces"
gui_dir = spec_dir.parent / "GUI"
fonts_dir = spec_dir / "fonts"

_datas = [("potions/catalog.json", "potions")]
if pieces_dir.is_dir():
    _datas.append((str(pieces_dir), "pieces"))
if gui_dir.is_dir():
    _datas.append((str(gui_dir), "GUI"))
if fonts_dir.is_dir():
    _datas.append((str(fonts_dir), "fonts"))
shapes_json = spec_dir / "object_shapes.json"
if shapes_json.is_file():
    _datas.append((str(shapes_json), "."))

# Keep release bundle app-only (exclude local dev watcher tooling).
_excludes = [
    "dev_watch",
    "watchdog",
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=_excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TLOPOPotionsMaster",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
