"""
Semi-transparent Toplevel over the TLOPO **client** area drawing ``object_shapes.json`` ROIs.

Mirrors PotionBotExeGUI ``ObjectRecognizer`` right-click overlay (boxes + polygons + labels),
using ``brew_object_recognition`` shape loading and scaling (same letterbox transform).
"""

from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from typing import Callable, Dict, List, Optional, Tuple

from brew_core.object_recognition import (
    BoxShape,
    PolyShape,
    Shape,
    _scaled_shapes_for_size,
    load_shapes,
    resolve_object_shapes_json,
)

ClientRectFn = Callable[[], Optional[Tuple[int, int, int, int]]]

# Same wording as the Brewing Get Locations report (``object_shapes.json`` keys unchanged).
_OVERLAY_VALIDATION_LABELS: dict[str, str] = {
    "validation_left": "Current Piece Left",
    "validation_right": "Current Piece Right",
}


def _overlay_drop_label_slots(scaled: List[Shape]) -> Dict[str, int]:
    """``drop_*`` labels → 1-based index in left-to-right order (matches Brewing log)."""
    items: list[tuple[float, float, str]] = []
    for s in scaled:
        lab = getattr(s, "label", "")
        if not isinstance(lab, str) or not lab.lower().startswith("drop_"):
            continue
        if isinstance(s, BoxShape):
            cx = (float(s.x0) + float(s.x1)) * 0.5
            cy = (float(s.y0) + float(s.y1)) * 0.5
        elif isinstance(s, PolyShape) and s.closed and len(s.pts) >= 3:
            xs = [float(p[0]) for p in s.pts]
            ys = [float(p[1]) for p in s.pts]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
        else:
            continue
        items.append((cx, cy, lab))
    items.sort(key=lambda t: (t[0], t[1]))
    return {lab: i + 1 for i, (_, __, lab) in enumerate(items)}


def _iround(v: float) -> int:
    return int(round(v))


class BrewTlopoShapeOverlay:
    """Toggleable debug overlay aligned to the live game client rectangle."""

    _LOOP_MS = 33
    _ALPHA = 0.35

    def __init__(self, root: tk.Tk, get_client_rect: ClientRectFn, *, font_family: str) -> None:
        self.root = root
        self._get_client_rect = get_client_rect
        self._font_family = font_family
        self._active = False
        self._win: tk.Toplevel | None = None
        self._canvas: tk.Canvas | None = None
        self._hide_btn: tk.Button | None = None
        self._job: str | None = None
        self._raw: List[Shape] = []
        self._baseline_w = 1280
        self._baseline_h = 720
        self._baseline_fit = "auto"
        self._reload_shapes()

    def _reload_shapes(self) -> None:
        path = resolve_object_shapes_json()
        if not path.is_file():
            self._raw = []
            self._next_piece_polygon_expand = 1.15
            return
        (
            self._raw,
            self._baseline_w,
            self._baseline_h,
            self._baseline_fit,
            self._next_piece_polygon_expand,
        ) = load_shapes(path)

    def _try_enable_click_through(self) -> None:
        """On Windows, make the overlay ignore mouse input (click-through)."""
        if sys.platform != "win32" or self._win is None:
            return
        try:
            hwnd = int(self._win.winfo_id())
            user32 = ctypes.windll.user32
            # Keep WinAPI signatures explicit on 64-bit Python.
            user32.GetWindowLongPtrW.restype = ctypes.c_longlong
            user32.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
            user32.SetWindowLongPtrW.restype = ctypes.c_longlong
            user32.SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_longlong]
            user32.SetLayeredWindowAttributes.restype = ctypes.c_int
            user32.SetLayeredWindowAttributes.argtypes = [
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.c_ubyte,
                ctypes.c_uint,
            ]
            user32.SetWindowPos.restype = ctypes.c_int
            user32.SetWindowPos.argtypes = [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_uint,
            ]
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            LWA_ALPHA = 0x2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_FRAMECHANGED = 0x0020
            style = int(user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE))
            style |= WS_EX_LAYERED | WS_EX_TRANSPARENT
            user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
            # Ensure layered composition remains visible while click-through is enabled.
            user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
            user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
            )
        except Exception:
            # If the platform/WM call fails, keep the overlay functional.
            pass

    @property
    def active(self) -> bool:
        return self._active

    def stop(self) -> None:
        if not self._active and self._win is None:
            return
        self._active = False
        if self._job:
            try:
                self.root.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        if self._win:
            try:
                self._win.destroy()
            except tk.TclError:
                pass
        self._win = None
        self._canvas = None
        self._hide_btn = None

    def start(self) -> bool:
        if self._active:
            return True
        rect = self._get_client_rect()
        if not rect:
            return False
        l, t, r, b = rect
        cw, ch = int(r - l), int(b - t)
        if cw < 8 or ch < 8:
            return False
        self._reload_shapes()
        self._win = tk.Toplevel(self.root)
        self._win.title("TLOPO shape overlay")
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        try:
            self._win.attributes("-alpha", self._ALPHA)
        except tk.TclError:
            pass
        self._win.geometry(f"{cw}x{ch}+{l}+{t}")
        self._canvas = tk.Canvas(
            self._win,
            width=cw,
            height=ch,
            bg="#000000",
            highlightthickness=0,
            confine=False,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._hide_btn = tk.Button(
            self._win,
            text="Hide Overlay",
            command=self.stop,
            takefocus=0,
            cursor="hand2",
            relief=tk.RAISED,
            bd=1,
            padx=8,
            pady=2,
        )
        self._hide_btn.place(relx=1.0, x=-8, y=8, anchor="ne")
        self._active = True
        try:
            self._win.update_idletasks()
        except tk.TclError:
            pass
        # Keep overlay interactive; Windows click-through styles were unreliable on some setups.
        self._draw_once()
        self._schedule_loop()
        return True

    def _schedule_loop(self) -> None:
        if self._active:
            self._job = self.root.after(self._LOOP_MS, self._loop_tick)

    def _loop_tick(self) -> None:
        if not self._active or self._win is None or self._canvas is None:
            return
        rect = self._get_client_rect()
        if rect:
            l, t, r, b = rect
            cw, ch = int(r - l), int(b - t)
            try:
                self._win.geometry(f"{cw}x{ch}+{l}+{t}")
            except tk.TclError:
                pass
            if self._hide_btn is not None:
                try:
                    self._hide_btn.place(relx=1.0, x=-8, y=8, anchor="ne")
                    self._hide_btn.lift()
                except tk.TclError:
                    pass
            self._draw_once()
        if self._active:
            self._schedule_loop()

    def _draw_once(self) -> None:
        if not self._canvas or not self._win:
            return
        rect = self._get_client_rect()
        if not rect:
            return
        l, t, r, b = rect
        cw, ch = int(r - l), int(b - t)
        self._canvas.delete("all")
        if not self._raw:
            self._canvas.create_text(
                cw // 2,
                ch // 2,
                text="object_shapes.json missing or empty",
                fill="#ffffff",
                font=(self._font_family, 12),
            )
            return
        scaled, tr = _scaled_shapes_for_size(
            self._raw,
            self._baseline_w,
            self._baseline_h,
            cw,
            ch,
            baseline_fit=self._baseline_fit,
            next_piece_polygon_expand=self._next_piece_polygon_expand,
        )
        drop_slots = _overlay_drop_label_slots(scaled)
        for s in scaled:
            lab = getattr(s, "label", "")
            if isinstance(lab, str) and lab in drop_slots:
                tag = f"drop_{drop_slots[lab]}"
            elif isinstance(lab, str) and lab in _OVERLAY_VALIDATION_LABELS:
                tag = _OVERLAY_VALIDATION_LABELS[lab]
            else:
                tag = str(lab)
            if isinstance(s, BoxShape):
                x0, y0, x1, y1 = _iround(s.x0), _iround(s.y0), _iround(s.x1), _iround(s.y1)
                self._canvas.create_rectangle(
                    x0, y0, x1, y1, outline=s.color, width=3, fill=""
                )
                self._canvas.create_text(
                    x0 + 8,
                    y0 - 10,
                    anchor="w",
                    text=tag,
                    fill=s.color,
                    font=(self._font_family, 11, "bold"),
                )
            elif isinstance(s, PolyShape) and s.closed and len(s.pts) >= 3:
                flat: list[int] = []
                for x, y in s.pts:
                    flat.extend([_iround(x), _iround(y)])
                self._canvas.create_polygon(
                    *flat, outline=s.color, width=3, fill=""
                )
                fx, fy = s.pts[0]
                self._canvas.create_text(
                    _iround(fx) + 8,
                    _iround(fy) - 10,
                    anchor="w",
                    text=tag,
                    fill=s.color,
                    font=(self._font_family, 11, "bold"),
                )
        info = (
            f"Overlay — {tr['method']}  scale={tr['scale_x']:.2f}  "
            f"offset={int(tr['offset_x'])},{int(tr['offset_y'])}"
        )
        self._canvas.create_text(
            cw // 2,
            18,
            anchor="n",
            text=info,
            fill="#ffffff",
            font=(self._font_family, 11, "bold"),
        )

    def toggle(self) -> bool:
        """Show overlay if hidden, else hide. Returns whether overlay is now visible."""
        if self._active:
            self.stop()
            return False
        return self.start()
