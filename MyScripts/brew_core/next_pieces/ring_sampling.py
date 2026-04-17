from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from tlopo_client.geometry import expand_polygon_radially

from ._pillow_deps import PIL_OK
from .roi_geometry import (
    _bbox_crop,
    _clip_polygon_pts_to_client,
    _outer_ring_mask,
    _pil_resize_bgra,
    _polygon_mask_local,
    _scale_pts,
    bgra_to_hsv_opencv,
)
from .shape_json import load_polygon_for_label


def _roi_ring_hsv_spread(
    frame_bgra: np.ndarray,
    shapes_path: Path,
    poly_label: str,
) -> Optional[
    Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, int, int]
]:
    """
    Shared crop/resize/ring extraction for ``poly_label``.

    Returns ``(H_flat, S_flat, V_flat, spread_flat, B_flat, G_flat, R_flat, bw, bh, n_ring)``
    where ``B_flat`` / ``G_flat`` / ``R_flat`` are OpenCV BGR channels on the ring, or ``None``.
    """
    if not PIL_OK:
        return None
    loaded = load_polygon_for_label(shapes_path, poly_label)
    if not loaded:
        return None
    baseline_w, baseline_h, raw_pts, baseline_fit, radial_expand = loaded
    cur_h, cur_w = frame_bgra.shape[:2]
    pts_abs = _scale_pts(
        raw_pts, baseline_w, baseline_h, cur_w, cur_h, baseline_fit=baseline_fit
    )
    if radial_expand > 1.0005:
        pts_f = expand_polygon_radially(
            [(float(x), float(y)) for x, y in pts_abs], radial_expand
        )
        pts_abs = _clip_polygon_pts_to_client(
            [(int(round(x)), int(round(y))) for x, y in pts_f], cur_w, cur_h
        )
    roi_bgra, pts_local, (_bx, _by, bw_i, bh_i) = _bbox_crop(frame_bgra, pts_abs)
    roi_mask = _polygon_mask_local(bh_i, bw_i, pts_local)
    roi_bgra, roi_mask = _pil_resize_bgra(roi_bgra, roi_mask, 140)
    hsv_roi = bgra_to_hsv_opencv(roi_bgra)
    ring_u8 = _outer_ring_mask(roi_mask)
    zone_b = ring_u8.astype(bool)
    if int(zone_b.sum()) < 12:
        zone_b = (roi_mask > 0).astype(bool)
    n_ring = int(zone_b.sum())
    if n_ring < 8:
        return None
    H = hsv_roi[..., 0].astype(np.int16)[zone_b]
    S = hsv_roi[..., 1].astype(np.int16)[zone_b]
    V = hsv_roi[..., 2].astype(np.int16)[zone_b]
    bgr = roi_bgra[..., :3].astype(np.int16)
    b0, g0, r0 = bgr[..., 0][zone_b], bgr[..., 1][zone_b], bgr[..., 2][zone_b]
    spread = np.maximum(np.maximum(r0, g0), b0) - np.minimum(np.minimum(r0, g0), b0)
    return H, S, V, spread, b0, g0, r0, int(bw_i), int(bh_i), n_ring


def sample_polygon_median_bgra(
    frame_bgra: np.ndarray,
    shapes_path: Path,
    poly_label: str,
) -> Dict[str, Any]:
    """
    Median B/G/R over the **full** polygon interior (after the same resize as piece classification).

    Used when the slot shows empty board (pair moved away) to capture a stable board color.
    """
    if not PIL_OK:
        return {"ok": False, "error": "Pillow is required for polygon masks."}
    loaded = load_polygon_for_label(shapes_path, poly_label)
    if not loaded:
        return {
            "ok": False,
            "error": f"Polygon `{poly_label}` not found in {shapes_path.name}.",
        }
    baseline_w, baseline_h, raw_pts, baseline_fit, radial_expand = loaded
    cur_h, cur_w = frame_bgra.shape[:2]
    pts_abs = _scale_pts(
        raw_pts, baseline_w, baseline_h, cur_w, cur_h, baseline_fit=baseline_fit
    )
    if radial_expand > 1.0005:
        pts_f = expand_polygon_radially(
            [(float(x), float(y)) for x, y in pts_abs], radial_expand
        )
        pts_abs = _clip_polygon_pts_to_client(
            [(int(round(x)), int(round(y))) for x, y in pts_f], cur_w, cur_h
        )
    roi_bgra, pts_local, (_bx, _by, bw_i, bh_i) = _bbox_crop(frame_bgra, pts_abs)
    roi_mask = _polygon_mask_local(bh_i, bw_i, pts_local)
    roi_bgra, roi_mask = _pil_resize_bgra(roi_bgra, roi_mask, 140)
    mask = roi_mask > 0
    n = int(mask.sum())
    if n < 12:
        return {
            "ok": False,
            "error": f"Too few pixels in `{poly_label}` mask ({n}); check capture and polygon.",
        }
    bgr = roi_bgra[..., :3].astype(np.float32)
    b = bgr[..., 0][mask]
    g = bgr[..., 1][mask]
    r = bgr[..., 2][mask]
    return {
        "ok": True,
        "poly_label": poly_label,
        "n_pixels": n,
        "b": int(round(float(np.median(b)))),
        "g": int(round(float(np.median(g)))),
        "r": int(round(float(np.median(r)))),
    }


def sample_piece_ring_at_label(
    frame_bgra: np.ndarray,
    shapes_path: Path,
    poly_label: str,
) -> Dict[str, Any]:
    """
    Ring pixel stats for guided calibration (current-piece left slot): RGB bands + HSV reference.

    Returns ``{"ok": True, ... stats ...}`` or ``{"ok": False, "error": "..."}``.
    """
    got = _roi_ring_hsv_spread(frame_bgra, shapes_path, poly_label)
    if got is None:
        return {
            "ok": False,
            "error": f"Could not sample ring for `{poly_label}` (missing polygon or too few pixels).",
        }
    H, S, V, spread, Bch, Gch, Rch, bw_i, bh_i, n_ring = got

    def pct(arr: np.ndarray, p: float) -> int:
        return int(round(float(np.percentile(arr, p))))

    stats = {
        "ok": True,
        "poly_label": poly_label,
        "roi_bbox_wh": (bw_i, bh_i),
        "n_ring_pixels": n_ring,
        "r_med": pct(Rch, 50),
        "g_med": pct(Gch, 50),
        "b_med": pct(Bch, 50),
        "r_p5": pct(Rch, 5),
        "r_p95": pct(Rch, 95),
        "g_p5": pct(Gch, 5),
        "g_p95": pct(Gch, 95),
        "b_p5": pct(Bch, 5),
        "b_p95": pct(Bch, 95),
        "h_p5": pct(H, 5),
        "h_p50": pct(H, 50),
        "h_p95": pct(H, 95),
        "s_p5": pct(S, 5),
        "s_p50": pct(S, 50),
        "s_p95": pct(S, 95),
        "v_p5": pct(V, 5),
        "v_p50": pct(V, 50),
        "v_p95": pct(V, 95),
        "spread_p5": pct(spread, 5),
        "spread_p50": pct(spread, 50),
        "spread_p95": pct(spread, 95),
    }
    return stats
