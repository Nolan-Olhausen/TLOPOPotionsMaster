from __future__ import annotations

import re
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from typing import Any

import variables.global_variables as gv


def _rgb888_to_hex(r: int, g: int, b: int) -> str:
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _normalize_live_game_visual_mode(v: str | None) -> str:
    s = str(v or "").strip().lower()
    if s == "none":
        return "None"
    if s == "exact":
        return "Exact"
    return "Simple"


def _empty_brew_ring_median_grid() -> dict[str, dict[str, tuple[int, int, int]]]:
    return {
        "next_piece_left": {},
        "next_piece_right": {},
        "current_piece_left": {},
        "current_piece_right": {},
    }


def _slug(s: str) -> str:
    s = s.lower().strip()
    s = "".join(ch if ch.isalnum() else "_" for ch in s)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_") or "unknown"


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.strip().lstrip("#")
    if len(h) != 6:
        return (220, 200, 180)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _blend_hex_towards_white(h: str, t: float) -> str:
    r, g, b = _hex_to_rgb(h)
    t = max(0.0, min(1.0, t))
    r = int(r + (255 - r) * t)
    g = int(g + (255 - g) * t)
    b = int(b + (255 - b) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _shade_hex(h: str, factor: float) -> str:
    r, g, b = _hex_to_rgb(h)
    factor = max(0.35, min(1.65, factor))
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _sample_bbox_mean_color(pil_rgb: Any, bbox: tuple[float, float, float, float]) -> str:
    w, h = pil_rgb.size
    x0, y0, x1, y1 = bbox
    l = max(0, min(w - 1, int(round(min(x0, x1)))))
    r = max(1, min(w, int(round(max(x0, x1)))))
    t = max(0, min(h - 1, int(round(min(y0, y1)))))
    b = max(1, min(h, int(round(max(y0, y1)))))
    if r <= l or b <= t:
        return gv.FALLBACK_PANEL
    crop = pil_rgb.crop((l, t, r, b))
    stat = crop.convert("RGB").resize((1, 1))
    rr, gg, bb = stat.getpixel((0, 0))
    return f"#{rr:02x}{gg:02x}{bb:02x}"


def _sample_mean_hex_image_pixels(img: Any, left: int, top: int, right: int, bottom: int) -> str:
    if right <= left or bottom <= top:
        return "#000000"
    crop = img.crop((left, top, right, bottom)).convert("RGB")
    tiny = crop.resize((1, 1))
    r, g, b = tiny.getpixel((0, 0))
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _bbox_norm_to_screen_rect(
    sx: int, sy: int, sw: int, sh: int, b: tuple[float, float, float, float]
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = b
    l = sx + int(round(min(x0, x1) * sw))
    r = sx + int(round(max(x0, x1) * sw))
    t = sy + int(round(min(y0, y1) * sh))
    bb = sy + int(round(max(y0, y1) * sh))
    return l, t, r, bb


def _display_name_to_piece_suffix(display_name: str) -> str:
    raw = (display_name or "").strip()
    if not raw:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", raw)
    if not cleaned:
        return ""
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", cleaned)
    if not parts:
        return cleaned
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def resolve_canonical_piece_png(ing: dict, pieces_dir: Path) -> Path | None:
    color_key = str(ing.get("color") or "").lower().strip()
    prefix = gv.COLOR_TO_PREFIX.get(color_key)
    if not prefix:
        return None
    lvl = int(ing.get("ingredient_level") or ing.get("level") or 1)
    raw_name = str(ing.get("display_name") or "").strip()
    suffix = _display_name_to_piece_suffix(raw_name)
    if not suffix:
        return None
    p = pieces_dir / f"{prefix}{lvl}{suffix}.png"
    return p if p.is_file() else None


def _resolve_piece_png_fallback(ing: dict, pieces_dir: Path) -> Path | None:
    name = ing.get("display_name") or ""
    color = str(ing.get("color") or "").lower()
    for candidate in (_slug(name) + ".png", f"{color}.png" if color else ""):
        if not candidate:
            continue
        p = pieces_dir / candidate
        if p.is_file():
            return p
    return None


def resolve_piece_png(ing: dict, pieces_dir: Path) -> Path | None:
    return resolve_canonical_piece_png(ing, pieces_dir) or _resolve_piece_png_fallback(ing, pieces_dir)


def resolve_serif_family(root: tk.Tk) -> str:
    """Serif stack for catalog / headings; journal-style faces first (closer to parchment UI art)."""
    prefs = (
        "Palatino Linotype",
        "Book Antiqua",
        "Garamond",
        "Georgia",
        "Cambria",
        "Constantia",
        "Times New Roman",
        "Palatino",
    )
    try:
        fams = {f.lower() for f in tkfont.families(root)}
        for f in prefs:
            if f.lower() in fams:
                return f
    except tk.TclError:
        pass
    return "Times New Roman"


def resolve_ui_sans_family(root: tk.Tk) -> str:
    """UI / body text: lining figures and better digit legibility at small sizes (Windows-first stack)."""
    prefs = (
        "Segoe UI",
        "Calibri",
        "Tahoma",
        "Microsoft Sans Serif",
        "Arial",
    )
    try:
        fams = {f.lower() for f in tkfont.families(root)}
        for f in prefs:
            if f.lower() in fams:
                return f
    except tk.TclError:
        pass
    return "Arial"
