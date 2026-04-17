"""TLOPO client window discovery and geometry helpers (Windows-first)."""

from tlopo_client.geometry import (
    calc_aspect_ratio_transform,
    expand_polygon_radially,
    normalize_baseline_fit,
)
from tlopo_client.window import (
    DEFAULT_GAME_WINDOW_TITLE,
    TlopoGameWindow,
    enable_process_dpi_awareness,
    format_window_info_text,
)

__all__ = [
    "DEFAULT_GAME_WINDOW_TITLE",
    "TlopoGameWindow",
    "calc_aspect_ratio_transform",
    "enable_process_dpi_awareness",
    "expand_polygon_radially",
    "format_window_info_text",
    "normalize_baseline_fit",
]
