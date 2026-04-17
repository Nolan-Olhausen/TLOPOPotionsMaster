from __future__ import annotations

from core_helpers import brew_choice_is_board_rule, potion_supports_port_royal_column_board_rule
from hexGrid.hex_grid import BREW_BOARD_HEX_GRID, compute_hex_cell_outline_colors_for_palette
import variables.global_variables as gv


def _sync_board_strategy_hex_fills(self) -> None:
    """Clear hex styling, then set island board-rule column outlines when active."""
    self._hex_cell_fill_colors.clear()
    self._hex_cell_outline_colors.clear()
    if self._view != "game" or not self.potions:
        return
    idx = max(0, min(self._current_potion_index, len(self.potions) - 1))
    potion = self.potions[idx]
    if not brew_choice_is_board_rule(potion, self._brew_strategy_choice):
        return
    if not potion_supports_port_royal_column_board_rule(potion):
        return
    island = str((potion or {}).get("island") or "").strip().lower()
    if island == "cuba":
        pal = gv.ISLAND_CUBA_BOARD_COLUMN_HEX
    elif island == "tortuga":
        pal = gv.ISLAND_TORTUGA_BOARD_COLUMN_HEX
    elif island == "padres":
        pal = gv.ISLAND_PADRES_BOARD_COLUMN_HEX
    else:
        pal = gv.PORT_ROYAL_BOARD_COLUMN_HEX
    self._hex_cell_outline_colors.update(
        compute_hex_cell_outline_colors_for_palette(BREW_BOARD_HEX_GRID, pal)
    )
