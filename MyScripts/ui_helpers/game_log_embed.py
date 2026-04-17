from __future__ import annotations

import tkinter as tk


def _destroy_game_log_embed(self) -> None:
    """Destroy the log ``Toplevel`` (and its child ``Text`` / frames)."""
    top = getattr(self, "_game_log_top", None)
    if top is not None:
        try:
            top.destroy()
        except tk.TclError:
            pass
        self._game_log_top = None
    self._game_log_shell = None
    self._game_log_txt = None


def _game_log_text_key_guard(event: tk.Event) -> str | None:
    """Read-only log: allow navigation, selection modifiers, and Ctrl+C / Ctrl+A / Ctrl+Insert."""
    if event.state & 0x4 and event.keysym.lower() in ("c", "a", "insert"):
        return None
    if event.keysym in (
        "Left",
        "Right",
        "Up",
        "Down",
        "Home",
        "End",
        "Prior",
        "Next",
        "Shift_L",
        "Shift_R",
        "Control_L",
        "Control_R",
        "Alt_L",
        "Alt_R",
        "Caps_Lock",
        "Num_Lock",
        "Escape",
    ):
        return None
    if len(event.keysym) > 1 and event.keysym.startswith("F") and event.keysym[1:].isdigit():
        return None
    return "break"


def _sync_game_log_text_body(self) -> None:
    """Refresh log ``Text`` from ``_game_log_lines`` without rebuilding the panel chrome."""
    w = self._game_log_txt
    if not w or not w.winfo_exists():
        self._draw_game_log_layer()
        top = getattr(self, "_game_log_top", None)
        if top is not None:
            try:
                if top.winfo_exists():
                    top.lift()
            except tk.TclError:
                pass
        return
    body = "\n".join(self._game_log_lines)
    if not body:
        body = "(no messages yet)"
    w.delete("1.0", tk.END)
    w.insert(tk.END, body)
    w.see(tk.END)
    top = getattr(self, "_game_log_top", None)
    if top is not None:
        try:
            if top.winfo_exists():
                top.lift()
        except tk.TclError:
            pass
