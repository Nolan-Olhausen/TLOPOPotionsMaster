from __future__ import annotations

import tkinter as tk

import variables.global_variables as gv


def _brew_again_color_matches(self, rgb: tuple[int, int, int] | None) -> bool:
    if rgb is None:
        return False
    tr = int(self._brew_again_r)
    tg = int(self._brew_again_g)
    tb = int(self._brew_again_b)
    if (tr | tg | tb) == 0:
        return False
    rr, gg, bb = int(rgb[0]), int(rgb[1]), int(rgb[2])
    d = int(max(0, gv.BREW_AGAIN_PER_CHANNEL_MAX_DELTA))
    return abs(rr - tr) <= d and abs(gg - tg) <= d and abs(bb - tb) <= d


def _brew_again_ok_color_matches(self, rgb: tuple[int, int, int] | None) -> bool:
    if rgb is None:
        return False
    tr = int(self._brew_again_ok_r)
    tg = int(self._brew_again_ok_g)
    tb = int(self._brew_again_ok_b)
    if (tr | tg | tb) == 0:
        return False
    rr, gg, bb = int(rgb[0]), int(rgb[1]), int(rgb[2])
    d = int(max(0, gv.BREW_AGAIN_PER_CHANNEL_MAX_DELTA))
    return abs(rr - tr) <= d and abs(gg - tg) <= d and abs(bb - tb) <= d


def _potion_failed_continue_color_matches(self, rgb: tuple[int, int, int] | None) -> bool:
    if rgb is None:
        return False
    tr = int(self._potion_failed_continue_r)
    tg = int(self._potion_failed_continue_g)
    tb = int(self._potion_failed_continue_b)
    if (tr | tg | tb) == 0:
        return False
    rr, gg, bb = int(rgb[0]), int(rgb[1]), int(rgb[2])
    d = int(max(0, gv.BREW_AGAIN_PER_CHANNEL_MAX_DELTA))
    return abs(rr - tr) <= d and abs(gg - tg) <= d and abs(bb - tb) <= d


def _brew_automation_hotkey_entry_ok(self, widget: tk.Misc) -> bool:
    """
    False when focus is in a text field so Left Ctrl doesn't toggle automation while typing.
    """
    try:
        wclass = widget.winfo_class()
    except tk.TclError:
        return False
    return wclass not in ("Text", "Entry", "TEntry", "Spinbox")
