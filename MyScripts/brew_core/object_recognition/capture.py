from __future__ import annotations

import sys
from typing import Optional, Tuple

from ._optional_deps import NUMPY_OK, mss, np


def capture_client_bgra(
    left: int, top: int, width: int, height: int
) -> Optional["np.ndarray"]:
    """Single mss grab: ``(H, W, 4)`` uint8 BGRA (same layout as PotionBot).

    ``mss`` may back ``ScreenShot`` with a buffer that is reused or invalidated when the
    ``MSS`` context exits. Copy **inside** the ``with`` block. On Windows, one discarded
    grab in the **same** session primes DXGI/GDI so the returned frame matches the live
    client (avoids an all-Grey first read without relying on a second process-wide call).
    """
    if mss is None or not NUMPY_OK:
        return None
    bbox = {"left": int(left), "top": int(top), "width": width, "height": height}
    with mss.mss() as sct:
        if sys.platform == "win32":
            sct.grab(bbox)
        shot = sct.grab(bbox)
        return np.asarray(shot, dtype=np.uint8).copy()


def mapping_size_from_bgra_frame(
    frame: Optional["np.ndarray"], fallback_w: int, fallback_h: int
) -> Tuple[int, int]:
    """Use actual bitmap dimensions so ROI geometry matches ``mss`` pixels."""
    if frame is None or getattr(frame, "ndim", 0) < 2:
        return fallback_w, fallback_h
    h, w = int(frame.shape[0]), int(frame.shape[1])
    if w < 1 or h < 1:
        return fallback_w, fallback_h
    return w, h
