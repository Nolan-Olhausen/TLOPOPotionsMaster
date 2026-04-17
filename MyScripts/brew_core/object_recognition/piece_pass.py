from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .calibration import _load_runtime_color_calibration
from ._log import LogFn, _default_log


def _run_piece_classification_pass(
    bundle: Dict[str, Any],
    lg: LogFn,
    log: Optional[LogFn],
    verbose_logs: bool,
) -> Dict[str, Any]:
    frame_bgra = bundle["frame_bgra"]
    path: Path = bundle["path"]
    piece_info: Dict[str, Any] = {
        "next_pieces": {},
        "current_piece_left": None,
        "current_piece_right": None,
        "current_piece_area_combined": None,
    }
    try:
        from brew_core.automation_color_recognition import calibrated_label_for_slot_ring
        from brew_core.next_pieces import resolve_first_polygon_label, sample_piece_ring_at_label

        ring_grid, piece_display = _load_runtime_color_calibration()

        def _slot_obj(label: str | None) -> dict[str, Any]:
            lab = label if isinstance(label, str) else "Unknown"
            return {
                "label": lab,
                "top": [(lab, 1.0)] if lab != "Unknown" else [],
                "fractions": {lab: 1.0} if lab != "Unknown" else {},
                "n_pixels": 0,
                "roi_size": (0, 0),
            }

        for slot_key in ("next_piece_left", "next_piece_right"):
            sn = sample_piece_ring_at_label(frame_bgra, path, slot_key)
            if sn.get("ok"):
                rgb = (int(sn["r_med"]), int(sn["g_med"]), int(sn["b_med"]))
                piece_info["next_left_ring_rgb" if slot_key == "next_piece_left" else "next_right_ring_rgb"] = rgb
                tok = calibrated_label_for_slot_ring(
                    slot_key,
                    rgb,
                    ring_median_grid=ring_grid,
                    piece_display_rgb=piece_display,
                    per_channel_max_delta=0,
                )
                piece_info["next_pieces"][slot_key] = _slot_obj(tok)
            else:
                piece_info["next_pieces"][slot_key] = _slot_obj(None)

        lpoly = resolve_first_polygon_label(path, ("current_piece_left", "validation_left"))
        rpoly = resolve_first_polygon_label(path, ("current_piece_right", "validation_right"))
        if lpoly:
            sl = sample_piece_ring_at_label(frame_bgra, path, lpoly)
            if sl.get("ok"):
                rgb_l = (int(sl["r_med"]), int(sl["g_med"]), int(sl["b_med"]))
                piece_info["current_left_ring_rgb"] = rgb_l
                tok_l = calibrated_label_for_slot_ring(
                    "current_piece_left",
                    rgb_l,
                    ring_median_grid=ring_grid,
                    piece_display_rgb=piece_display,
                    per_channel_max_delta=0,
                )
                piece_info["current_piece_left"] = _slot_obj(tok_l)
        if rpoly:
            sr = sample_piece_ring_at_label(frame_bgra, path, rpoly)
            if sr.get("ok"):
                rgb_r = (int(sr["r_med"]), int(sr["g_med"]), int(sr["b_med"]))
                piece_info["current_right_ring_rgb"] = rgb_r
                tok_r = calibrated_label_for_slot_ring(
                    "current_piece_right",
                    rgb_r,
                    ring_median_grid=ring_grid,
                    piece_display_rgb=piece_display,
                    per_channel_max_delta=0,
                )
                piece_info["current_piece_right"] = _slot_obj(tok_r)
    except Exception as e:
        piece_info["error"] = str(e)
        if verbose_logs:
            (log or _default_log)("WARNING", f"\U0001f9e9 Next-piece pass skipped or failed: {e}")

    return piece_info
