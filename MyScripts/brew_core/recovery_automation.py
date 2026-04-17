"""
Fail-state recovery: in-game potion list scroll math and shape label helpers.

The catalog order in ``potions/catalog.json`` matches the in-game list top-to-bottom.
``potion_list_down`` advances the first visible row by 2 until the last step, which
advances by 1 so the final potion can sit on ``potion_list_row_23`` (verified for 52
potions: 15 downs to show ``Mejor Muertos Mojito`` on row 23).
"""

from __future__ import annotations

from collections import deque

VISIBLE_LIST_ROWS = 23


def scroll_down_new_top(top: int, max_top: int) -> int:
    """One in-game ``potion_list_down`` click: +2 while possible, else +1 to ``max_top``."""
    if top >= max_top:
        return top
    if top + 2 <= max_top:
        return top + 2
    return top + 1


def min_scroll_clicks_to_top(goal_top: int, max_top: int) -> int | None:
    """Minimum ``potion_list_down`` clicks to reach ``goal_top`` from list top (0)."""
    if goal_top < 0 or goal_top > max_top:
        return None
    if goal_top == 0:
        return 0
    q: deque[tuple[int, int]] = deque([(0, 0)])
    seen = {0}
    while q:
        top, d = q.popleft()
        nt = scroll_down_new_top(top, max_top)
        if nt == goal_top:
            return d + 1
        if nt not in seen and nt > top:
            seen.add(nt)
            q.append((nt, d + 1))
    return None


def plan_potion_list_scroll(
    target_index: int, num_potions: int
) -> tuple[int, int, int]:
    """
    Minimum scrolls and row to click for a0-based catalog index.

    Returns ``(down_clicks, row_1based, final_top_index)``.
    """
    if num_potions <= 0:
        return 0, 1, 0
    ti = max(0, min(target_index, num_potions - 1))
    max_top = max(0, num_potions - VISIBLE_LIST_ROWS)
    low = max(0, ti - (VISIBLE_LIST_ROWS - 1))
    high = min(ti, max_top)
    best: tuple[int, int] | None = None
    for T in range(low, high + 1):
        clicks = min_scroll_clicks_to_top(T, max_top)
        if clicks is None:
            continue
        if best is None or clicks < best[0] or (clicks == best[0] and T < best[1]):
            best = (clicks, T)
    if best is None:
        T = min(max(ti, 0), max_top)
        c = min_scroll_clicks_to_top(T, max_top) or 0
        best = (c, T)
    clicks, final_top = best
    row = ti - final_top + 1
    row = max(1, min(VISIBLE_LIST_ROWS, row))
    return clicks, row, final_top


def potion_list_row_label(row_1based: int) -> str:
    return f"potion_list_row_{int(row_1based)}"
