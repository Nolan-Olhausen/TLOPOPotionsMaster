from __future__ import annotations

import json

import variables.global_variables as gv
from core_helpers import brew_gui_settings_path


def _normalize_live_game_visual_mode(v: str | None) -> str:
    s = str(v or "").strip().lower()
    if s == "none":
        return "None"
    if s == "exact":
        return "Exact"
    return "Simple"


def _empty_brew_ring_median_grid() -> dict[str, dict[str, tuple[int, int, int]]]:
    return {
        "next_piece_left": {},
        "next_piece_right": {},
        "current_piece_left": {},
        "current_piece_right": {},
    }


def _sync_board_bgr_vars_from_state(self) -> None:
    self._game_config_board_b_var.set(str(int(self._brew_board_await_b)))
    self._game_config_board_g_var.set(str(int(self._brew_board_await_g)))
    self._game_config_board_r_var.set(str(int(self._brew_board_await_r)))
    self._game_config_brew_again_r_var.set(str(int(self._brew_again_r)))
    self._game_config_brew_again_g_var.set(str(int(self._brew_again_g)))
    self._game_config_brew_again_b_var.set(str(int(self._brew_again_b)))
    self._game_config_brew_again_ok_r_var.set(str(int(self._brew_again_ok_r)))
    self._game_config_brew_again_ok_g_var.set(str(int(self._brew_again_ok_g)))
    self._game_config_brew_again_ok_b_var.set(str(int(self._brew_again_ok_b)))
    self._game_config_potion_failed_continue_r_var.set(str(int(self._potion_failed_continue_r)))
    self._game_config_potion_failed_continue_g_var.set(str(int(self._potion_failed_continue_g)))
    self._game_config_potion_failed_continue_b_var.set(str(int(self._potion_failed_continue_b)))


def _sync_automation_timing_vars_from_state(self) -> None:
    self._game_config_delay_var.set(str(float(self._brew_automation_delay_s)))
    self._game_config_foreground_settle_var.set(
        str(float(self._brew_automation_foreground_settle_s))
    )
    self._game_config_action_delay_var.set(str(float(self._brew_automation_action_delay_s)))
    self._game_config_pre_click_settle_var.set(
        str(float(self._brew_automation_pre_click_settle_s))
    )
    self._game_config_post_click_settle_var.set(
        str(float(self._brew_automation_post_click_settle_s))
    )
    self._game_config_post_drop_sleep_var.set(
        str(float(self._brew_automation_post_drop_sleep_s))
    )
    self._game_config_hand_poll_interval_ms_var.set(
        str(int(self._brew_automation_hand_poll_interval_ms))
    )
    self._game_config_board_wait_poll_interval_ms_var.set(
        str(int(self._brew_automation_board_wait_poll_interval_ms))
    )


def _sync_piece_cfg_rgb_vars_from_state(self) -> None:
    for t in gv._CONFIG_PIECE_DISPLAY_ORDER:
        if t in self._brew_piece_display_rgb:
            r, g, b = self._brew_piece_display_rgb[t]
            self._game_config_piece_r_vars[t].set(str(int(r)))
            self._game_config_piece_g_vars[t].set(str(int(g)))
            self._game_config_piece_b_vars[t].set(str(int(b)))
        else:
            self._game_config_piece_r_vars[t].set("0")
            self._game_config_piece_g_vars[t].set("0")
            self._game_config_piece_b_vars[t].set("0")


def _sync_ring_median_grid_vars_from_state(self) -> None:
    for sk in gv._GAME_CONFIG_RING_GRID_SLOTS:
        inner = self._brew_ring_median_grid.get(sk, {})
        for t in gv._CONFIG_PIECE_DISPLAY_ORDER:
            tup = inner.get(t) if isinstance(inner, dict) else None
            if isinstance(tup, tuple) and len(tup) == 3:
                r, g, b = int(tup[0]), int(tup[1]), int(tup[2])
                if (r | g | b) == 0:
                    self._game_config_ring_r_vars[sk][t].set("0")
                    self._game_config_ring_g_vars[sk][t].set("0")
                    self._game_config_ring_b_vars[sk][t].set("0")
                else:
                    self._game_config_ring_r_vars[sk][t].set(str(r))
                    self._game_config_ring_g_vars[sk][t].set(str(g))
                    self._game_config_ring_b_vars[sk][t].set(str(b))
            else:
                self._game_config_ring_r_vars[sk][t].set("0")
                self._game_config_ring_g_vars[sk][t].set("0")
                self._game_config_ring_b_vars[sk][t].set("0")


def _load_brew_gui_settings(self) -> None:
    path = brew_gui_settings_path()
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return
    if not isinstance(data, dict):
        return
    raw = data.get("automation_delay_s", data.get("delay_s"))
    if raw is not None:
        try:
            v = float(str(raw).strip().replace(",", "."))
        except ValueError:
            pass
        else:
            self._brew_automation_delay_s = max(0.0, min(5.0, v))
    for key, attr, lo, hi in (
        ("automation_foreground_settle_s", "_brew_automation_foreground_settle_s", 0.0, 2.0),
        ("automation_action_delay_s", "_brew_automation_action_delay_s", 0.0, 2.0),
        ("automation_pre_click_settle_s", "_brew_automation_pre_click_settle_s", 0.0, 1.0),
        ("automation_post_click_settle_s", "_brew_automation_post_click_settle_s", 0.0, 1.0),
        ("automation_post_drop_sleep_s", "_brew_automation_post_drop_sleep_s", 0.0, 2.0),
    ):
        if key not in data:
            continue
        try:
            fv = float(str(data[key]).strip().replace(",", "."))
        except (TypeError, ValueError):
            continue
        setattr(self, attr, max(lo, min(hi, fv)))
    for key, attr, lo, hi in (
        ("automation_hand_poll_interval_ms", "_brew_automation_hand_poll_interval_ms", 30, 1000),
        (
            "automation_board_wait_poll_interval_ms",
            "_brew_automation_board_wait_poll_interval_ms",
            30,
            2000,
        ),
    ):
        if key not in data:
            continue
        try:
            iv = int(data[key])
        except (TypeError, ValueError):
            continue
        setattr(self, attr, max(lo, min(hi, iv)))
    self._brew_live_game_visual = _normalize_live_game_visual_mode(data.get("live_game_visual"))
    self._game_config_live_visual_var.set(self._brew_live_game_visual)
    if "simple_ui" in data:
        su = data["simple_ui"]
        if isinstance(su, bool):
            self._brew_simple_ui = su
        elif isinstance(su, (int, float)):
            self._brew_simple_ui = bool(su)
        elif isinstance(su, str) and su.strip().lower() in ("1", "true", "yes", "on"):
            self._brew_simple_ui = True
        elif isinstance(su, str) and su.strip().lower() in ("0", "false", "no", "off"):
            self._brew_simple_ui = False
        self._game_config_simple_ui_var.set(bool(self._brew_simple_ui))
    for key, attr in (
        ("board_await_b", "_brew_board_await_b"),
        ("board_await_g", "_brew_board_await_g"),
        ("board_await_r", "_brew_board_await_r"),
        ("brew_again_r", "_brew_again_r"),
        ("brew_again_g", "_brew_again_g"),
        ("brew_again_b", "_brew_again_b"),
        ("brew_again_ok_r", "_brew_again_ok_r"),
        ("brew_again_ok_g", "_brew_again_ok_g"),
        ("brew_again_ok_b", "_brew_again_ok_b"),
        ("potion_failed_continue_r", "_potion_failed_continue_r"),
        ("potion_failed_continue_g", "_potion_failed_continue_g"),
        ("potion_failed_continue_b", "_potion_failed_continue_b"),
    ):
        if key not in data:
            continue
        try:
            iv = int(data[key])
        except (TypeError, ValueError):
            continue
        iv = max(0, min(255, iv))
        setattr(self, attr, iv)
    prgb = data.get("piece_display_rgb")
    if isinstance(prgb, dict):
        self._brew_piece_display_rgb.clear()
        for k, v in prgb.items():
            if k not in gv._CONFIG_PIECE_DISPLAY_ORDER or not isinstance(v, (list, tuple)) or len(v) != 3:
                continue
            try:
                r, g, b = int(v[0]), int(v[1]), int(v[2])
            except (TypeError, ValueError):
                continue
            self._brew_piece_display_rgb[k] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    rmg = data.get("ring_median_grid")
    if isinstance(rmg, dict):
        base = _empty_brew_ring_median_grid()
        for sk, inner in rmg.items():
            if sk not in base or not isinstance(inner, dict):
                continue
            for ck, tup in inner.items():
                if ck not in gv._CONFIG_PIECE_DISPLAY_ORDER or not isinstance(tup, (list, tuple)):
                    continue
                if len(tup) != 3:
                    continue
                try:
                    r, g, b = int(tup[0]), int(tup[1]), int(tup[2])
                except (TypeError, ValueError):
                    continue
                base[sk][ck] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        self._brew_ring_median_grid = base
    self._sync_board_bgr_vars_from_state()
    self._sync_automation_timing_vars_from_state()
    self._sync_piece_cfg_rgb_vars_from_state()
    self._sync_ring_median_grid_vars_from_state()


def _save_brew_gui_settings(self) -> None:
    path = brew_gui_settings_path()
    piece_rgb_out = {
        k: [int(v[0]), int(v[1]), int(v[2])]
        for k, v in self._brew_piece_display_rgb.items()
        if k in gv._CONFIG_PIECE_DISPLAY_ORDER
    }
    ring_grid_out: dict[str, dict[str, list[int]]] = {}
    for sk, inner in self._brew_ring_median_grid.items():
        if not isinstance(inner, dict):
            continue
        ring_grid_out[sk] = {
            k: [int(v[0]), int(v[1]), int(v[2])]
            for k, v in inner.items()
            if k in gv._CONFIG_PIECE_DISPLAY_ORDER
        }
    try:
        path.write_text(
            json.dumps(
                {
                    "automation_delay_s": self._brew_automation_delay_s,
                    "automation_foreground_settle_s": self._brew_automation_foreground_settle_s,
                    "automation_action_delay_s": self._brew_automation_action_delay_s,
                    "automation_pre_click_settle_s": self._brew_automation_pre_click_settle_s,
                    "automation_post_click_settle_s": self._brew_automation_post_click_settle_s,
                    "automation_post_drop_sleep_s": self._brew_automation_post_drop_sleep_s,
                    "automation_hand_poll_interval_ms": self._brew_automation_hand_poll_interval_ms,
                    "automation_board_wait_poll_interval_ms": self._brew_automation_board_wait_poll_interval_ms,
                    "live_game_visual": self._brew_live_game_visual,
                    "simple_ui": bool(self._brew_simple_ui),
                    "board_await_b": int(self._brew_board_await_b),
                    "board_await_g": int(self._brew_board_await_g),
                    "board_await_r": int(self._brew_board_await_r),
                    "brew_again_r": int(self._brew_again_r),
                    "brew_again_g": int(self._brew_again_g),
                    "brew_again_b": int(self._brew_again_b),
                    "brew_again_ok_r": int(self._brew_again_ok_r),
                    "brew_again_ok_g": int(self._brew_again_ok_g),
                    "brew_again_ok_b": int(self._brew_again_ok_b),
                    "potion_failed_continue_r": int(self._potion_failed_continue_r),
                    "potion_failed_continue_g": int(self._potion_failed_continue_g),
                    "potion_failed_continue_b": int(self._potion_failed_continue_b),
                    "piece_display_rgb": piece_rgb_out,
                    "ring_median_grid": ring_grid_out,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass
