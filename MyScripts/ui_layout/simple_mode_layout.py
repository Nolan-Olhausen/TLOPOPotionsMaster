from __future__ import annotations

import tkinter as tk

import variables.global_variables as gv


def _simple_ui_active_potion_caption(self) -> str:
    active_name = "?"
    if self.potions:
        idx = max(0, min(self._current_potion_index, len(self.potions) - 1))
        p = self.potions[idx]
        if isinstance(p, dict):
            active_name = str(p.get("display_name") or "?")
    return f"Active Potion: {active_name}"


def _refresh_simple_active_potion_label(self) -> None:
    """Update the static Active Potion line after ``_current_potion_index`` changes (layout is not rerun)."""
    if not getattr(self, "_brew_simple_ui", False):
        return
    cap = _simple_ui_active_potion_caption(self)
    for item in self.bg_canvas.find_withtag("active_potion_label"):
        try:
            self.bg_canvas.itemconfigure(item, text=cap)
        except tk.TclError:
            pass


def _layout_simple_compact_overlays(self, *, include_game_controls: bool) -> None:
    """Shared simple-mode layout: list right, controls left."""
    w = max(self.root.winfo_width(), 1)
    h = max(self.root.winfo_height(), 1)
    sc = float(getattr(self, "_layout_font_scale", 1.0) or 1.0)

    self._recipe_rect = (0, 0, 0, 0)
    self._credits_btn_rect = (0, 0, 0, 0)
    self._game_board_rect = (0, 0, 0, 0)

    col_x = max(8, int(round(12 * sc)))
    col_y = max(8, int(round(12 * sc)))
    col_w = max(170, min(int(round(330 * sc)), int(w * 0.38)))
    list_gap = max(10, int(round(14 * sc)))
    list_x = min(w - 40, col_x + col_w + list_gap)
    list_y = max(8, int(round(10 * sc)))
    list_w = max(180, w - list_x - max(8, int(round(10 * sc))))
    list_h = max(120, h - max(12, int(round(16 * sc))))
    self._list_rect = (list_x, list_y, list_w, list_h)

    row_h = max(34, int(round(36 * sc)))
    row_gap = max(6, int(round(7 * sc)))

    base_fill = gv.BREW_SIMPLE_UI_PANEL_BG
    base_outline = gv.BREW_SIMPLE_UI_MUTED
    base_text = gv.BREW_SIMPLE_UI_TEXT

    def draw_btn(
        x0: int,
        y0: int,
        rw: int,
        rh: int,
        *,
        btn_tag: str,
        label_tag: str,
        text: str,
        fill: str,
        outline: str,
        text_fill: str,
        wrap_pad: int = 8,
    ) -> tuple[int, int, int, int]:
        self.bg_canvas.create_rectangle(
            x0,
            y0,
            x0 + rw,
            y0 + rh,
            fill=fill,
            outline=outline,
            width=2,
            tags=("game_ui", btn_tag),
        )
        self.bg_canvas.create_text(
            x0 + rw // 2,
            y0 + rh // 2,
            text=text,
            font=self._font_meta,
            fill=text_fill,
            anchor="center",
            justify="center",
            width=max(56, rw - wrap_pad),
            tags=("game_ui", label_tag),
        )
        return (x0, y0, x0 + rw, y0 + rh)

    y = col_y
    self._get_window_btn_rect = draw_btn(
        col_x,
        y,
        col_w,
        row_h,
        btn_tag="get_window_btn",
        label_tag="get_window_label",
        text=self._game_get_window_caption,
        fill=base_fill,
        outline=base_outline,
        text_fill=base_text,
    )
    y += row_h + row_gap

    self._get_objects_btn_rect = draw_btn(
        col_x,
        y,
        col_w,
        row_h,
        btn_tag="get_objects_btn",
        label_tag="get_objects_label",
        text=self._game_get_objects_caption,
        fill=base_fill,
        outline=base_outline,
        text_fill=base_text,
    )
    y += row_h + row_gap

    self._guided_config_btn_rect = draw_btn(
        col_x,
        y,
        col_w,
        row_h,
        btn_tag="guided_config_btn",
        label_tag="guided_config_label",
        text=self._guided_config_caption(),
        fill=base_fill,
        outline=base_outline,
        text_fill=base_text,
    )
    y += row_h + row_gap

    cfg_lbl = "Hide config" if self._game_config_visible else "Config Panel"
    self._config_toggle_rect = draw_btn(
        col_x,
        y,
        col_w,
        row_h,
        btn_tag="config_toggle_btn",
        label_tag="config_toggle_label",
        text=cfg_lbl,
        fill=base_fill,
        outline=base_outline,
        text_fill=base_text,
    )
    y += row_h + row_gap

    logs_lbl = "Hide logs" if self._game_log_visible else "Logs"
    self._logs_toggle_rect = draw_btn(
        col_x,
        y,
        col_w,
        row_h,
        btn_tag="logs_toggle_btn",
        label_tag="logs_toggle_label",
        text=logs_lbl,
        fill=base_fill,
        outline=base_outline,
        text_fill=base_text,
    )
    y += row_h + row_gap

    overlay_lbl = (
        "Hide overlay"
        if self._game_tlopo_overlay is not None and self._game_tlopo_overlay.active
        else "Object overlay"
    )
    self._overlay_toggle_rect = draw_btn(
        col_x,
        y,
        col_w,
        row_h,
        btn_tag="overlay_toggle_btn",
        label_tag="overlay_toggle_label",
        text=overlay_lbl,
        fill=base_fill,
        outline=base_outline,
        text_fill=base_text,
    )
    y += row_h + max(8, row_gap)

    self.bg_canvas.create_text(
        col_x,
        y,
        text=_simple_ui_active_potion_caption(self),
        font=self._font_meta,
        fill=base_text,
        anchor="nw",
        width=max(60, col_w),
        justify="left",
        tags=("game_ui", "active_potion_label"),
    )
    y += max(28, int(round(32 * sc)))

    if include_game_controls:
        strategy_h = max(64, int(round(74 * sc)))
        self._draw_game_strategy_embed(col_x, y, col_w, strategy_h)
        y += strategy_h + max(8, row_gap)

        _as_fill, _as_outline, _as_text, as_lbl = self._automation_start_button_style()
        auto_h = max(row_h, int(round(50 * sc)))
        self._automation_start_btn_rect = draw_btn(
            col_x,
            y,
            col_w,
            auto_h,
            btn_tag="automation_start_btn",
            label_tag="automation_start_label",
            text=as_lbl,
            fill=base_fill,
            outline=base_outline,
            text_fill=base_text,
            wrap_pad=10,
        )
        self._back_hit_rect = (0, 0, 0, 0)
    else:
        self._automation_start_btn_rect = (0, 0, 0, 0)
        self._back_hit_rect = (0, 0, 0, 0)
        credits_h = row_h
        credits_y = max(col_y, h - credits_h - max(8, int(round(10 * sc))))
        self._credits_btn_rect = draw_btn(
            col_x,
            credits_y,
            col_w,
            credits_h,
            btn_tag="credits_btn",
            label_tag="credits_label",
            text="Credits",
            fill=base_fill,
            outline=base_outline,
            text_fill=base_text,
        )
