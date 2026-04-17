from __future__ import annotations

import tkinter as tk


def _on_global_bare_ctrl_toggle(self) -> None:
    if self._view != "game":
        return
    try:
        fw = self.root.focus_get()
    except tk.TclError:
        fw = None
    if fw is not None and not self._brew_automation_hotkey_entry_ok(fw):
        return
    self._brew_automation_toggle_from_hotkey()


def _brew_automation_toggle_from_hotkey(self) -> None:
    if self._brew_automation_running:
        self._brew_automation_stop("Left Ctrl")
    else:
        if not self._brew_automation_prereqs_ok():
            return
        self._brew_automation_start()


def _brew_automation_hotkey_stop(self) -> None:
    h = self._brew_automation_hotkey_listener
    self._brew_automation_hotkey_listener = None
    if h is not None:
        h.stop()


def _brew_automation_hotkey_start(self) -> None:
    if self._brew_automation_hotkey_listener is not None:
        return
    try:
        from brew_core.automation_hotkey import CtrlLToggleListener
    except ImportError as e:
        self._append_game_log(f"[Automation] Hotkey module missing: {e}")
        return

    def on_ctrl_l() -> None:
        try:
            self.root.after(0, self._on_global_bare_ctrl_toggle)
        except tk.TclError:
            pass

    listener = CtrlLToggleListener(on_ctrl_l)
    if listener.start():
        self._brew_automation_hotkey_listener = listener
        self._append_game_log(
            "[Automation] Left Ctrl listening — Start/Pause automation (button on game screen must be armed)."
        )
    else:
        self._append_game_log(
            "[Automation] Install pynput for Left Ctrl while TLOPO is focused: pip install pynput"
        )
