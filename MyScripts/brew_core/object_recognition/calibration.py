from __future__ import annotations

import json
import sys
from pathlib import Path

from brew_core.paths import MYSCRIPTS_DIR


def _brew_gui_settings_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "brew_gui_settings.json"
    return MYSCRIPTS_DIR / "brew_gui_settings.json"


def _load_runtime_color_calibration() -> tuple[
    dict[str, dict[str, tuple[int, int, int]]], dict[str, tuple[int, int, int]]
]:
    """Load ring-grid and display RGB calibration from brew_gui_settings.json."""
    ring_grid: dict[str, dict[str, tuple[int, int, int]]] = {
        "next_piece_left": {},
        "next_piece_right": {},
        "current_piece_left": {},
        "current_piece_right": {},
    }
    piece_display: dict[str, tuple[int, int, int]] = {}
    p = _brew_gui_settings_path()
    if not p.is_file():
        return ring_grid, piece_display
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ring_grid, piece_display
    if not isinstance(data, dict):
        return ring_grid, piece_display
    rmg = data.get("ring_median_grid")
    if isinstance(rmg, dict):
        for sk, inner in rmg.items():
            if sk not in ring_grid or not isinstance(inner, dict):
                continue
            for tok, tup in inner.items():
                if not isinstance(tok, str) or not isinstance(tup, (list, tuple)) or len(tup) != 3:
                    continue
                try:
                    r, g, b = int(tup[0]), int(tup[1]), int(tup[2])
                except (TypeError, ValueError):
                    continue
                ring_grid[sk][tok] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    prgb = data.get("piece_display_rgb")
    if isinstance(prgb, dict):
        for tok, tup in prgb.items():
            if not isinstance(tok, str) or not isinstance(tup, (list, tuple)) or len(tup) != 3:
                continue
            try:
                r, g, b = int(tup[0]), int(tup[1]), int(tup[2])
            except (TypeError, ValueError):
                continue
            piece_display[tok] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    return ring_grid, piece_display
