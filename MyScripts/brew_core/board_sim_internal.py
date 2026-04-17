"""
Internalized board simulator formerly loaded from ``oldBot/board_sim.py``.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from functools import cmp_to_key
from typing import Any, Optional

_COL_X_SCALE = 0.1392
_ROW_Y_SCALE = 0.1616
_ROW_Y_EVEN_COL_OFFSET = 0.0808


def piece_screen_xy(column: int, row: int) -> tuple[float, float]:
    x = column * _COL_X_SCALE
    y = row * _ROW_Y_SCALE + (_ROW_Y_EVEN_COL_OFFSET if column % 2 == 0 else 0.0)
    return (x, y)


@dataclass
class Gem:
    color: str
    level: int


Cell = Optional[Gem]

ROWS = 10
COLS = 8
_SPAWN_R = ROWS - 1
_SUPPORT_R = ROWS - 2
_MAX_SETTLED_R = ROWS - 2


def column_accepts_pair_hex(sim: "BoardSim", c: int) -> bool:
    if c < 0 or c >= COLS:
        return False
    return sim.grid[_SUPPORT_R][c] is None


def columns_clear_for_pair_drop(sim: "BoardSim", p: int) -> bool:
    if p < 0 or p >= COLS - 1:
        return False
    return column_accepts_pair_hex(sim, p) and column_accepts_pair_hex(sim, p + 1)


def hex_neighbors(r: int, c: int) -> list[tuple[int, int]]:
    n: list[tuple[int, int]] = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        r2, c2 = r + dr, c + dc
        if 0 <= r2 < ROWS and 0 <= c2 < COLS:
            n.append((r2, c2))
    if c % 2 == 0:
        for dr, dc in ((1, -1), (1, 1)):
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < ROWS and 0 <= c2 < COLS:
                n.append((r2, c2))
    else:
        for dr, dc in ((-1, -1), (-1, 1)):
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < ROWS and 0 <= c2 < COLS:
                n.append((r2, c2))
    return n


def _cmp_merge_game(
    a: tuple[int, int],
    b: tuple[int, int],
    deg: dict[tuple[int, int], int],
) -> int:
    ar, ac = a
    br, bc = b
    d1, d2 = deg[a], deg[b]
    if d1 != d2:
        return (d2 > d1) - (d2 < d1)
    xa, ya = piece_screen_xy(ac, ar)
    xb, yb = piece_screen_xy(bc, br)
    if ya != yb:
        return (ya > yb) - (ya < yb)
    return (xa > xb) - (xa < xb)


@dataclass
class MergeStats:
    triples: int = 0
    quads: int = 0


class BoardSim:
    def __init__(self) -> None:
        self.grid: list[list[Cell]] = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.last_stats = MergeStats()

    def clone(self) -> "BoardSim":
        o = BoardSim()
        o.grid = copy.deepcopy(self.grid)
        return o

    def compact_column(self, c: int) -> None:
        stack: list[Gem] = []
        for r in range(ROWS):
            if self.grid[r][c] is not None:
                stack.append(self.grid[r][c])  # type: ignore
        for r in range(ROWS):
            self.grid[r][c] = None
        for i, cell in enumerate(stack):
            if i > _MAX_SETTLED_R:
                break
            self.grid[i][c] = cell

    def compact_all(self) -> None:
        for c in range(COLS):
            self.compact_column(c)

    def can_place_pair(self, p: int, left: str, right: str) -> bool:
        return columns_clear_for_pair_drop(self, p)

    def place_pair_raw(self, p: int, left: str, right: str) -> bool:
        if not self.can_place_pair(p, left, right):
            return False
        self.grid[_SPAWN_R][p] = Gem(left, 1)
        self.grid[_SPAWN_R][p + 1] = Gem(right, 1)
        self.compact_all()
        return True

    def _neighbor_match_deg(self, r: int, c: int, color: str, level: int) -> int:
        n = 0
        for nr, nc in hex_neighbors(r, c):
            g = self.grid[nr][nc]
            if g is not None and g.color == color and g.level == level:
                n += 1
        return n

    def _find_clusters(self) -> list[set[tuple[int, int]]]:
        global_seen: set[tuple[int, int]] = set()
        clusters: list[set[tuple[int, int]]] = []
        for c in range(COLS):
            for r in range(ROWS):
                if (r, c) in global_seen or self.grid[r][c] is None:
                    continue
                g0 = self.grid[r][c]
                assert g0 is not None
                color, level = g0.color, g0.level
                comp: set[tuple[int, int]] = set()
                stack = [(r, c)]
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in comp:
                        continue
                    v = self.grid[cr][cc]
                    if v is None or v.color != color or v.level != level:
                        continue
                    comp.add((cr, cc))
                    for nr, nc in hex_neighbors(cr, cc):
                        nv = self.grid[nr][nc]
                        if nv is not None and nv.color == color and nv.level == level:
                            if (nr, nc) not in comp:
                                stack.append((nr, nc))
                if len(comp) >= 3:
                    clusters.append(comp)
                    global_seen |= comp
        return clusters

    def _apply_merge_tick(self, clusters: list[set[tuple[int, int]]]) -> None:
        gems_remove: set[int] = set()
        gems_upgrade: list[Gem] = []
        for cluster in clusters:
            rc_list = list(cluster)
            g0 = self.grid[rc_list[0][0]][rc_list[0][1]]
            assert g0 is not None
            color, level = g0.color, g0.level
            n = len(rc_list)
            if n < 3:
                continue
            deg = {rc: self._neighbor_match_deg(rc[0], rc[1], color, level) for rc in rc_list}
            key = cmp_to_key(lambda a, b: _cmp_merge_game(a, b, deg))
            ordered = sorted(rc_list, key=key, reverse=True)
            first_rc = ordered[0]
            rest = [rc for rc in rc_list if rc != first_rc]
            ordered2 = sorted(rest, key=key, reverse=True)
            second_rc = ordered2[0]
            for rc in (first_rc, second_rc):
                g = self.grid[rc[0]][rc[1]]
                assert g is not None
                gems_remove.add(id(g))
            for rc in rc_list:
                if rc in (first_rc, second_rc):
                    continue
                g = self.grid[rc[0]][rc[1]]
                assert g is not None
                if g.level < 6:
                    gems_upgrade.append(g)
                else:
                    gems_remove.add(id(g))
            if n >= 4:
                self.last_stats.quads += 1
            else:
                self.last_stats.triples += 1
        for r in range(ROWS):
            for c in range(COLS):
                g = self.grid[r][c]
                if g is not None and id(g) in gems_remove:
                    self.grid[r][c] = None
        self.compact_all()
        for g in gems_upgrade:
            g.level += 1

    def resolve_merges_once(self) -> bool:
        clusters = self._find_clusters()
        if not clusters:
            return False
        self._apply_merge_tick(clusters)
        return True

    def resolve_all_merges(self) -> MergeStats:
        self.last_stats = MergeStats()
        while self.resolve_merges_once():
            pass
        return self.last_stats

    def place_pair_and_resolve(self, p: int, left: str, right: str) -> MergeStats:
        if not self.place_pair_raw(p, left, right):
            return MergeStats()
        return self.resolve_all_merges()

    def score_heuristic(self) -> float:
        h = 0.0
        for c in range(COLS):
            for r in range(ROWS):
                if self.grid[r][c]:
                    h += float(r)
        m = self.last_stats.triples * 4.0 + self.last_stats.quads * 8.0
        return h - m

    def to_api_grid(self) -> list[list[Optional[dict[str, Any]]]]:
        out: list[list[Optional[dict[str, Any]]]] = []
        for r in range(ROWS - 1, -1, -1):
            row: list[Optional[dict[str, Any]]] = []
            for c in range(COLS):
                cell = self.grid[r][c]
                if cell is None:
                    row.append(None)
                else:
                    row.append({"color": cell.color, "level": cell.level})
            out.append(row)
        return out
