from __future__ import annotations

import json
import sys
from pathlib import Path

import variables.global_variables as gv


def brew_gui_settings_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / gv.BREW_GUI_SETTINGS_FILENAME
    return Path(__file__).resolve().parent.parent / gv.BREW_GUI_SETTINGS_FILENAME


def get_catalog_path() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base / "potions" / "catalog.json"
    return Path(__file__).resolve().parent.parent / "potions" / "catalog.json"


def get_pieces_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "pieces"
    return Path(__file__).resolve().parent.parent.parent / "pieces"


def get_gui_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "GUI"
    return Path(__file__).resolve().parent.parent.parent / "GUI"


def get_brew_fonts_dir() -> Path:
    """Directory with bundled UI fonts (Cormorant, OFL). Next to ``app`` when dev; under ``fonts`` in frozen builds."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent)) / "fonts"
    return Path(__file__).resolve().parent.parent / "fonts"


def get_cormorant_regular_path() -> Path:
    return get_brew_fonts_dir() / "Cormorant-Regular.ttf"


def get_cormorant_bold_path() -> Path:
    return get_brew_fonts_dir() / "Cormorant-Bold.ttf"


def brew_bundled_cormorant_available() -> bool:
    r = get_cormorant_regular_path()
    b = get_cormorant_bold_path()
    return r.is_file() and b.is_file()


def resolve_list_template_path(gui_dir: Path) -> Path | None:
    for name in gv.LIST_TEMPLATE_NAMES:
        p = gui_dir / name
        if p.is_file():
            return p
    return None


def resolve_game_template_path(gui_dir: Path) -> Path | None:
    for name in gv.GAME_TEMPLATE_NAMES:
        p = gui_dir / name
        if p.is_file():
            return p
    return None


def load_catalog(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    potions = data.get("potions")
    if not isinstance(potions, list):
        raise ValueError("catalog.json must contain a 'potions' array")
    return potions
