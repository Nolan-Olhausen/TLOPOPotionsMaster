"""
Port Royal board automation helpers: column tokens, drop-slot lookup, and Win32 mouse moves.

Piece labels must be single-letter ``R`` / ``G`` / ``B`` for column matching (same as
``brew_next_pieces`` primary tokens on the Port Royal palette).

Drop planning matches ``oldBot/planner.py`` ``plan_drop`` for ``port_royal``: try the vision
order first, then the swapped order, preferring the leftmost slot; ``needs_swap`` means
perform an in-game right-click at the hand rest (parking) before dropping, as the old bot did.

Automation loop (GUI): move to parking → poll until neither hand ring median sits inside a **tight
per-channel box** around guided empty-board RGB → capture → read settled pair → plan drop /
optional R-click at parking → left-click drop → ``automation_delay_s`` (same as oldBot ``run.py --delay``,
idle after the drop before the next cycle) → repeat.

Mouse pacing matches ``oldBot/run.py`` / ``oldBot/config_loader.py``: ``action_delay_sec`` (0.2s)
after swap and after moving to the placement before the left click. After the drop, the cursor returns
to parking and ``PORT_ROYAL_POST_DROP_SLEEP_SEC`` is used like ``post_place_sleep_sec`` at the hand rest,
then ``automation_delay_s`` (``--delay``) before the next cycle.
"""

from __future__ import annotations

import ctypes
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import variables.global_variables as gv

# Re-export for ``automation.flow`` (``import brew_core.port_royal_automation as pra``).
from brew_core.automation_color_recognition import (
    automation_current_hand_read_looks_settled,
    automation_current_pair_labels,
    automation_next_pair_labels,
    calibrated_label_for_slot_ring,
    parse_automation_piece_colors,
)

# Columns 1–8 (1-based) = R R R B B G G R — indices 0..7 here.
PORT_ROYAL_COLUMN_TOKENS: Tuple[str, ...] = ("R", "R", "R", "B", "B", "G", "G", "R")
ISLAND_BOARD_COLUMN_TOKENS: Dict[str, Tuple[str, ...]] = {
    "port_royal": PORT_ROYAL_COLUMN_TOKENS,
    "cuba": ("P", "R", "B", "P", "G", "B", "R", "G"),
    "tortuga": ("Grey", "R", "B", "Grey", "G", "B", "R", "G"),
    "padres": ("O", "R", "B", "O", "G", "B", "R", "G"),
}

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

# oldBot timing defaults: leave enough time for cursor settle and click registration.
PORT_ROYAL_ACTION_DELAY_SEC = float(gv.BREW_AUTOMATION_ACTION_DELAY_DEFAULT_S)
PORT_ROYAL_FOREGROUND_SETTLE_SEC = float(gv.BREW_AUTOMATION_FOREGROUND_SETTLE_DEFAULT_S)
PORT_ROYAL_POST_DROP_SLEEP_SEC = float(gv.BREW_AUTOMATION_POST_DROP_SLEEP_DEFAULT_S)
PORT_ROYAL_PRE_CLICK_SETTLE_SEC = float(gv.BREW_AUTOMATION_PRE_CLICK_SETTLE_DEFAULT_S)
# Tiny hold after click before moving away; helps UI buttons register on slower frames.
PORT_ROYAL_POST_CLICK_SETTLE_SEC = float(gv.BREW_AUTOMATION_POST_CLICK_SETTLE_DEFAULT_S)

# After merges, the hand ROI can briefly show board (brown) and classify as ``O``; require
# confident ring fractions plus two matching polls (see ``brew_automation_color_recognition``).
HAND_POLL_INTERVAL_MS = int(gv.BREW_AUTOMATION_HAND_POLL_INTERVAL_DEFAULT_MS)
HAND_POLL_MAX_ATTEMPTS = 55

# Empty-board wait: ring median counts as "still bare board" only if **each** R,G,B channel is
# within this many levels of guided ``board_await_*`` (wizard / config panel — same pipeline as
# ring sample). Avoids Euclidean "near brown" false positives (e.g. RR pairs still within a large RGB ball).
PORT_ROYAL_EMPTY_BOARD_PER_CHANNEL_MAX_DELTA = 8
# After parking, poll until both hand rings leave that tight box (merge / pair off-screen).
BOARD_WAIT_POLL_INTERVAL_MS = int(gv.BREW_AUTOMATION_BOARD_WAIT_POLL_INTERVAL_DEFAULT_MS)
BOARD_WAIT_MAX_ATTEMPTS = 140


def norm_piece_token_for_port_royal(label: str) -> Optional[str]:
    """Return ``R``, ``G``, or ``B`` if the label is already a Port Royal column token; else ``None``."""
    if not label:
        return None
    x = str(label).strip()
    if x in ("R", "G", "B"):
        return x
    return None


def port_royal_column_token_from_piece_label(label: str) -> Optional[str]:
    """
    Map a **classifier** label (``brew_next_pieces``) to ``R`` / ``G`` / ``B`` for column lookup.

    The Port Royal board is only RRRBBGGR. The recognizer also emits ``O`` (orange), ``P``
    (purple), ``Grey``, etc. For automation we fold extras into the nearest column family:
    ``O`` → ``R`` (warm / red stack), ``P`` → ``B`` (cool / blue stack). ``Grey`` and anything
    else unknown stay ``None`` so the caller can retry or tune swatches.
    """
    base = norm_piece_token_for_port_royal(label)
    if base is not None:
        return base
    key = str(label or "").strip()
    if not key:
        return None
    u = key.upper()
    if u == "O":
        return "R"
    if u == "P":
        return "B"
    if u in ("GREY", "GRAY") or key.casefold() == "grey":
        return None
    return None


def plan_port_royal_drop_slot(left: str, right: str) -> Tuple[Optional[int], bool]:
    """
    Same rule as ``oldBot.planner.plan_drop`` for Port Royal.

    Returns ``(slot_1based, needs_swap)`` where ``slot_1based`` is 1..7 (left column of the
    adjacent pair) or ``None`` if no RGB column pair matches. ``needs_swap`` is ``True`` when
    the match required treating the right-hand vision gem as dropping first (in-game flip).
    """
    vl = port_royal_column_token_from_piece_label(left)
    vr = port_royal_column_token_from_piece_label(right)
    if vl is None or vr is None:
        return None, False
    cols = PORT_ROYAL_COLUMN_TOKENS
    for swap in (False, True):
        first, second = (vr, vl) if swap else (vl, vr)
        for p in range(7):
            if cols[p] == first and cols[p + 1] == second:
                return p + 1, swap
    return None, False


def normalize_island_piece_token(label: str) -> Optional[str]:
    """Normalize a classifier label to canonical board-rule tokens for island planners."""
    if not label:
        return None
    key = str(label).strip()
    if not key:
        return None
    u = key.upper()
    if u == "R":
        return "R"
    if u == "G":
        return "G"
    if u == "B":
        return "B"
    if u == "O":
        return "O"
    if u == "P":
        return "P"
    if u in ("GREY", "GRAY") or key.casefold() in ("grey", "gray", "black"):
        return "Grey"
    return None


def board_tokens_for_island(island_slug: str | None) -> Tuple[str, ...]:
    """Return 8 board-rule column tokens for a potion island."""
    k = str(island_slug or "").strip().lower()
    if not k:
        k = "port_royal"
    return ISLAND_BOARD_COLUMN_TOKENS.get(k, PORT_ROYAL_COLUMN_TOKENS)


def plan_island_exact_drop_slot(
    left: str,
    right: str,
    *,
    island_slug: str | None,
) -> Tuple[Optional[int], bool]:
    """
    Exact board-rule planner for any supported island.

    Returns ``(slot_1based, needs_swap)`` with the same semantics as
    ``plan_port_royal_drop_slot``.
    """
    vl = normalize_island_piece_token(left)
    vr = normalize_island_piece_token(right)
    if vl is None or vr is None:
        return None, False
    cols = board_tokens_for_island(island_slug)
    for swap in (False, True):
        first, second = (vr, vl) if swap else (vl, vr)
        for p in range(7):
            if cols[p] == first and cols[p + 1] == second:
                return p + 1, swap
    return None, False


def find_object_center(
    results: List[Dict[str, Any]], label: str
) -> Optional[Tuple[float, float]]:
    for r in results:
        if str(r.get("label", "")) == label:
            cx = r.get("cx")
            cy = r.get("cy")
            if isinstance(cx, (int, float)) and isinstance(cy, (int, float)):
                return float(cx), float(cy)
    return None


def sorted_drop_labels_by_cx(results: List[Dict[str, Any]]) -> List[str]:
    """``drop_*`` labels sorted left-to-right by ROI center (same order as the Brewing log)."""
    items: List[Tuple[float, str]] = []
    for r in results:
        lab = str(r.get("label", ""))
        if not lab.lower().startswith("drop_"):
            continue
        cx = r.get("cx")
        if not isinstance(cx, (int, float)):
            continue
        cy = r.get("cy")
        fy = float(cy) if isinstance(cy, (int, float)) else 0.0
        items.append((float(cx) + 1e-6 * fy, lab))
    items.sort(key=lambda t: t[0])
    return [lab for _, lab in items]


def client_xy_to_screen(
    client_rect: Tuple[int, int, int, int], cx: float, cy: float
) -> Tuple[int, int]:
    """Client-space ``(cx, cy)`` from recognition → screen pixels using ``(l,t,r,b)`` client rect."""
    l, t, _, _ = client_rect
    return int(round(l + cx)), int(round(t + cy))


def win32_move_cursor_screen(sx: int, sy: int) -> bool:
    if sys.platform != "win32":
        return False
    return bool(ctypes.windll.user32.SetCursorPos(int(sx), int(sy)))


def win32_left_click_at_screen(
    sx: int,
    sy: int,
    *,
    settle_s: float = 0.04,
    pre_click_settle_s: float | None = None,
) -> None:
    """Move to screen point and send a left-button click (down + up)."""
    if sys.platform != "win32":
        return
    u = ctypes.windll.user32
    u.SetCursorPos(int(sx), int(sy))
    if settle_s > 0:
        time.sleep(settle_s)
    win32_left_click_at_current_pos(pre_click_settle_s=pre_click_settle_s)


def win32_left_click_at_current_pos(*, pre_click_settle_s: float | None = None) -> None:
    """Left mouse down + up at the current cursor (``oldBot`` does move, delay, then click)."""
    if sys.platform != "win32":
        return
    u = ctypes.windll.user32
    settle = (
        float(PORT_ROYAL_PRE_CLICK_SETTLE_SEC)
        if pre_click_settle_s is None
        else max(0.0, float(pre_click_settle_s))
    )
    if settle > 0:
        time.sleep(settle)
    u.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    u.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def win32_right_click_at_screen(
    sx: int,
    sy: int,
    *,
    settle_s: float = 0.04,
    pre_click_settle_s: float | None = None,
) -> None:
    """Move to screen point and send a right-button click (hand flip at parking)."""
    if sys.platform != "win32":
        return
    u = ctypes.windll.user32
    u.SetCursorPos(int(sx), int(sy))
    if settle_s > 0:
        time.sleep(settle_s)
    settle = (
        float(PORT_ROYAL_PRE_CLICK_SETTLE_SEC)
        if pre_click_settle_s is None
        else max(0.0, float(pre_click_settle_s))
    )
    if settle > 0:
        time.sleep(settle)
    u.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    u.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


def ring_rgb_matches_empty_board_calibration(
    ring: Tuple[int, ...],
    board_r: int,
    board_g: int,
    board_b: int,
    *,
    per_channel_max_delta: int = PORT_ROYAL_EMPTY_BOARD_PER_CHANNEL_MAX_DELTA,
) -> bool:
    """True when ring median RGB sits inside the axis-aligned box around guided empty-board RGB."""
    if len(ring) != 3:
        return False
    r, g, b = int(ring[0]), int(ring[1]), int(ring[2])
    br, bg, bb = int(board_r), int(board_g), int(board_b)
    d = int(max(0, per_channel_max_delta))
    return (
        abs(r - br) <= d
        and abs(g - bg) <= d
        and abs(b - bb) <= d
    )


def current_pair_rings_not_empty_board(
    piece_info: Dict[str, Any],
    board_r: int,
    board_g: int,
    board_b: int,
    *,
    per_channel_max_delta: int = PORT_ROYAL_EMPTY_BOARD_PER_CHANNEL_MAX_DELTA,
) -> bool:
    """
    True when **neither** hand ring median sits inside the tight per-channel box around
    ``board_await_*`` from settings. If ring samples are missing (split-area path, etc.),
    returns True so automation can fall back to classifier-only logic.
    """
    lr = piece_info.get("current_left_ring_rgb")
    rr = piece_info.get("current_right_ring_rgb")
    if not isinstance(lr, (list, tuple)) or not isinstance(rr, (list, tuple)):
        return True
    if len(lr) != 3 or len(rr) != 3:
        return True
    lt = tuple(int(x) for x in lr)
    rt = tuple(int(x) for x in rr)
    if ring_rgb_matches_empty_board_calibration(
        lt, board_r, board_g, board_b, per_channel_max_delta=per_channel_max_delta
    ):
        return False
    if ring_rgb_matches_empty_board_calibration(
        rt, board_r, board_g, board_b, per_channel_max_delta=per_channel_max_delta
    ):
        return False
    return True
