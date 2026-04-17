from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple

from tlopo_client.geometry import normalize_baseline_fit


def _read_next_piece_polygon_expand(data: dict) -> float:
    raw = data.get("next_piece_polygon_expand", 1.15)
    try:
        e = float(raw)
    except (TypeError, ValueError):
        e = 1.15
    if e < 1.0:
        return 1.0
    if e > 1.6:
        return 1.6
    return e


def load_polygon_for_label(
    path: Path, label: str
) -> Optional[Tuple[int, int, List[Tuple[float, float]], str, float]]:
    """
    Baseline size, polygon ``pts``, ``baseline_fit``, and radial expand factor.

    ``next_piece_polygon_expand`` from JSON applies only to ``next_piece_left`` /
    ``next_piece_right``; other labels use ``1.0``.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cap = data.get("captured_image_size") or {}
    bw = int(cap.get("width", 1280))
    bh = int(cap.get("height", 720))
    baseline_fit = normalize_baseline_fit(data.get("baseline_fit"))
    piece_expand = _read_next_piece_polygon_expand(data)
    expand = (
        piece_expand
        if label in ("next_piece_left", "next_piece_right")
        else 1.0
    )
    for sh in data.get("shapes", []):
        if sh.get("type") != "polygon":
            continue
        if sh.get("label") != label:
            continue
        pts = [(float(x), float(y)) for x, y in sh["pts"]]
        if len(pts) >= 3:
            return bw, bh, pts, baseline_fit, expand
    return None


def resolve_first_polygon_label(
    shapes_path: Path, labels: Tuple[str, ...]
) -> Optional[str]:
    """First label in ``labels`` that exists as a polygon in ``object_shapes.json``."""
    for lab in labels:
        if load_polygon_for_label(shapes_path, lab) is not None:
            return lab
    return None
