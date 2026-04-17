"""
Find the TLOPO **game client** window (not this Brewing app) in **screen pixels** (Windows).

- Targets the live client titled like ``The Legend of Pirates Online [BETA]`` by default.
- Enumerates all matching top-level windows, then picks the best match (prefers ``[BETA]`` in
  the title, then largest client area) so launchers / other windows do not win by accident.
- Optional process-name filter (``tlopo.exe``) when ``psutil`` is installed.
- Optional client capture via ``mss`` + Pillow.

**DPI:** This module does **not** change process DPI awareness on import. Calling
``enable_process_dpi_awareness()`` after your GUI exists can make Windows **resize or move**
already-created windows — only use it once at startup **before** ``tk.Tk()`` if you need it.

Non-Windows: ``find_window()`` returns False (no Win32).
"""

from __future__ import annotations

import ctypes
import re
import sys
import threading
from ctypes import wintypes
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

try:
    import win32api  # type: ignore
    import win32con  # type: ignore
    import win32gui  # type: ignore
    import win32process  # type: ignore

    WIN32_OK = True
except ImportError:
    win32api = None  # type: ignore
    win32con = None  # type: ignore
    win32gui = None  # type: ignore
    win32process = None  # type: ignore
    WIN32_OK = False

try:
    import psutil
except ImportError:
    psutil = None

# Primary window caption for the current TLOPO beta client (substring match is enough).
DEFAULT_GAME_WINDOW_TITLE = "The Legend of Pirates Online [BETA]"


def enable_process_dpi_awareness() -> None:
    """
    Best-effort per-monitor DPI awareness for the **whole process**.

    Call **once** before creating any windows (e.g. before ``tk.Tk()``). If you call this after
    the Brewing GUI is already open, Windows may rescale or reposition existing windows.
    """
    if not WIN32_OK:
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def win32_set_foreground_window(hwnd: int) -> bool:
    """
    Best-effort ``SetForegroundWindow`` using the attach-thread pattern (Windows 10+).

    Many DXGI / DWM captures match **foreground** composition; with one GUI button the
    Brewing window often stayed focused, unlike the old separate Get Window / Get Objects
    clicks where the game was usually foreground before capture.
    """
    if not WIN32_OK or win32gui is None or win32process is None or win32api is None:
        return False
    try:
        hwnd = int(hwnd)
    except (TypeError, ValueError):
        return False
    if hwnd <= 0:
        return False
    try:
        if not win32gui.IsWindow(hwnd):
            return False
    except Exception:
        return False
    try:
        fg = win32gui.GetForegroundWindow()
        if fg == hwnd:
            return True
        tid_cur = win32api.GetCurrentThreadId()
        tid_fg = win32process.GetWindowThreadProcessId(fg)[0]
        attached = False
        if tid_fg and tid_fg != tid_cur:
            win32process.AttachThreadInput(tid_fg, tid_cur, True)
            attached = True
        try:
            try:
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except Exception:
                pass
            win32gui.SetForegroundWindow(hwnd)
            try:
                return win32gui.GetForegroundWindow() == hwnd
            except Exception:
                return True
        finally:
            if attached:
                try:
                    win32process.AttachThreadInput(tid_fg, tid_cur, False)
                except Exception:
                    pass
    except Exception:
        return False


DWMWA_EXTENDED_FRAME_BOUNDS = 9
_dwmapi = None
try:
    _dwmapi = ctypes.WinDLL("dwmapi")
except Exception:
    _dwmapi = None


def _get_extended_frame_bounds(hwnd: int) -> Optional[Tuple[int, int, int, int]]:
    if not _dwmapi:
        return None
    rect = wintypes.RECT()
    hr = _dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd),
        wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(rect),
        ctypes.sizeof(rect),
    )
    if hr == 0:
        return rect.left, rect.top, rect.right, rect.bottom
    return None


def _compile_title_patterns(keywords: Iterable[str]) -> list[re.Pattern[str]]:
    return [re.compile(re.escape(k), re.IGNORECASE) for k in keywords]


def _client_area_pixels(hwnd: int) -> int:
    if not WIN32_OK:
        return 0
    try:
        l, t, r, b = win32gui.GetClientRect(hwnd)
        return max(0, r - l) * max(0, b - t)
    except Exception:
        return 0


def format_window_info_text(info: Dict[str, Any]) -> str:
    """Human-readable block matching PotionBotExeGUI log style (frame vs client, DPI, monitor, process)."""
    lines: List[str] = []
    fr = info.get("frame") or {}
    cl = info.get("client") or {}
    if isinstance(fr, dict) and fr.get("width"):
        lines.append(
            f"Window (frame): {fr['width']}×{fr['height']} at ({fr['left']}, {fr['top']})"
        )
    if isinstance(cl, dict) and cl.get("width"):
        lines.append(
            f"Client area: {cl['width']}×{cl['height']} at ({cl['left']}, {cl['top']})"
        )
    dpi = info.get("dpi") or {}
    if isinstance(dpi, dict) and dpi.get("dpi"):
        lines.append(f"DPI: {dpi['dpi']} ({dpi.get('scale_percent', 100)}% scaling)")
    mon = info.get("monitor") or {}
    if isinstance(mon, dict) and not mon.get("error"):
        fa = mon.get("full_area") or {}
        if isinstance(fa, dict) and fa.get("width"):
            prim = "Primary" if mon.get("is_primary") else "Secondary"
            lines.append(f"Monitor: {fa['width']}×{fa['height']} ({prim})")
    proc = info.get("process") or {}
    if isinstance(proc, dict) and proc.get("pid") is not None:
        name = proc.get("name") or "?"
        pid = proc["pid"]
        mem = proc.get("memory_mb")
        if mem is not None:
            lines.append(f"Process: {name} (PID: {pid}, {mem}MB)")
        else:
            lines.append(f"Process: {name} (PID: {pid})")
    win = info.get("window") or {}
    if isinstance(win, dict) and win.get("title") is not None:
        lines.append(f"Title: {win['title']!r}")
    return "\n".join(lines) if lines else str(info)


def _title_match_score(title: str) -> int:
    """
    Higher = better target for the real game. Prefer explicit [BETA] client caption.
    """
    t = title.lower()
    score = 0
    if "[beta]" in t:
        score += 500
    if "the legend of pirates online" in t:
        score += 200
    if "tlopo" in t:
        score += 50
    return score


class TlopoGameWindow:
    """
    Locate TLOPO's top-level window and query client/frame geometry in screen coordinates.

    Typical usage::

        win = TlopoGameWindow()
        if win.find_window():
            rect = win.get_client_rect()  # (left, top, right, bottom) screen px
            img = win.capture_client_image()  # PIL.Image or None
    """

    def __init__(
        self,
        proc_names: Iterable[str] = ("tlopo.exe",),
        title_keywords: Iterable[str] = (
            DEFAULT_GAME_WINDOW_TITLE,
            "The Legend of Pirates Online",
            "TLOPO",
        ),
        log: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.proc_names = tuple(n.lower() for n in proc_names)
        self._title_patterns = _compile_title_patterns(title_keywords)
        self._log = log or (lambda _m: None)
        self._lock = threading.RLock()
        self._hwnd: Optional[int] = None

    def find_window(self) -> bool:
        """Resolve `hwnd` via process list and/or title enumeration."""
        if not WIN32_OK:
            self._log("pywin32 not installed; cannot find TLOPO window.")
            with self._lock:
                self._hwnd = None
            return False

        hwnd: Optional[int] = None
        candidates: list[tuple[int, str]] = []

        if psutil is not None and self.proc_names:
            try:
                pids: list[int] = []
                for p in psutil.process_iter(["pid", "name"]):
                    name = (p.info.get("name") or "").lower()
                    if name in self.proc_names:
                        pids.append(int(p.info["pid"]))
                candidates = self._enumerate_windows_for_pids(pids)
            except Exception as e:
                self._log(f"psutil process scan failed: {e}")

        if not candidates:
            candidates = self._enumerate_windows_by_title()

        if candidates:
            hwnd = self._pick_best_hwnd(candidates)

        with self._lock:
            if hwnd and win32gui.IsWindow(hwnd):
                self._hwnd = hwnd
                return True
            self._hwnd = None
            return False

    def get_hwnd(self) -> Optional[int]:
        with self._lock:
            return self._hwnd

    def bring_to_foreground_for_capture(self) -> bool:
        """Raise and foreground this window before ``mss`` capture (Win32 only)."""
        h = self.get_hwnd()
        if not h:
            return False
        return win32_set_foreground_window(h)

    def get_window_title(self) -> str:
        """Title bar text of the selected window (empty if none / error)."""
        if not WIN32_OK:
            return ""
        with self._lock:
            h = self._hwnd
        if not h:
            return ""
        try:
            return (win32gui.GetWindowText(h) or "").strip()
        except Exception:
            return ""

    def is_valid(self) -> bool:
        """Window still exists, visible, and not minimized."""
        if not WIN32_OK:
            return False
        with self._lock:
            h = self._hwnd
        if not h:
            return False
        try:
            return bool(
                win32gui.IsWindow(h)
                and win32gui.IsWindowVisible(h)
                and not win32gui.IsIconic(h)
            )
        except Exception:
            return False

    def get_frame_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """Outer window bounds (l,t,r,b) in screen pixels; prefers DWM extended bounds."""
        if not WIN32_OK:
            return None
        with self._lock:
            h = self._hwnd
        if not h:
            return None
        try:
            ext = _get_extended_frame_bounds(h)
            if ext:
                return ext
            return win32gui.GetWindowRect(h)
        except Exception:
            return None

    def get_client_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """Client area (l,t,r,b) in **screen** pixels — use with mss / mapping from captures."""
        if not WIN32_OK:
            return None
        with self._lock:
            h = self._hwnd
        if not h:
            return None
        try:
            _l, _t, r_rel, b_rel = win32gui.GetClientRect(h)
            top_left = win32gui.ClientToScreen(h, (0, 0))
            l, t = top_left[0], top_left[1]
            return l, t, l + (r_rel - _l), t + (b_rel - _t)
        except Exception:
            return None

    def get_client_rect_mss_aligned(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Same top-left as ``get_client_rect``, but width/height match a one-shot ``mss`` grab.

        On Hi-DPI Windows, Win32 ``GetClientRect`` and the bitmap ``mss`` returns for that
        region can disagree. ROI transforms and overlays must use the **capture** pixel grid,
        or boxes drift relative to the game.
        """
        r = self.get_client_rect()
        if not r:
            return None
        l, t, ri, bo = r
        w, h = int(ri - l), int(bo - t)
        if w < 1 or h < 1:
            return r
        try:
            import mss  # type: ignore
        except ImportError:
            return r
        if sys.platform == "win32":
            try:
                from mss import windows as _mss_win  # type: ignore[import-untyped]

                _mss_win.MSS._set_dpi_awareness = lambda _self: None  # type: ignore[method-assign]
            except Exception:
                pass
        try:
            with mss.mss() as sct:
                shot = sct.grab({"left": int(l), "top": int(t), "width": w, "height": h})
            sw, sh = int(shot.size[0]), int(shot.size[1])
        except Exception:
            return r
        if sw < 1 or sh < 1:
            return r
        if sw == w and sh == h:
            return r
        return (l, t, l + sw, t + sh)

    def get_window_info(self) -> Optional[Dict[str, Any]]:
        """
        Snapshot of frame/client rects, DPI, monitor, process, and title (same data PotionBot logs).

        Client ``(left, top)`` is the **client-area origin** in screen space (inside the frame,
        below the title bar) — it will not match the frame's ``(left, top)``.
        """
        if not WIN32_OK:
            return None
        with self._lock:
            hwnd = self._hwnd
        if not hwnd or not win32gui.IsWindow(hwnd):
            return None

        try:
            info: Dict[str, Any] = {}

            frame_rect = self.get_frame_rect()
            client_rect = self.get_client_rect()

            if frame_rect:
                fl, ft, fr, fb = frame_rect
                info["frame"] = {
                    "left": fl,
                    "top": ft,
                    "right": fr,
                    "bottom": fb,
                    "width": fr - fl,
                    "height": fb - ft,
                }
            if client_rect:
                cl, ct, cr, cb = client_rect
                info["client"] = {
                    "left": cl,
                    "top": ct,
                    "right": cr,
                    "bottom": cb,
                    "width": cr - cl,
                    "height": cb - ct,
                }

            try:
                dpi = int(ctypes.windll.user32.GetDpiForWindow(hwnd))
                sf = dpi / 96.0
                info["dpi"] = {
                    "dpi": dpi,
                    "scale_factor": sf,
                    "scale_percent": int(sf * 100),
                }
            except Exception:
                info["dpi"] = {"dpi": 96, "scale_factor": 1.0, "scale_percent": 100}

            try:
                monitor = win32api.MonitorFromWindow(
                    hwnd, win32con.MONITOR_DEFAULTTONEAREST
                )
                mi = win32api.GetMonitorInfo(monitor)
                work = mi["Work"]
                mon = mi["Monitor"]
                info["monitor"] = {
                    "handle": monitor,
                    "is_primary": mi["Flags"] == win32con.MONITORINFOF_PRIMARY,
                    "full_area": {
                        "left": mon[0],
                        "top": mon[1],
                        "right": mon[2],
                        "bottom": mon[3],
                        "width": mon[2] - mon[0],
                        "height": mon[3] - mon[1],
                    },
                    "work_area": {
                        "left": work[0],
                        "top": work[1],
                        "right": work[2],
                        "bottom": work[3],
                        "width": work[2] - work[0],
                        "height": work[3] - work[1],
                    },
                }
            except Exception as e:
                info["monitor"] = {"error": str(e)}

            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                info["process"] = {"pid": int(pid), "name": "Unknown"}
                if psutil:
                    try:
                        proc = psutil.Process(int(pid))
                        details: Dict[str, Any] = {}
                        try:
                            details["name"] = str(proc.name())
                        except Exception:
                            pass
                        try:
                            details["exe"] = str(proc.exe())
                        except Exception:
                            pass
                        try:
                            rss = proc.memory_info().rss
                            details["memory_mb"] = round(rss / 1024 / 1024, 1)
                        except Exception:
                            details["memory_mb"] = 0.0
                        info["process"].update(details)
                    except Exception:
                        info["process"]["note"] = "psutil could not open process"
                else:
                    info["process"]["note"] = "psutil not installed"
            except Exception as e:
                info["process"] = {"error": str(e)}

            try:
                title = win32gui.GetWindowText(hwnd) or ""
                info["window"] = {
                    "handle": hwnd,
                    "title": title,
                    "class_name": win32gui.GetClassName(hwnd),
                }
            except Exception:
                info["window"] = {"handle": hwnd, "error": "properties"}

            return info
        except Exception:
            return None

    def capture_client_image(self):
        """
        Screenshot the client area. Requires ``mss`` and ``Pillow``.

        Returns:
            PIL.Image in RGB, or None if capture is unavailable or the window is missing.
        """
        rect = self.get_client_rect_mss_aligned() or self.get_client_rect()
        if not rect:
            return None
        l, t, r, b = rect
        w, h = int(r - l), int(b - t)
        if w < 2 or h < 2:
            return None
        try:
            import mss  # type: ignore
            from PIL import Image  # type: ignore
        except ImportError:
            self._log("mss and/or Pillow missing; cannot capture.")
            return None
        if sys.platform == "win32":
            try:
                from mss import windows as _mss_win  # type: ignore[import-untyped]

                _mss_win.MSS._set_dpi_awareness = lambda _self: None  # type: ignore[method-assign]
            except Exception:
                pass
        try:
            with mss.mss() as sct:
                shot = sct.grab({"left": l, "top": t, "width": w, "height": h})
            return Image.frombytes("RGB", shot.size, shot.rgb)
        except Exception as e:
            self._log(f"capture failed: {e}")
            return None

    def _enumerate_windows_for_pids(self, pids: list[int]) -> list[tuple[int, str]]:
        if not pids or not WIN32_OK:
            return []
        pset = set(pids)
        found: list[tuple[int, str]] = []

        def enum_handler(hwnd: int, _lp) -> bool:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid not in pset:
                    return True
                title = (win32gui.GetWindowText(hwnd) or "").strip()
                if title and any(p.search(title) for p in self._title_patterns):
                    found.append((hwnd, title))
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(enum_handler, None)
        except Exception:
            return []
        return found

    def _enumerate_windows_by_title(self) -> list[tuple[int, str]]:
        if not WIN32_OK:
            return []
        found: list[tuple[int, str]] = []

        def enum_handler(hwnd: int, _lp) -> bool:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            try:
                title = (win32gui.GetWindowText(hwnd) or "").strip()
                if title and any(p.search(title) for p in self._title_patterns):
                    found.append((hwnd, title))
            except Exception:
                pass
            return True

        try:
            win32gui.EnumWindows(enum_handler, None)
        except Exception:
            return []
        return found

    def _pick_best_hwnd(self, candidates: list[tuple[int, str]]) -> Optional[int]:
        """Prefer [BETA] game caption, then largest client (main game vs small dialogs)."""
        if not candidates or not WIN32_OK:
            return None
        ranked: list[tuple[tuple[int, int], int, str]] = []
        for hwnd, title in candidates:
            if not win32gui.IsWindow(hwnd):
                continue
            area = _client_area_pixels(hwnd)
            if area < 10_000:
                continue
            ts = _title_match_score(title)
            ranked.append(((ts, area), hwnd, title))
        if not ranked:
            for hwnd, title in candidates:
                if win32gui.IsWindow(hwnd):
                    return hwnd
            return None
        ranked.sort(key=lambda x: x[0], reverse=True)
        best = ranked[0]
        self._log(f"Picked game window: '{best[2]}' (score={best[0][0]}, client_px²={best[0][1]})")
        return best[1]


def main() -> None:
    w = TlopoGameWindow(log=print)
    ok = w.find_window()
    print("find_window:", ok, "hwnd:", w.get_hwnd())
    if ok:
        info = w.get_window_info()
        if info:
            print(format_window_info_text(info))
        img = w.capture_client_image()
        print("capture:", None if img is None else img.size)


if __name__ == "__main__":
    main()


__all__ = [
    "TlopoGameWindow",
    "DEFAULT_GAME_WINDOW_TITLE",
    "enable_process_dpi_awareness",
    "format_window_info_text",
    "main",
]
