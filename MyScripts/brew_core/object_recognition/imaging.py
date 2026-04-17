from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ._optional_deps import Image, ImageDraw, PIL_AVAILABLE, np

# numpy required at runtime for these helpers; callers check NUMPY_OK


def _to_gray_from_mss_bgra(img_bgra: "np.ndarray") -> "np.ndarray":
    b = img_bgra[..., 0].astype(np.float32)
    g = img_bgra[..., 1].astype(np.float32)
    r = img_bgra[..., 2].astype(np.float32)
    return 0.114 * b + 0.587 * g + 0.299 * r


def _polygon_mask(h: int, w: int, poly_pts: List[Tuple[int, int]]) -> "np.ndarray":
    mask = np.zeros((h, w), dtype=np.uint8)
    if len(poly_pts) < 3:
        return mask
    if PIL_AVAILABLE and Image is not None and ImageDraw is not None:
        pil_mask = Image.fromarray(mask * 255)
        draw = ImageDraw.Draw(pil_mask)
        draw.polygon(poly_pts, outline=1, fill=1)
        return (np.array(pil_mask) > 0).astype(np.uint8)
    try:
        import cv2 as _cv2  # type: ignore[import-not-found]

        pts = np.array(poly_pts, dtype=np.int32).reshape((-1, 1, 2))
        _cv2.fillPoly(mask, [pts], color=1)
        return mask
    except Exception:
        return mask


def _presence_metrics(
    gray: "np.ndarray", roi_mask: Optional["np.ndarray"] = None
) -> Dict[str, Any]:
    if roi_mask is not None:
        pixels = gray[roi_mask > 0]
    else:
        pixels = gray.ravel()
    if pixels.size == 0:
        return {"mean_gray": 0.0, "contrast": 0.0, "n_pixels": 0}
    mean = float(pixels.mean())
    std = float(pixels.std())
    return {
        "mean_gray": round(mean, 3),
        "contrast": round(std, 3),
        "n_pixels": int(pixels.size),
    }


def _clip(v: float, lo: int, hi: int) -> int:
    return int(max(lo, min(hi, round(v))))
