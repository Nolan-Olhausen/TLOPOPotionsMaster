"""
Board memory + physics used by automation and ROI fallback planning.

Primary source is the internalized simulator under ``MyScripts/brew_core`` so release builds
do not depend on sibling folders. Vision tokens (R / G / B / O / P / Grey) are mapped to
planner / BoardSim color names.
"""

from __future__ import annotations

from typing import Any


BoardSim: Any = None
BoardMemory: Any = None
ROWS: int = 10
COLS: int = 8
_LOAD_ERROR: str | None = None

try:
    from brew_core.board_sim_internal import BoardSim as _BoardSim, ROWS as _ROWS, COLS as _COLS
    from brew_core.board_memory_internal import BoardMemory as _BoardMemory

    BoardSim = _BoardSim
    BoardMemory = _BoardMemory
    ROWS = int(_ROWS)
    COLS = int(_COLS)
except Exception as e:  # noqa: BLE001 — keep GUI alive without board memory
    _LOAD_ERROR = str(e)
    BoardSim = None
    BoardMemory = None


def board_memory_available() -> bool:
    return BoardSim is not None and BoardMemory is not None


def vision_label_to_sim_line(label: str) -> str | None:
    """
    Map a calibrated vision label to a ``board_sim.Gem`` color string
    (``red`` / ``green`` / ``blue`` / ``orange`` / ``purple`` / ``grey``).
    """
    if not label:
        return None
    t = str(label).strip()
    u = t.upper()
    if u == "R" or t.casefold() == "red":
        return "red"
    if u == "G" or t.casefold() == "green":
        return "green"
    if u == "B" or t.casefold() == "blue":
        return "blue"
    if u == "O" or t.casefold() == "orange":
        return "orange"
    if u == "P" or t.casefold() == "purple":
        return "purple"
    if u in ("GREY", "GRAY") or t.casefold() == "grey":
        return "grey"
    if t.casefold() in ("gray", "black"):
        return "grey"
    return None


def drop_colors_for_place_pair(
    v_left: str, v_right: str, *, auto_swap: bool
) -> tuple[str, str] | None:
    """
    ``(a, b)`` for ``BoardSim.place_pair_and_resolve(p, a, b)`` — gem at column ``p`` then ``p+1``.
    Same ordering as ``oldBot/run.py``: ``a, b = (right_line, left_line) if swap else (left_line, right_line)``.
    """
    sl = vision_label_to_sim_line(v_left)
    sr = vision_label_to_sim_line(v_right)
    if sl is None or sr is None:
        return None
    if auto_swap:
        return sr, sl
    return sl, sr


def sim_rc_to_hex_cell(board_r: int, board_c: int) -> tuple[int, int] | None:
    """
    BoardSim uses ``grid[board_r][board_c]`` with ``board_r=0`` at the floor and ``board_r=9`` at spawn.
    Hex UI uses ``(cc, rr)`` with ``rr=0`` at the top of the overlay — map with ``rr = ROWS-1-board_r``.
    """
    if board_r < 0 or board_r >= ROWS or board_c < 0 or board_c >= COLS:
        return None
    return board_c, ROWS - 1 - board_r


def apply_recipe_consumption_from_catalog(
    sim: Any,
    potion: dict[str, Any],
    ingredient_done: list[bool],
) -> int:
    """
    oldBot ``apply_potion_recipe_consumption`` semantics for app catalog dicts:
    scan columns left->right, rows bottom->top; each cell can satisfy one unfinished
    ingredient with exact (color, level).
    """
    ings = potion.get("ingredients") if isinstance(potion, dict) else None
    if not isinstance(ings, list):
        return 0
    if len(ingredient_done) != len(ings):
        raise ValueError("ingredient_done length must match potion ingredients length")
    cleared = 0
    for c in range(COLS):
        for r in range(ROWS):
            cell = sim.grid[r][c]
            if cell is None:
                continue
            color = str(getattr(cell, "color", "") or "").strip().lower()
            level = int(getattr(cell, "level", 0) or 0)
            for i, ing in enumerate(ings):
                if ingredient_done[i] or not isinstance(ing, dict):
                    continue
                ing_color = str(ing.get("color") or "").strip().lower()
                if ing_color == "black":
                    ing_color = "grey"
                if ing_color == "gray":
                    ing_color = "grey"
                try:
                    ing_level = int(ing.get("level", 0))
                except (TypeError, ValueError):
                    ing_level = 0
                if ing_color == color and ing_level == level:
                    sim.grid[r][c] = None
                    ingredient_done[i] = True
                    cleared += 1
                    break
    if cleared:
        sim.compact_all()
    return cleared


def settle_merges_and_recipe_from_catalog(
    sim: Any,
    potion: dict[str, Any] | None,
    ingredient_done: list[bool],
) -> int:
    """
    oldBot ``settle_merges_and_recipe`` loop for app catalog dicts.
    Returns total newly-completed ingredients this post-drop settle.
    """
    if not isinstance(potion, dict):
        return 0
    ings = potion.get("ingredients")
    if not isinstance(ings, list) or not ings:
        return 0
    total = 0
    while True:
        n = apply_recipe_consumption_from_catalog(sim, potion, ingredient_done)
        if n == 0:
            break
        total += n
        carry_t = int(getattr(sim.last_stats, "triples", 0))
        carry_q = int(getattr(sim.last_stats, "quads", 0))
        sim.resolve_all_merges()
        sim.last_stats.triples += carry_t
        sim.last_stats.quads += carry_q
    return total
