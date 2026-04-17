from __future__ import annotations

import tkinter as tk
import tkinter.messagebox as messagebox

import variables.global_variables as gv


def _active_pil_template(self):
    if getattr(self, "_brew_simple_ui", False):
        return None
    if self._view == "game" and self._game_template is not None:
        return self._game_template
    return self._catalog_template


def _on_escape(self, _event: tk.Event) -> None:
    if self._view == "game":
        self._exit_game_view()


def _on_root_delete_protocol(self) -> None:
    self._brew_automation_hotkey_stop()
    self._stop_tlopo_shape_overlay()
    self._save_brew_gui_settings()
    self.root.destroy()


def _automation_start_button_style(self) -> tuple[str, str, str, str]:
    if getattr(self, "_brew_simple_ui", False):
        if self._brew_automation_armed:
            return (
                gv.BREW_SIMPLE_UI_PANEL_BG,
                gv.BREW_SIMPLE_UI_MUTED,
                gv.BREW_SIMPLE_UI_TEXT,
                gv.GAME_CAPTION_AUTOMATION_ARMED,
            )
        return (
            gv.BREW_SIMPLE_UI_PANEL_BG,
            gv.BREW_SIMPLE_UI_MUTED,
            gv.BREW_SIMPLE_UI_TEXT,
            gv.GAME_CAPTION_AUTOMATION_START,
        )
    if self._brew_automation_armed:
        return (
            gv.GAME_UI_BUTTON_FILL,
            gv.GAME_UI_BUTTON_OUTLINE,
            gv.GAME_UI_BUTTON_TEXT,
            gv.GAME_CAPTION_AUTOMATION_ARMED,
        )
    if self._brew_automation_prereqs_ok():
        return (
            gv.GAME_UI_BUTTON_FILL,
            gv.GAME_UI_BUTTON_OUTLINE,
            gv.GAME_UI_BUTTON_TEXT,
            gv.GAME_CAPTION_AUTOMATION_START,
        )
    return (
        gv.GAME_UI_BUTTON_DISABLED_FILL,
        gv.GAME_UI_BUTTON_DISABLED_OUTLINE,
        gv.GAME_UI_BUTTON_DISABLED_TEXT,
        gv.GAME_CAPTION_AUTOMATION_START,
    )


def _refresh_automation_start_button(self) -> None:
    if self._view != "game":
        return
    as_fill, as_outline, as_text, as_lbl = self._automation_start_button_style()
    ids_r = self.bg_canvas.find_withtag("automation_start_btn")
    if ids_r:
        self.bg_canvas.itemconfigure(ids_r[0], fill=as_fill, outline=as_outline)
    ids_t = self.bg_canvas.find_withtag("automation_start_label")
    if ids_t:
        self.bg_canvas.itemconfigure(ids_t[0], text=as_lbl, fill=as_text)


def _on_automation_start_clicked(self) -> None:
    if self._brew_automation_armed:
        self._brew_automation_armed = False
        if self._brew_automation_running:
            self._brew_automation_stop("Start button")
        else:
            self._brew_automation_hotkey_sync()
        self._append_game_log("[Automation] Start disarmed — Left Ctrl inactive.")
        return
    if not self._brew_automation_prereqs_ok():
        if (
            self._game_prereq_window_ok
            and self._game_prereq_objects_ok
            and self.potions
            and not self._brew_piece_color_config_ok()
        ):
            messagebox.showwarning(
                "Automation",
                "Red, green, and blue piece RGB and empty-board RGB in config are still all zero (or missing). "
                "Run Config Colors (guided) or enter them in the automation config panel, then try again.",
                parent=self.root,
            )
        else:
            messagebox.showwarning(
                "Automation",
                "Run Get window and Get locations first (both must succeed).",
                parent=self.root,
            )
        return
    self._brew_automation_armed = True
    self._append_game_log(
        "[Automation] Armed — press Left Ctrl to start or pause automation; click Start again to disarm."
    )
    self._brew_automation_hotkey_sync()


def _refresh_logs_toggle_label(self) -> None:
    ids = self.bg_canvas.find_withtag("logs_toggle_label")
    if ids:
        self.bg_canvas.itemconfigure(ids[0], text="Hide logs" if self._game_log_visible else "Logs")


def _get_objects_button_style(self) -> tuple[str, str, str]:
    if getattr(self, "_brew_simple_ui", False):
        return (
            gv.BREW_SIMPLE_UI_PANEL_BG,
            gv.BREW_SIMPLE_UI_MUTED,
            gv.BREW_SIMPLE_UI_TEXT,
        )
    if self._game_prereq_window_ok:
        return (gv.GAME_UI_BUTTON_FILL, gv.GAME_UI_BUTTON_OUTLINE, gv.GAME_UI_BUTTON_TEXT)
    return (
        gv.GAME_UI_BUTTON_DISABLED_FILL,
        gv.GAME_UI_BUTTON_DISABLED_OUTLINE,
        gv.GAME_UI_BUTTON_DISABLED_TEXT,
    )
