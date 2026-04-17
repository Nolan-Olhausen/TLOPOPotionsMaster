from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Union

from brew_core.paths import MYSCRIPTS_DIR
from tlopo_client.geometry import normalize_baseline_fit


@dataclass
class BoxShape:
    label: str
    category: str
    color: str
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class PolyShape:
    label: str
    category: str
    color: str
    closed: bool
    pts: List[Tuple[float, float]]


Shape = Union[BoxShape, PolyShape]


def resolve_object_shapes_json() -> Path:
    """
    Resolve ``object_shapes.json``.

    Shared PotionBot config is preferred so keys like ``baseline_fit`` are not shadowed by an
    old hand-copied ``MyScripts/object_shapes.json``. Override with ``BREW_OBJECT_SHAPES``.
    """
    here = MYSCRIPTS_DIR
    local = here / "object_shapes.json"
    root = here.parent.parent
    shared = root / "PotionBotExeGUI" / "configuration" / "object_shapes.json"
    frozen_base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    bundled = frozen_base / "object_shapes.json"
    sidecar = Path(sys.executable).resolve().parent / "object_shapes.json"

    env_path = (os.environ.get("BREW_OBJECT_SHAPES") or "").strip()
    if env_path:
        p = Path(env_path).expanduser()
        if p.is_file():
            return p

    if bundled.is_file():
        return bundled
    if sidecar.is_file():
        return sidecar
    if shared.is_file():
        return shared
    if local.is_file():
        return local
    if getattr(sys, "frozen", False):
        return bundled
    return shared


def _read_next_piece_polygon_expand(data: dict) -> float:
    """JSON ``next_piece_polygon_expand``: scale vertices from centroid (>= 1.0)."""
    raw = data.get("next_piece_polygon_expand", 1.25)
    try:
        e = float(raw)
    except (TypeError, ValueError):
        e = 1.25
    if e < 1.0:
        return 1.0
    if e > 1.6:
        return 1.6
    return e


def load_shapes(path: Path) -> Tuple[List[Shape], int, int, str, float]:
    """
    Returns ``(shapes, baseline_w, baseline_h, baseline_fit, next_piece_polygon_expand)``.

    Optional JSON root key ``baseline_fit``: ``auto`` (default), ``match_width``,
    or ``match_height`` (see ``tlopo_geometry.calc_aspect_ratio_transform``).

    Optional ``next_piece_polygon_expand`` (default ``1.15``): radially scale
    ``next_piece_left`` / ``next_piece_right`` polygons from their centroid after
    mapping to the live client so sampling aligns with the **hex border** when traces
    were drawn too tight around the inner art.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cap = data.get("captured_image_size") or {}
    bw = int(cap.get("width", 1280))
    bh = int(cap.get("height", 720))
    baseline_fit = normalize_baseline_fit(data.get("baseline_fit"))
    next_piece_expand = _read_next_piece_polygon_expand(data)
    raw: List[Shape] = []
    for sh in data.get("shapes", []):
        t = sh.get("type")
        if t == "box":
            raw.append(
                BoxShape(
                    label=sh["label"],
                    category=sh.get("category", "button"),
                    color=sh.get("color", "#00b7ff"),
                    x0=float(sh["x0"]),
                    y0=float(sh["y0"]),
                    x1=float(sh["x1"]),
                    y1=float(sh["y1"]),
                )
            )
        elif t == "polygon":
            pts = [(float(x), float(y)) for x, y in sh["pts"]]
            raw.append(
                PolyShape(
                    label=sh["label"],
                    category=sh.get("category", "button"),
                    color=sh.get("color", "#ff6b00"),
                    closed=bool(sh.get("closed", True)),
                    pts=pts,
                )
            )
    return raw, bw, bh, baseline_fit, next_piece_expand
