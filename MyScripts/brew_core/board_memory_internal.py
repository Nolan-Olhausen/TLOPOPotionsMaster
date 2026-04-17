"""Internalized per-round move memory (formerly from ``oldBot/board_memory.py``)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BoardMemory:
    moves: list[tuple[int, str, str, bool, str]] = field(default_factory=list)

    def reset(self) -> None:
        self.moves.clear()

    def record(
        self,
        placement: int,
        left: str,
        right: str,
        swapped: bool,
        plan_kind: str = "exact",
    ) -> None:
        self.moves.append((placement, left, right, swapped, plan_kind))

    def last_n(self, n: int = 12) -> list[tuple[int, str, str, bool, str]]:
        return self.moves[-n:]
