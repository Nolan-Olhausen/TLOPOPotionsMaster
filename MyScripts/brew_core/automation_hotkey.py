"""
Global start/pause hotkey — same pattern as ``oldBot/run.py``:

``pynput.keyboard.Listener(on_press=...)``; only ``keyboard.Key.ctrl_l`` toggles;
all other keys are ignored (no combo / release logic).
"""

from __future__ import annotations

from typing import Callable, Optional


class CtrlLToggleListener:
    """Starts a non-blocking pynput listener; call :meth:`stop` before exit."""

    def __init__(self, on_ctrl_l_press: Callable[[], None]) -> None:
        self._on_ctrl_l_press = on_ctrl_l_press
        self._listener: Optional[object] = None

    def start(self) -> bool:
        if self._listener is not None:
            return True
        try:
            from pynput import keyboard
        except ImportError:
            return False

        def on_press(key: object) -> None:
            try:
                if key != keyboard.Key.ctrl_l:
                    return
            except AttributeError:
                return
            self._on_ctrl_l_press()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()
        return True

    def stop(self) -> None:
        if self._listener is None:
            return
        try:
            self._listener.stop()
        except Exception:
            pass
        self._listener = None
