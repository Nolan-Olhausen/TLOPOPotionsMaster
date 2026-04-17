"""
Resolution-independent layout for TLOPO (or any fixed-aspect client).

- Store regions in **normalized** [0,1]×[0,1] of a reference client, or in **pixel**
  coordinates of a **baseline** size (e.g. 1280×720 from a trace).
- At runtime, pass the **live** client width/height and use `calc_aspect_ratio_transform`
  then `apply_aspect_transform_*` to get pixel coordinates in the current capture.

This mirrors the letterbox / pillarbox + scale approach used in PotionBotExeGUI
(`object_recognition._calc_aspect_ratio_transform`).
"""

from __future__ import annotations

from typing import List, Sequence, Tuple, TypedDict


class AspectTransform(TypedDict):
    scale_x: float
    scale_y: float
    offset_x: float
    offset_y: float
    method: str


def normalize_baseline_fit(fit: object) -> str:
    """``auto`` | ``match_width`` | ``match_height`` (aliases accepted)."""
    s = str(fit or "auto").strip().lower()
    if s in ("match_width", "width", "letterbox", "fit_width"):
        return "match_width"
    if s in ("match_height", "height", "pillarbox", "fit_height"):
        return "match_height"
    return "auto"


def calc_aspect_ratio_transform(
    orig_w: int,
    orig_h: int,
    cur_w: int,
    cur_h: int,
    *,
    baseline_fit: str = "auto",
) -> AspectTransform:
    """
    Map baseline (orig_w×orig_h) into current client (cur_w×cur_h) with uniform scale
    and centering, or letterbox/pillarbox offsets when aspect ratios differ.

    ``baseline_fit`` (also set via ``object_shapes.json``):

    - ``auto`` — pick letterbox vs pillarbox from aspect (same as PotionBot).
    - ``match_width`` — always scale to **full client width** (vertical centering /
      crop). Good when the reference layout is width-anchored.
    - ``match_height`` — always scale to **full client height** (horizontal centering /
      crop). Common for game UIs that use “scale with screen size, match height”.
    """
    orig_w = max(1, int(orig_w))
    orig_h = max(1, int(orig_h))
    cur_w = max(1, int(cur_w))
    cur_h = max(1, int(cur_h))

    bf = normalize_baseline_fit(baseline_fit)
    if bf == "match_width":
        scale = cur_w / orig_w
        scaled_h = orig_h * scale
        return {
            "scale_x": scale,
            "scale_y": scale,
            "offset_x": 0.0,
            "offset_y": (cur_h - scaled_h) / 2,
            "method": "match_width",
        }
    if bf == "match_height":
        scale = cur_h / orig_h
        scaled_w = orig_w * scale
        return {
            "scale_x": scale,
            "scale_y": scale,
            "offset_x": (cur_w - scaled_w) / 2,
            "offset_y": 0.0,
            "method": "match_height",
        }

    original_aspect = orig_w / orig_h
    current_aspect = cur_w / cur_h

    if abs(original_aspect - current_aspect) < 0.01:
        scale = min(cur_w / orig_w, cur_h / orig_h)
        return {
            "scale_x": scale,
            "scale_y": scale,
            "offset_x": (cur_w - orig_w * scale) / 2,
            "offset_y": (cur_h - orig_h * scale) / 2,
            "method": "uniform_scale",
        }

    if current_aspect > original_aspect:
        scale = cur_h / orig_h
        scaled_w = orig_w * scale
        return {
            "scale_x": scale,
            "scale_y": scale,
            "offset_x": (cur_w - scaled_w) / 2,
            "offset_y": 0.0,
            "method": "pillarbox_compensation",
        }

    scale = cur_w / orig_w
    scaled_h = orig_h * scale
    return {
        "scale_x": scale,
        "scale_y": scale,
        "offset_x": 0.0,
        "offset_y": (cur_h - scaled_h) / 2,
        "method": "letterbox_compensation",
    }


def apply_aspect_transform_xy(
    x: float, y: float, tr: AspectTransform
) -> Tuple[float, float]:
    return (
        x * tr["scale_x"] + tr["offset_x"],
        y * tr["scale_y"] + tr["offset_y"],
    )


def apply_aspect_transform_points(
    points: Sequence[Tuple[float, float]],
    orig_w: int,
    orig_h: int,
    cur_w: int,
    cur_h: int,
    *,
    baseline_fit: str = "auto",
) -> Tuple[List[Tuple[float, float]], AspectTransform]:
    """Scale a polyline/polygon from baseline space to live client pixels."""
    tr = calc_aspect_ratio_transform(
        orig_w, orig_h, cur_w, cur_h, baseline_fit=baseline_fit
    )
    out = [apply_aspect_transform_xy(px, py, tr) for px, py in points]
    return out, tr


def apply_aspect_transform_box(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    orig_w: int,
    orig_h: int,
    cur_w: int,
    cur_h: int,
    *,
    baseline_fit: str = "auto",
) -> Tuple[float, float, float, float, AspectTransform]:
    """Scale axis-aligned box corners from baseline to live client."""
    tr = calc_aspect_ratio_transform(
        orig_w, orig_h, cur_w, cur_h, baseline_fit=baseline_fit
    )
    ax0, ay0 = apply_aspect_transform_xy(x0, y0, tr)
    ax1, ay1 = apply_aspect_transform_xy(x1, y1, tr)
    return ax0, ay0, ax1, ay1, tr


def normalized_rect_to_baseline_pixels(
    nx0: float,
    ny0: float,
    nx1: float,
    ny1: float,
    baseline_w: int,
    baseline_h: int,
) -> Tuple[float, float, float, float]:
    """Convert 0–1 normalized rect to pixel rect in baseline resolution."""
    bw, bh = max(1, int(baseline_w)), max(1, int(baseline_h))
    return nx0 * bw, ny0 * bh, nx1 * bw, ny1 * bh


def normalized_point_to_baseline_pixels(
    nx: float, ny: float, baseline_w: int, baseline_h: int
) -> Tuple[float, float]:
    bw, bh = max(1, int(baseline_w)), max(1, int(baseline_h))
    return nx * bw, ny * bh


def expand_polygon_radially(
    pts: Sequence[Tuple[float, float]],
    factor: float,
) -> List[Tuple[float, float]]:
    """
    Scale vertex distances from the polygon centroid by ``factor``.

    Used when traced ``next_piece_*`` polygons sit **inside** the visible hex frame:
    expanding outward (``factor`` > 1) aligns sampling with the colored border instead
    of the center icon.
    """
    if factor <= 1.0005 or len(pts) < 1:
        return [(float(x), float(y)) for x, y in pts]
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    return [(cx + factor * (x - cx), cy + factor * (y - cy)) for x, y in pts]


# Other helpers in this module are used internally; MyScripts imports only these three.
__all__ = [
    "normalize_baseline_fit",
    "calc_aspect_ratio_transform",
    "expand_polygon_radially",
]
