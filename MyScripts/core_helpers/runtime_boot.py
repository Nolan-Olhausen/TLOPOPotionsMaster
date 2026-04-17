from __future__ import annotations

import atexit
import ctypes
import os
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path


def _brew_windows_normalize_tk_font_scaling(root: tk.Tk) -> None:
    """
    Keep Tk font point scaling at legacy 96 DPI on Windows.
    """
    if sys.platform != "win32":
        return
    if os.environ.get("BREW_NO_TK_FONT_SCALING", "").strip().lower() in ("1", "true", "yes"):
        return
    try:
        root.tk.call("tk", "scaling", "-displayof", ".", 96.0 / 72.0)
    except tk.TclError:
        pass


def _patch_mss_skip_process_dpi_awareness() -> None:
    """
    Prevent mss from toggling process DPI awareness after Tk is initialized.
    """
    if sys.platform != "win32":
        return
    try:
        from mss import windows as _mss_win  # type: ignore[import-untyped]

        _mss_win.MSS._set_dpi_awareness = lambda _self: None  # type: ignore[method-assign]
    except Exception:
        pass


BREW_CORMORANT_USE_FONT_FILE = "brew_cormorant_use_font_file"

_BREW_WINDOWS_PRIVATE_FONT_PATHS: list[str] = []
_BREW_FONT_CLEANUP_REGISTERED = False


def _brew_cleanup_windows_private_fonts() -> None:
    if sys.platform != "win32":
        return
    fr_private = 0x10
    for p in _BREW_WINDOWS_PRIVATE_FONT_PATHS:
        try:
            ctypes.windll.gdi32.RemoveFontResourceExW(p, fr_private, 0)
        except Exception:
            pass
    _BREW_WINDOWS_PRIVATE_FONT_PATHS.clear()


def _brew_register_windows_private_font(path: Path) -> bool:
    fr_private = 0x10
    s = str(path.resolve())
    return int(ctypes.windll.gdi32.AddFontResourceExW(s, fr_private, 0) or 0) > 0


def _brew_windows_broadcast_font_change() -> None:
    try:
        hwnd_broadcast = 0xFFFF
        wm_fontchange = 0x001D
        ctypes.windll.user32.SendMessageW(hwnd_broadcast, wm_fontchange, 0, 0)
    except Exception:
        pass


def brew_prepare_cormorant_fonts(root: tk.Tk, regular: Path, bold: Path) -> str | None:
    """
    Make bundled Cormorant usable with ``tkinter.font.Font(family=..., ...)``.

    Tcl builds without ``font create -file`` (common on Windows) need GDI private font
    registration first. Returns a Tk **family** string, ``BREW_CORMORANT_USE_FONT_FILE``
    when ``Font(file=...)`` works, or ``None`` on failure.
    """
    global _BREW_FONT_CLEANUP_REGISTERED
    if not regular.is_file() or not bold.is_file():
        return None

    if sys.platform == "win32":
        if not _brew_register_windows_private_font(regular):
            return None
        if not _brew_register_windows_private_font(bold):
            fr_private = 0x10
            ctypes.windll.gdi32.RemoveFontResourceExW(str(regular.resolve()), fr_private, 0)
            return None
        _brew_windows_broadcast_font_change()
        _BREW_WINDOWS_PRIVATE_FONT_PATHS.extend([str(regular.resolve()), str(bold.resolve())])
        if not _BREW_FONT_CLEANUP_REGISTERED:
            atexit.register(_brew_cleanup_windows_private_fonts)
            _BREW_FONT_CLEANUP_REGISTERED = True
        for candidate in ("Cormorant", "Cormorant Regular"):
            try:
                probe = tkfont.Font(root, family=candidate, size=12)
                actual = probe.actual("family")
                if "cormorant" in actual.lower():
                    return actual
            except tk.TclError:
                continue

        fr_private = 0x10
        for p in (str(bold.resolve()), str(regular.resolve())):
            ctypes.windll.gdi32.RemoveFontResourceExW(p, fr_private, 0)
        _BREW_WINDOWS_PRIVATE_FONT_PATHS.clear()
        return None

    try:
        tkfont.Font(root, file=str(regular), size=12)
    except tk.TclError:
        return None
    return BREW_CORMORANT_USE_FONT_FILE
