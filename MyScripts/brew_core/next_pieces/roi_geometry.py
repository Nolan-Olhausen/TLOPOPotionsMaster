from __future__ import annotations

from typing import List, Tuple

import numpy as np
from tlopo_client.geometry import calc_aspect_ratio_transform

from ._pillow_deps import Image, ImageDraw, ImageFilter, PIL_OK


def _clip_polygon_pts_to_client(
    pts: List[Tuple[int, int]], cur_w: int, cur_h: int
) -> List[Tuple[int, int]]:
    wm, hm = max(0, cur_w - 1), max(0, cur_h - 1)
    return [(max(0, min(wm, x)), max(0, min(hm, y))) for x, y in pts]


def _scale_pts(
    pts: List[Tuple[float, float]],
    orig_w: int,
    orig_h: int,
    cur_w: int,
    cur_h: int,
    *,
    baseline_fit: str = "auto",
) -> List[Tuple[int, int]]:
    tr = calc_aspect_ratio_transform(
        orig_w, orig_h, cur_w, cur_h, baseline_fit=baseline_fit
    )
    sx, sy = tr["scale_x"], tr["scale_y"]
    ox, oy = tr["offset_x"], tr["offset_y"]
    out: List[Tuple[int, int]] = []
    for x, y in pts:
        out.append((int(round(x * sx + ox)), int(round(y * sy + oy))))
    return out


def _bbox_crop(
    frame_bgra: np.ndarray, pts_abs: List[Tuple[int, int]]
) -> Tuple[np.ndarray, List[Tuple[int, int]], Tuple[int, int, int, int]]:
    xs = [p[0] for p in pts_abs]
    ys = [p[1] for p in pts_abs]
    H, W = frame_bgra.shape[:2]
    x0, y0 = max(0, min(xs)), max(0, min(ys))
    x1, y1 = min(W, max(xs) + 1), min(H, max(ys) + 1)
    roi = frame_bgra[y0:y1, x0:x1].copy()
    local = [(px - x0, py - y0) for (px, py) in pts_abs]
    return roi, local, (x0, y0, x1 - x0, y1 - y0)


def _polygon_mask_local(h: int, w: int, pts_local: List[Tuple[int, int]]) -> np.ndarray:
    m = np.zeros((h, w), dtype=np.uint8)
    if len(pts_local) < 3 or not PIL_OK or Image is None or ImageDraw is None:
        return m
    im = Image.fromarray(m)
    d = ImageDraw.Draw(im)
    d.polygon(pts_local, outline=1, fill=1)
    return (np.array(im) > 0).astype(np.uint8)


def _outer_ring_mask(poly_mask: np.ndarray) -> np.ndarray:
    """
    ``{0,1}`` mask of the **hex frame** (polygon minus eroded interior). TLOPO next-piece
    art is colored on the border; center icons (gold, etc.) sit in the eroded core.

    Calibrated on ``Brewing/pieces/*.png`` OpenCV HSV ring medians. If the ring is too thin,
    returns the full ``poly_mask`` footprint.
    """
    m = (poly_mask > 0).astype(np.uint8)
    if not PIL_OK or Image is None or ImageFilter is None or int(m.sum()) < 16:
        return m
    h, w = m.shape
    k = max(3, min(21, int(round(min(h, w) * 0.16))) | 1)
    im = Image.fromarray(m * 255)
    inner = (np.array(im.filter(ImageFilter.MinFilter(k))) > 127).astype(np.uint8)
    ring = m & (1 - inner)
    if int(ring.sum()) < max(24, int(0.06 * int(m.sum()))):
        return m
    return ring


def _pil_resize_bgra(roi_bgra: np.ndarray, mask: np.ndarray, max_side: int) -> Tuple[np.ndarray, np.ndarray]:
    h, w = roi_bgra.shape[:2]
    scale = min(1.0, float(max_side) / max(h, w))
    if scale >= 0.999:
        return roi_bgra, mask
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    rgb = np.stack([roi_bgra[..., 2], roi_bgra[..., 1], roi_bgra[..., 0]], axis=-1)
    im = Image.fromarray(rgb.astype(np.uint8))
    im2 = im.resize((nw, nh), Image.Resampling.LANCZOS)
    rgb2 = np.asarray(im2)
    bgra2 = np.zeros((nh, nw, 4), dtype=np.uint8)
    bgra2[..., 0] = rgb2[..., 2]
    bgra2[..., 1] = rgb2[..., 1]
    bgra2[..., 2] = rgb2[..., 0]
    bgra2[..., 3] = 255
    pil_m = Image.fromarray((mask * 255).astype(np.uint8))
    m2 = (np.array(pil_m.resize((nw, nh), Image.Resampling.NEAREST)) > 0).astype(np.uint8)
    return bgra2, m2


def bgra_to_hsv_opencv(bgra: np.ndarray) -> np.ndarray:
    # BGRA uint8 to HSV uint8 (OpenCV-compatible H/S/V ranges).
    b = bgra[..., 0].astype(np.float32)
    g = bgra[..., 1].astype(np.float32)
    r = bgra[..., 2].astype(np.float32)
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    delt = maxc - minc
    v = maxc
    s = np.where(maxc > 1e-6, delt / (maxc + 1e-8), 0.0)
    m = delt > 1e-6
    d = np.maximum(delt, 1e-12)
    hh = np.zeros_like(maxc)
    hh = np.where(m & (maxc == r), ((g - b) / d) % 6.0, hh)
    hh = np.where(m & (maxc == g), ((b - r) / d) + 2.0, hh)
    hh = np.where(m & (maxc == b), ((r - g) / d) + 4.0, hh)
    h_deg = 60.0 * hh
    hop = np.clip((h_deg * (179.0 / 360.0)).astype(np.int32), 0, 179).astype(np.uint8)
    s255 = np.clip((s * 255.0).astype(np.int32), 0, 255).astype(np.uint8)
    v255 = np.clip(v.astype(np.int32), 0, 255).astype(np.uint8)
    return np.stack([hop, s255, v255], axis=-1)
