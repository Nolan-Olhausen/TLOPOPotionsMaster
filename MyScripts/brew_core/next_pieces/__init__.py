"""
Next-piece color ID (ring sampling + calibration), without OpenCV.

Package layout: ``shape_json``, ``roi_geometry``, ``ring_sampling``.
"""

from __future__ import annotations

from ._log import LogFn, _default_log
from .ring_sampling import sample_piece_ring_at_label, sample_polygon_median_bgra
from .roi_geometry import bgra_to_hsv_opencv
from .shape_json import load_polygon_for_label, resolve_first_polygon_label

__all__ = [
    "LogFn",
    "_default_log",
    "bgra_to_hsv_opencv",
    "load_polygon_for_label",
    "resolve_first_polygon_label",
    "sample_piece_ring_at_label",
    "sample_polygon_median_bgra",
]
