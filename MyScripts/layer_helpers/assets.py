from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Any

import variables.global_variables as gv

from core_helpers.app_utilities import resolve_piece_png

try:
    from PIL import Image, ImageTk  # type: ignore[import-untyped]

    PIL_OK = True
except Exception:
    Image = None
    ImageTk = None
    PIL_OK = False

try:
    _LANCZOS = Image.Resampling.LANCZOS if Image is not None else None
except Exception:
    _LANCZOS = None


def _load_piece_thumbnail(self, path: Path, *, size: int | None = None) -> tk.PhotoImage | None:
    px = int(size) if size is not None else gv.PIECE_SIZE
    px = max(8, min(256, px))
    cache_key = f"{path.resolve()}|{px}"
    if cache_key in self._thumb_cache:
        return self._thumb_cache[cache_key]

    if PIL_OK and Image is not None and ImageTk is not None and _LANCZOS is not None:
        try:
            im = Image.open(path).convert("RGBA")
            im = im.resize((px, px), _LANCZOS)
            photo = ImageTk.PhotoImage(im)
        except OSError:
            return None
    else:
        try:
            photo = tk.PhotoImage(file=str(path))
            iw, ih = photo.width(), photo.height()
            if iw > 0 and max(iw, ih) > px:
                step = max(1, max(iw, ih) // px)
                photo = photo.subsample(step, step)
        except tk.TclError:
            return None

    self._thumb_cache[cache_key] = photo
    self._thumb_keepalive.append(photo)
    return photo


def _resolve_exact_piece_png_for_gem(self, gem: Any, potion: dict | None) -> Path | None:
    color = str(getattr(gem, "color", "") or "").strip().lower()
    level = int(getattr(gem, "level", 1) or 1)
    if level < 1:
        level = 1

    if potion is not None:
        ing = self._ingredient_for_board_line_color(potion, color)
        if ing is not None:
            ing_use = dict(ing)
            ing_use["level"] = level
            png = resolve_piece_png(ing_use, self.pieces_dir)
            if png is not None and png.is_file():
                return png

    prefix = gv.COLOR_TO_PREFIX.get("black" if color == "grey" else color)
    if not prefix:
        return None
    pattern = f"{prefix}{level}*.png"
    try:
        for p in self.pieces_dir.glob(pattern):
            if p.is_file():
                return p
    except OSError:
        return None
    return None
