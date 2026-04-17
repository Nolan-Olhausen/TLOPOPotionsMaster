"""
Strategy-agnostic piece color reads for brewing automation.

Parses ``piece_info`` from :func:`brew_object_recognition.run_get_objects_pipeline` into
:class:`AutomationPieceColors` (labels + ring medians for current hand + next queue). Hand
“settled” detection (swatch confidence vs calibrated ring medians) lives here so every board
strategy can share the same recognition rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

# Per-channel max delta vs saved ring medians (``ring_median_grid`` / ``piece_display_rgb``).
HAND_CALIBRATION_MATCH_MAX_DELTA = 14


@dataclass
class SlotColorRead:
    """One polygon slot: classifier label, optional ring median RGB, full classifier blob."""

    label: Optional[str] = None
    ring_rgb: Optional[Tuple[int, int, int]] = None
    classifier: Optional[Dict[str, Any]] = None


@dataclass
class AutomationPieceColors:
    """Normalized colors for automation: current pair (hand), next pair (queue), plus raw dict."""

    current_left: SlotColorRead
    current_right: SlotColorRead
    next_left: SlotColorRead
    next_right: SlotColorRead
    raw: Dict[str, Any]
    error: Optional[str] = None


def _triple_from_seq(seq: Any) -> Optional[Tuple[int, int, int]]:
    if not isinstance(seq, (list, tuple)) or len(seq) != 3:
        return None
    try:
        return int(seq[0]), int(seq[1]), int(seq[2])
    except (TypeError, ValueError):
        return None


def _slot_from_classifier_dict(
    d: Any, ring_rgb: Optional[Tuple[int, int, int]] = None
) -> SlotColorRead:
    if not isinstance(d, dict):
        return SlotColorRead(label=None, ring_rgb=ring_rgb, classifier=None)
    lab = d.get("label")
    lab_s = str(lab) if isinstance(lab, str) else None
    return SlotColorRead(label=lab_s, ring_rgb=ring_rgb, classifier=d)


def parse_automation_piece_colors(piece_info: Dict[str, Any]) -> AutomationPieceColors:
    """
    Build :class:`AutomationPieceColors` from a ``piece_info`` dict (classification pass output).

    Ring medians are attached for current and next slots when corresponding
    ``*_ring_rgb`` fields are present.
    """
    err_o = piece_info.get("error")
    err = str(err_o) if err_o is not None else None

    lr = _triple_from_seq(piece_info.get("current_left_ring_rgb"))
    rr = _triple_from_seq(piece_info.get("current_right_ring_rgb"))
    nlr = _triple_from_seq(piece_info.get("next_left_ring_rgb"))
    nrr = _triple_from_seq(piece_info.get("next_right_ring_rgb"))

    cl_d = piece_info.get("current_piece_left")
    cr_d = piece_info.get("current_piece_right")
    cur_l = _slot_from_classifier_dict(cl_d, ring_rgb=lr)
    cur_r = _slot_from_classifier_dict(cr_d, ring_rgb=rr)

    npi = piece_info.get("next_pieces") or {}
    if not isinstance(npi, dict):
        npi = {}
    nl_d = npi.get("next_piece_left")
    nr_d = npi.get("next_piece_right")
    nxl = _slot_from_classifier_dict(nl_d, ring_rgb=nlr)
    nxr = _slot_from_classifier_dict(nr_d, ring_rgb=nrr)

    return AutomationPieceColors(
        current_left=cur_l,
        current_right=cur_r,
        next_left=nxl,
        next_right=nxr,
        raw=piece_info,
        error=err,
    )


def automation_current_pair_labels(colors: AutomationPieceColors) -> Tuple[Optional[str], Optional[str]]:
    return colors.current_left.label, colors.current_right.label


def automation_next_pair_labels(colors: AutomationPieceColors) -> Tuple[Optional[str], Optional[str]]:
    return colors.next_left.label, colors.next_right.label


def _rgb_triple_nonzero(trip: Any) -> Optional[Tuple[int, int, int]]:
    if not isinstance(trip, (list, tuple)) or len(trip) != 3:
        return None
    try:
        r, g, b = int(trip[0]), int(trip[1]), int(trip[2])
    except (TypeError, ValueError):
        return None
    if (r | g | b) == 0:
        return None
    return r, g, b


def _slot_rgb_sources_from_ring_grid(
    ring_median_grid: Optional[Dict[str, Any]], slot_key: str
) -> Dict[str, Tuple[int, int, int]]:
    out: Dict[str, Tuple[int, int, int]] = {}
    if not ring_median_grid or not isinstance(ring_median_grid, dict):
        return out
    inner = ring_median_grid.get(slot_key)
    if not isinstance(inner, dict):
        return out
    for tok, trip in inner.items():
        if not isinstance(tok, str):
            continue
        t3 = _rgb_triple_nonzero(trip)
        if t3 is not None:
            out[tok] = t3
    return out


def _slot_rgb_sources_fallback_display(
    piece_display_rgb: Optional[Dict[str, Tuple[int, int, int]]],
) -> Dict[str, Tuple[int, int, int]]:
    out: Dict[str, Tuple[int, int, int]] = {}
    if not piece_display_rgb:
        return out
    for tok, trip in piece_display_rgb.items():
        if not isinstance(tok, str):
            continue
        t3 = _rgb_triple_nonzero(trip)
        if t3 is not None:
            out[tok] = t3
    return out


def _rgb_within_channel_max_delta(
    rgb: Tuple[int, int, int], target: Tuple[int, int, int], d: int
) -> bool:
    pr, pg, pb = target
    return (
        abs(rgb[0] - pr) <= d
        and abs(rgb[1] - pg) <= d
        and abs(rgb[2] - pb) <= d
    )


def _ring_median_matches_slot_sources(
    rgb: Tuple[int, int, int],
    classifier_label: Optional[str],
    slot_sources: Dict[str, Tuple[int, int, int]],
    *,
    per_channel_max_delta: int,
) -> bool:
    if not slot_sources:
        return False
    d = int(max(0, per_channel_max_delta))
    lab = str(classifier_label).strip() if classifier_label else ""
    if lab and lab != "Unknown" and lab in slot_sources:
        if _rgb_within_channel_max_delta(rgb, slot_sources[lab], d):
            return True
    for _tok, trip in slot_sources.items():
        if _rgb_within_channel_max_delta(rgb, trip, d):
            return True
    return False


def calibrated_label_for_slot_ring(
    slot_key: str,
    rgb: Optional[Tuple[int, int, int]],
    *,
    ring_median_grid: Optional[Dict[str, Dict[str, Tuple[int, int, int]]]] = None,
    piece_display_rgb: Optional[Dict[str, Tuple[int, int, int]]] = None,
    per_channel_max_delta: int = HAND_CALIBRATION_MATCH_MAX_DELTA,
) -> Optional[str]:
    """
    Best calibrated label for one slot ring median.

    Prefers per-slot ``ring_median_grid[slot_key]``; falls back to global
    ``piece_display_rgb``. Returns ``None`` when no candidate is within threshold.
    """
    if rgb is None:
        return None
    src = _slot_rgb_sources_from_ring_grid(ring_median_grid, slot_key)
    if not src:
        src = _slot_rgb_sources_fallback_display(piece_display_rgb)
    if not src:
        return None
    d = int(max(0, per_channel_max_delta))
    best_tok: Optional[str] = None
    best_score = 10**9
    for tok, trip in src.items():
        dr = abs(int(rgb[0]) - int(trip[0]))
        dg = abs(int(rgb[1]) - int(trip[1]))
        db = abs(int(rgb[2]) - int(trip[2]))
        if dr > d or dg > d or db > d:
            continue
        score = dr + dg + db
        if score < best_score:
            best_score = score
            best_tok = tok
    return best_tok


def ring_medians_match_hand_calibration(
    colors: AutomationPieceColors,
    *,
    cl: Optional[str] = None,
    cr: Optional[str] = None,
    ring_median_grid: Optional[Dict[str, Dict[str, Tuple[int, int, int]]]] = None,
    piece_display_rgb: Optional[Dict[str, Tuple[int, int, int]]] = None,
    per_channel_max_delta: int = HAND_CALIBRATION_MATCH_MAX_DELTA,
) -> bool:
    """
    True when left/right **current** ring medians match saved calibration (per-slot grid or
    global display RGB fallback).
    """
    lt = colors.current_left.ring_rgb
    rt = colors.current_right.ring_rgb
    if lt is None or rt is None:
        return False

    left_slot = _slot_rgb_sources_from_ring_grid(ring_median_grid, "current_piece_left")
    if not left_slot:
        left_slot = _slot_rgb_sources_fallback_display(piece_display_rgb)
    right_slot = _slot_rgb_sources_from_ring_grid(ring_median_grid, "current_piece_right")
    if not right_slot:
        right_slot = _slot_rgb_sources_fallback_display(piece_display_rgb)
    if not left_slot or not right_slot:
        return False

    return (
        _ring_median_matches_slot_sources(
            lt, cl, left_slot, per_channel_max_delta=per_channel_max_delta
        )
        and _ring_median_matches_slot_sources(
            rt, cr, right_slot, per_channel_max_delta=per_channel_max_delta
        )
    )


def automation_current_hand_read_looks_settled(
    colors: AutomationPieceColors,
    cl: Optional[str],
    cr: Optional[str],
    *,
    piece_display_rgb: Optional[Dict[str, Tuple[int, int, int]]] = None,
    ring_median_grid: Optional[Dict[str, Dict[str, Tuple[int, int, int]]]] = None,
    per_channel_max_delta: int = HAND_CALIBRATION_MATCH_MAX_DELTA,
) -> bool:
    """
    Strict mode: both current labels must be known and current ring medians must match
    calibrated values.
    """
    if not cl or not cr or cl == "Unknown" or cr == "Unknown":
        return False
    return ring_medians_match_hand_calibration(
        colors,
        cl=cl,
        cr=cr,
        ring_median_grid=ring_median_grid,
        piece_display_rgb=piece_display_rgb,
        per_channel_max_delta=per_channel_max_delta,
    )
