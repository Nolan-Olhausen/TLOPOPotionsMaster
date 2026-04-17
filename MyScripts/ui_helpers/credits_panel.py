from __future__ import annotations

import tkinter as tk
import webbrowser

import variables.global_variables as gv
import variables.brew_credits as brew_credits


def _destroy_credits_embed(self) -> None:
    sh = getattr(self, "_credits_shell", None)
    self._credits_shell = None
    if sh is not None:
        try:
            sh.destroy()
        except tk.TclError:
            pass


def _draw_credits_layer(self) -> None:
    self._destroy_credits_embed()
    self.bg_canvas.delete("credits_layer")
    if not getattr(self, "_credits_visible", False) or self._view != "catalog":
        return

    w = max(self.root.winfo_width(), 1)
    h = max(self.root.winfo_height(), 1)
    sc = float(getattr(self, "_layout_font_scale", 1.0) or 1.0)
    pad = max(10, int(round(14 * sc)))
    panel_w = min(max(340, int(round(760 * sc))), max(320, int(w * 0.7)))
    panel_h = min(max(240, int(round(560 * sc))), max(220, int(h * 0.72)))
    cx = w // 2
    cy = h // 2

    shell = tk.Frame(
        self.bg_canvas,
        bg=gv.GAME_LOG_PANEL_FILL,
        highlightthickness=2,
        highlightbackground=gv.GAME_LOG_PANEL_OUTLINE,
        padx=pad,
        pady=pad,
    )
    self._credits_shell = shell

    tk.Label(
        shell,
        text=brew_credits.CREDITS_WINDOW_TITLE,
        font=self._font_title,
        fg=gv.GAME_LOG_TEXT,
        bg=gv.GAME_LOG_PANEL_FILL,
        anchor=tk.W,
    ).pack(anchor=tk.W, pady=(0, 8))

    tk.Label(
        shell,
        text=brew_credits.CREDITS_INTRO.strip(),
        font=self._font_meta,
        fg=gv.GAME_LOG_TEXT,
        bg=gv.GAME_LOG_PANEL_FILL,
        justify=tk.LEFT,
        wraplength=max(240, panel_w - (pad * 2) - 24),
        anchor=tk.W,
    ).pack(anchor=tk.W, pady=(0, 10))

    for title, url in brew_credits.CREDITS_LINKS:
        row = tk.Frame(shell, bg=gv.GAME_LOG_PANEL_FILL)
        row.pack(anchor=tk.W, pady=2)
        lbl = tk.Label(
            row,
            text=f"• {title}",
            font=self._font_meta,
            fg="#6eb3ff",
            bg=gv.GAME_LOG_PANEL_FILL,
            cursor="hand2",
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=max(220, panel_w - (pad * 2) - 42),
        )
        lbl.pack(anchor=tk.W)

        def _open(_e: tk.Event, u: str = url) -> None:
            webbrowser.open(u)

        lbl.bind("<Button-1>", _open)

    def _close() -> None:
        self._credits_visible = False
        self._destroy_credits_embed()
        self.bg_canvas.delete("credits_layer")
        self._raise_overlay_tags()

    tk.Button(
        shell,
        text="Close",
        font=self._font_meta,
        command=_close,
    ).pack(anchor=tk.E, pady=(pad, 0))

    self.bg_canvas.create_window(
        cx,
        cy,
        window=shell,
        anchor=tk.CENTER,
        width=panel_w,
        height=panel_h,
        tags="credits_layer",
    )


def _toggle_brew_credits_panel(self) -> None:
    if self._view != "catalog":
        return
    self._credits_visible = not self._credits_visible
    if not self._credits_visible:
        self._destroy_credits_embed()
        self.bg_canvas.delete("credits_layer")
        self._raise_overlay_tags()
        return
    self._draw_credits_layer()
    if self.bg_canvas.find_withtag("credits_layer"):
        self.bg_canvas.tag_raise("credits_layer")
