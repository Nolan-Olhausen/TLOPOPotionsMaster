from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ._log import LogFn, _sink_log_for_verbose
from ._optional_deps import NUMPY_OK, mss
from .capture import capture_client_bgra, mapping_size_from_bgra_frame
from .imaging import _to_gray_from_mss_bgra
from .piece_pass import _run_piece_classification_pass
from .recognize import _accumulate_shape_roi_metrics
from .scale import _scaled_shapes_for_size
from .shapes import load_shapes, resolve_object_shapes_json


def _capture_recognition_bundle(
    client_rect: Tuple[int, int, int, int],
    *,
    shapes_json: Optional[Path],
    lg: LogFn,
) -> Optional[Dict[str, Any]]:
    """One mss grab + grayscale + scaled shapes. Returns ``None`` on hard failure."""
    path = shapes_json or resolve_object_shapes_json()
    if not path.is_file():
        lg(
            "ERROR",
            f"object_shapes.json not found at {path}. "
            "Copy from PotionBotExeGUI/configuration/ or symlink.",
        )
        return None
    raw, baseline_w, baseline_h, baseline_fit, next_piece_expand = load_shapes(path)
    l, t, r, b = client_rect
    cur_w, cur_h = int(r - l), int(b - t)
    if cur_w < 5 or cur_h < 5:
        lg("ERROR", "Client area too small to capture.")
        return None

    frame_bgra = capture_client_bgra(l, t, cur_w, cur_h)
    if frame_bgra is None:
        lg("ERROR", "Screen capture failed.")
        return None
    gray = _to_gray_from_mss_bgra(frame_bgra)
    cur_w, cur_h = mapping_size_from_bgra_frame(frame_bgra, cur_w, cur_h)

    shapes, tr = _scaled_shapes_for_size(
        raw,
        baseline_w,
        baseline_h,
        cur_w,
        cur_h,
        baseline_fit=baseline_fit,
        next_piece_polygon_expand=next_piece_expand,
    )
    lg(
        "INFO",
        f"\U0001f50d Recognition (transform: {tr['method']}, scale={tr['scale_x']:.3f}, "
        f"offset={int(tr['offset_x'])},{int(tr['offset_y'])})",
    )
    H, W = gray.shape[:2]
    return {
        "frame_bgra": frame_bgra,
        "gray": gray,
        "shapes": shapes,
        "tr": tr,
        "baseline_w": baseline_w,
        "baseline_h": baseline_h,
        "path": path,
        "H": H,
        "W": W,
    }


def run_object_recognition_roi_only(
    client_rect: Tuple[int, int, int, int],
    *,
    shapes_json: Optional[Path] = None,
    log: Optional[LogFn] = None,
    verbose_logs: bool = True,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    First pipeline stage only: one capture + per-shape ROI / contrast metrics.

    Use when you need ROI metrics from one frame and will run piece classification on a
    later capture so the client can repaint between stages.
    """
    lg = _sink_log_for_verbose(log, verbose_logs)
    if not NUMPY_OK:
        lg("ERROR", "numpy is required for object recognition. pip install numpy")
        return [], False
    if mss is None:
        lg("ERROR", "mss is required for object recognition. pip install mss")
        return [], False
    bundle = _capture_recognition_bundle(
        client_rect, shapes_json=shapes_json, lg=lg
    )
    if bundle is None:
        return [], False
    results = _accumulate_shape_roi_metrics(bundle, lg, log, verbose_logs)
    return results, True


def run_get_objects_pipeline(
    client_rect: Tuple[int, int, int, int],
    *,
    shapes_json: Optional[Path] = None,
    log: Optional[LogFn] = None,
    verbose_logs: bool = True,
) -> Tuple[List[Dict[str, Any]], bool, Dict[str, Any]]:
    """
    One mss capture: ROI stats for all shapes plus next-piece / current-piece color passes.

    Returns ``(results, ok, piece_info)``. When ``verbose_logs`` is False, routine INFO /
    SUCCESS lines are omitted (use for UI that formats its own report); ``log`` is still
    used for ``ERROR`` (and polygon warnings when verbose).

    Internally this is a single capture shared by both passes. For a fresh capture between
    ROI metrics and piece-color classification, run :func:`run_object_recognition_roi_only`
    then call this module's piece pass on a new capture from your UI (see ``piece_pass``).
    """
    lg = _sink_log_for_verbose(log, verbose_logs)
    if not NUMPY_OK:
        lg("ERROR", "numpy is required for object recognition. pip install numpy")
        return [], False, {}
    if mss is None:
        lg("ERROR", "mss is required for object recognition. pip install mss")
        return [], False, {}

    bundle = _capture_recognition_bundle(
        client_rect, shapes_json=shapes_json, lg=lg
    )
    if bundle is None:
        return [], False, {}
    results = _accumulate_shape_roi_metrics(bundle, lg, log, verbose_logs)
    piece_info = _run_piece_classification_pass(bundle, lg, log, verbose_logs)
    return results, True, piece_info


def capture_recognition_bundle_for_ui(
    client_rect: Tuple[int, int, int, int],
    *,
    shapes_json: Optional[Path] = None,
    log: Optional[LogFn] = None,
) -> Optional[Dict[str, Any]]:
    """
    Single mss capture + decoded shapes (BGRA frame, ``object_shapes`` path).

    For UI flows (e.g. guided color calibration) that need the raw frame without
    running the full shape-metrics pass.
    """
    lg = _sink_log_for_verbose(log, False)
    if not NUMPY_OK:
        lg("ERROR", "numpy is required for object recognition. pip install numpy")
        return None
    if mss is None:
        lg("ERROR", "mss is required for object recognition. pip install mss")
        return None
    return _capture_recognition_bundle(client_rect, shapes_json=shapes_json, lg=lg)
