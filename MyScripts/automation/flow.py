from __future__ import annotations

import copy
import sys
import time
import tkinter as tk
import tkinter.messagebox as messagebox
from typing import Any

import brew_core.board_memory as brew_board_memory
import brew_core.recovery_automation as brew_recovery
from core_helpers import (
    brew_board_strategy_label,
    brew_choice_is_board_rule,
    potion_supports_port_royal_column_board_rule,
)
import variables.global_variables as gv

def _brew_automation_prereqs_ok (self )->bool :
    return bool (
    self ._game_prereq_window_ok 
    and self ._game_prereq_objects_ok 
    and self .potions 
    and self ._brew_piece_color_config_ok ()
    )


def _brew_automation_strategy_ok (self )->tuple [bool ,str ]:
    idx =max (0 ,min (self ._current_potion_index ,len (self .potions )-1 ))
    potion =self .potions [idx ]
    if not potion_supports_port_royal_column_board_rule (potion ):
        return (
        False ,
        "Board-rule automation currently supports Any Island, Cuba, Tortuga & Bilgewater, and Padres del Fuego.",
        )
    if not brew_choice_is_board_rule (potion ,self ._brew_strategy_choice ):
        return (
        False ,
        f'Select "{brew_board_strategy_label(potion)}" in strategy, then try again.',
        )
    return True ,""


def _brew_automation_current_potion(self)->dict[str, Any] | None:
    if not self.potions:
        return None
    idx = max(0, min(self._current_potion_index, len(self.potions) - 1))
    p = self.potions[idx]
    return p if isinstance(p, dict) else None


def _brew_automation_island_slug(self)->str:
    p = _brew_automation_current_potion(self)
    if not isinstance(p, dict):
        return "port_royal"
    key = str(p.get("island") or "").strip().lower()
    return key or "port_royal"


def _brew_automation_plan_slot_with_roi(
    self,
    pra,
    *,
    island_slug: str,
    vl: str,
    vr: str,
    nl: str | None,
    nr: str | None,
) -> tuple[int | None, bool, str]:
    def _pair_lands_below_top_row(sim_obj, col0: int, a_line: str, b_line: str) -> bool:
        """
        True when both gems would land below the top row.
        Game blocks drops that place either gem into the top row.
        """
        try:
            rows = int(brew_board_memory.ROWS)
            top_row = rows - 1
            if rows <= 1:
                return False
            if col0 < 0 or (col0 + 1) >= int(brew_board_memory.COLS):
                return False
            g = getattr(sim_obj, "grid", None)
            if not isinstance(g, list) or len(g) < rows:
                return False

            def _landing_row_for_col(c: int) -> int | None:
                for rr in range(rows):
                    try:
                        if g[rr][c] is None:
                            return rr
                    except Exception:
                        return None
                return None

            r1 = _landing_row_for_col(col0)
            r2 = _landing_row_for_col(col0 + 1)
            if r1 is None or r2 is None:
                return False
            return int(r1) < top_row and int(r2) < top_row
        except Exception:
            return False

    # 1) Strict board rule first (only if legal with top-row constraint).
    slot, auto_swap = pra.plan_island_exact_drop_slot(vl, vr, island_slug=island_slug)
    if slot is not None:
        pair_exact = brew_board_memory.drop_colors_for_place_pair(vl, vr, auto_swap=auto_swap)
        if (
            pair_exact is not None
            and brew_board_memory.board_memory_available()
            and self._brew_board_sim is not None
        ):
            a_e, b_e = pair_exact
            col0_e = int(slot) - 1
            try:
                can_place_exact = bool(self._brew_board_sim.can_place_pair(col0_e, a_e, b_e))
            except Exception:
                can_place_exact = False
            if can_place_exact and _pair_lands_below_top_row(self._brew_board_sim, col0_e, a_e, b_e):
                return slot, auto_swap, "rule-exact"
        else:
            # If board memory is unavailable, preserve previous exact-rule behavior.
            return slot, auto_swap, "rule-exact"

    # 2) ROI fallback: simulate all legal placements and pick max immediate merges.
    if (
        not brew_board_memory.board_memory_available()
        or self._brew_board_sim is None
    ):
        return None, False, "roi-unavailable"

    try:
        base_sim = copy.deepcopy(self._brew_board_sim)
    except Exception:
        return None, False, "roi-copy-failed"

    def _place_pair_score(sim_obj, left_tok: str, right_tok: str, swap_now: bool) -> tuple[bool, float]:
        pair = brew_board_memory.drop_colors_for_place_pair(left_tok, right_tok, auto_swap=swap_now)
        if pair is None:
            return False, -1.0
        a, b = pair
        best = -1.0
        found = False
        for col0 in range(max(0, brew_board_memory.COLS - 1)):
            try:
                if not sim_obj.can_place_pair(col0, a, b):
                    continue
                if not _pair_lands_below_top_row(sim_obj, col0, a, b):
                    continue
                s2 = copy.deepcopy(sim_obj)
                s2.place_pair_and_resolve(col0, a, b)
                st = getattr(s2, "last_stats", None)
                triples = int(getattr(st, "triples", 0) or 0)
                quads = int(getattr(st, "quads", 0) or 0)
                score = float(triples) + 2.0 * float(quads)
                best = max(best, score)
                found = True
            except Exception:
                continue
        if not found:
            return False, -1.0
        return True, best

    next_known = bool(nl and nr and nl != "Unknown" and nr != "Unknown")
    cols_rule = pra.board_tokens_for_island(island_slug)
    vl_tok = pra.normalize_island_piece_token(vl)
    vr_tok = pra.normalize_island_piece_token(vr)
    candidates: list[tuple[float, int, bool, int]] = []
    for swap_now in (False, True):
        pair_now = brew_board_memory.drop_colors_for_place_pair(vl, vr, auto_swap=swap_now)
        if pair_now is None:
            continue
        first_tok, second_tok = (vr_tok, vl_tok) if swap_now else (vl_tok, vr_tok)
        a, b = pair_now
        for col0 in range(max(0, brew_board_memory.COLS - 1)):
            try:
                if not base_sim.can_place_pair(col0, a, b):
                    continue
                if not _pair_lands_below_top_row(base_sim, col0, a, b):
                    continue
                sim2 = copy.deepcopy(base_sim)
                sim2.place_pair_and_resolve(col0, a, b)
                st = getattr(sim2, "last_stats", None)
                triples = int(getattr(st, "triples", 0) or 0)
                quads = int(getattr(st, "quads", 0) or 0)
                immediate = float(triples) + 2.0 * float(quads)
                lookahead = 0.0
                if next_known:
                    ok_a, score_a = _place_pair_score(sim2, str(nl), str(nr), False)
                    ok_b, score_b = _place_pair_score(sim2, str(nl), str(nr), True)
                    if ok_a or ok_b:
                        lookahead = max(score_a, score_b)
                score_total = immediate + 0.30 * lookahead
                match_count = 0
                if (
                    isinstance(cols_rule, tuple)
                    and len(cols_rule) >= 8
                    and first_tok is not None
                    and second_tok is not None
                ):
                    if 0 <= col0 < len(cols_rule) and cols_rule[col0] == first_tok:
                        match_count += 1
                    if 0 <= (col0 + 1) < len(cols_rule) and cols_rule[col0 + 1] == second_tok:
                        match_count += 1
                candidates.append((score_total, col0 + 1, swap_now, match_count))
            except Exception:
                continue
    if not candidates:
        return None, False, "roi-no-legal-slot"
    # When no exact board-rule match exists, prefer placements that still keep at least one gem
    # aligned with a valid board-rule column for this island.
    with_match = [c for c in candidates if int(c[3]) >= 1]
    pool = with_match if with_match else candidates
    # Maximize ROI score first, then favor more board-rule matches, then prefer leftmost slot.
    best_pick = max(pool, key=lambda c: (float(c[0]), int(c[3]), -int(c[1])))
    return int(best_pick[1]), bool(best_pick[2]), "roi-fallback"


def _brew_automation_recovery_after_capture (
    self ,
    *,
    det :Any ,
    brew_hwnd :int ,
    rect :tuple [int ,int ,int ,int ],
    results :list [Any ],
    pra :Any ,
)->None :
    """Advance fail-state recovery using one object-detection result set (no piece read)."""
    from tlopo_client.window import win32_set_foreground_window 

    rec =getattr (self ,"_brew_automation_recovery",None )
    if not isinstance (rec ,dict ):
        return 
    phase =str (rec .get ("phase")or "")

    def _foreground_game ()->None :
        if sys .platform =="win32"and brew_hwnd >0 :
            try :
                det .bring_to_foreground_for_capture ()
                time .sleep (self ._brew_automation_foreground_settle_s )
            except Exception :
                pass 

    def _restore_brew_window ()->None :
        if sys .platform =="win32"and brew_hwnd >0 :
            try :
                win32_set_foreground_window (brew_hwnd )
            except Exception :
                pass 

    def _click_center (cx :float ,cy :float )->None :
        sx ,sy =pra .client_xy_to_screen (rect ,cx ,cy )
        try :
            _foreground_game ()
            pra .win32_left_click_at_screen (
 sx ,
            sy ,
            settle_s =self ._brew_automation_action_delay_s ,
            pre_click_settle_s =self ._brew_automation_pre_click_settle_s ,
            )
            if self ._brew_automation_post_click_settle_s >0 :
                time .sleep (self ._brew_automation_post_click_settle_s )
        finally :
            _restore_brew_window ()

    if phase =="wait_list":
        row1 =pra .find_object_center (results ,"potion_list_row_1")
        if row1 is not None :
            rem =int (rec .get ("scroll_remaining")or 0 )
            rec ["list_wait_attempts"]=0 
            if rem >0 :
                rec ["phase"]="scroll"
            else :
                rec ["phase"]="click_row"
            self ._append_game_log ("[Automation] Recovery: potion list visible; scrolling/clicking row.")
            self ._brew_automation_reschedule (200 ,self ._brew_automation_tick_recovery )
            return 
        att =int (rec .get ("list_wait_attempts")or 0 )+1 
        rec ["list_wait_attempts"]=att 
        if att >160 :
            self ._append_game_log ("[Automation] Recovery: gave up waiting for potion list.")
            self ._brew_automation_recovery =None 
            self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
            return 
        self ._brew_automation_reschedule (220 ,self ._brew_automation_tick_recovery )
        return 

    if phase =="scroll":
        rem =int (rec .get ("scroll_remaining")or 0 )
        if rem >0 :
            dc =pra .find_object_center (results ,"potion_list_down")
            if dc is None :
                miss =int (rec .get ("down_miss")or 0 )+1 
                rec ["down_miss"]=miss 
                if miss >40 :
                    self ._append_game_log ("[Automation] Recovery: potion_list_down not found; aborting.")
                    self ._brew_automation_recovery =None 
                    self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
                    return 
                self ._brew_automation_reschedule (250 ,self ._brew_automation_tick_recovery )
                return 
            rec ["down_miss"]=0 
            _click_center (dc [0 ],dc [1 ])
            rec ["scroll_remaining"]=rem -1 
            self ._append_game_log (
            f"[Automation] Recovery: potion_list_down ({rec['scroll_remaining']} scrolls left)"
            )
            self ._brew_automation_reschedule (280 ,self ._brew_automation_tick_recovery )
            return 
        rec ["phase"]="click_row"
        self ._brew_automation_reschedule (180 ,self ._brew_automation_tick_recovery )
        return 

    if phase =="click_row":
        row =int (rec .get ("row")or 1 )
        lab =brew_recovery .potion_list_row_label (row )
        rc =pra .find_object_center (results ,lab )
        if rc is None :
            miss =int (rec .get ("row_miss")or 0 )+1 
            rec ["row_miss"]=miss 
            if miss >45 :
                self ._append_game_log (f"[Automation] Recovery: {lab} not found; aborting.")
                self ._brew_automation_recovery =None 
                self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
                return 
            self ._brew_automation_reschedule (220 ,self ._brew_automation_tick_recovery )
            return 
        _click_center (rc [0 ],rc [1 ])
        nm =str (rec .get ("target_name")or "?")
        self ._append_game_log (
        f"[Automation] Recovery: clicked {lab} for «{nm}»; pausing 1s, then check Brew Again (potion full) or resume."
        )
        rec ["phase"]="wait_brew_again"
        self ._brew_automation_reschedule (1000 ,self ._brew_automation_tick_recovery )
        return 

    if phase =="wait_brew_again":
        from brew_core.object_recognition import capture_recognition_bundle_for_ui 

        if (int (self ._brew_again_ok_r )|int (self ._brew_again_ok_g )|int (self ._brew_again_ok_b ))==0 :
            self ._append_game_log ("[Automation] Recovery: brew_again_ok RGB unset; resuming normal automation.")
            self ._brew_automation_recovery =None 
            self ._brew_automation_reschedule (250 ,self ._brew_automation_tick_move_to_parking )
            return 
        aok_obj =next (
        (r for r in results if str (r .get ("label",""))=="brew_again_ok"),
        None ,
        )
        frame_bgra2 =None 
        if rect is not None and isinstance (aok_obj ,dict ):
            try :
                bundle_ok =capture_recognition_bundle_for_ui (rect ,log =self ._game_error_log )
                frame_bgra2 =bundle_ok .get ("frame_bgra")if isinstance (bundle_ok ,dict )else None 
            except Exception :
                frame_bgra2 =None 
        aok_rgb =self ._sample_result_box_median_rgb (frame_bgra2 ,aok_obj )if isinstance (aok_obj ,dict )else None 
        aok_center =pra .find_object_center (results ,"brew_again_ok")
        park_center =pra .find_object_center (results ,"mouse_parking")or pra .find_object_center (
        results ,"drop_mouse"
        )
        if (
        rect is not None 
        and aok_center is not None 
        and self ._brew_again_ok_color_matches (aok_rgb )
        ):
            okx ,oky =pra .client_xy_to_screen (rect ,aok_center [0 ],aok_center [1 ])
            try :
                _foreground_game ()
                pra .win32_left_click_at_screen (
                okx ,
                oky ,
                settle_s =self ._brew_automation_action_delay_s ,
                pre_click_settle_s =self ._brew_automation_pre_click_settle_s ,
                )
                if self ._brew_automation_post_click_settle_s >0 :
                    time .sleep (self ._brew_automation_post_click_settle_s )
                if park_center is not None :
                    psx ,psy =pra .client_xy_to_screen (rect ,park_center [0 ],park_center [1 ])
                    pra .win32_move_cursor_screen (psx ,psy )
                self ._append_game_log (
                f"[Automation] Recovery: potion-full OK clicked at RGB {aok_rgb}; resuming."
                )
            finally :
                _restore_brew_window ()
        else :
            self ._append_game_log (
            "[Automation] Recovery: no potion-full OK match; game likely started — resuming."
            )
        self ._brew_automation_recovery =None 
        self ._brew_automation_reschedule (250 ,self ._brew_automation_tick_move_to_parking )
        return 

    self ._brew_automation_recovery =None 
    self ._brew_automation_reschedule (300 ,self ._brew_automation_tick_move_to_parking )


def _brew_automation_tick_recovery (self )->None :
    """Polling tick during fail recovery (potion list / scroll / row)."""
    self ._brew_automation_after_id =None 
    if not self ._brew_automation_running :
        return 
    ok ,msg =self ._brew_automation_strategy_ok ()
    if not ok :
        self ._brew_automation_recovery =None 
        self ._brew_automation_stop (msg )
        return 
    try :
        from tlopo_client.window import TlopoGameWindow ,win32_set_foreground_window 
        from brew_core.object_recognition import run_get_objects_pipeline 
        import brew_core.port_royal_automation as pra 
    except ImportError as e :
        self ._brew_automation_recovery =None 
        self ._brew_automation_stop (f"import failed: {e}")
        return 

    det =TlopoGameWindow (log =lambda _m :None )
    if not det .find_window ()or not det .is_valid ():
        self ._append_game_log ("[Automation] Recovery: TLOPO window not found; retrying…")
        self ._brew_automation_reschedule (450 ,self ._brew_automation_tick_recovery )
        return 

    brew_hwnd =0 
    if self ._brew_automation_ctx and isinstance (self ._brew_automation_ctx ,dict ):
        try :
            brew_hwnd =int (self ._brew_automation_ctx .get ("brew_hwnd")or 0 )
        except (TypeError ,ValueError ):
            brew_hwnd =0 
    if brew_hwnd ==0 and sys .platform =="win32":
        try :
            brew_hwnd =int (self .root .winfo_id ())
        except (tk .TclError ,TypeError ,ValueError ):
            brew_hwnd =0 

    rect =None 
    results :list [Any ]=[]
    try :
        if sys .platform =="win32"and brew_hwnd >0 :
            det .bring_to_foreground_for_capture ()
            time .sleep (0.05 )
        rect =det .get_client_rect_mss_aligned ()
        if not rect :
            self ._brew_automation_reschedule (450 ,self ._brew_automation_tick_recovery )
            return 
        results ,cap_ok ,_piece =run_get_objects_pipeline (
        rect ,
        log =self ._game_error_log ,
        verbose_logs =False ,
        )
        if not cap_ok or not results :
            self ._brew_automation_reschedule (450 ,self ._brew_automation_tick_recovery )
            return 
    finally :
        if sys .platform =="win32"and brew_hwnd >0 :
            try :
                win32_set_foreground_window (brew_hwnd )
            except Exception :
                pass 

    self ._brew_automation_recovery_after_capture (
    det =det ,
    brew_hwnd =brew_hwnd ,
    rect =rect ,
    results =results ,
    pra =pra ,
    )


def _brew_automation_reset_hand_poll (self )->None :
    self ._brew_automation_hand_pair_prev =None 
    self ._brew_automation_hand_poll_attempts =0 


def _brew_automation_stop (
self ,reason :str |None =None ,*,resync_hotkey :bool =True 
)->None :
    was =self ._brew_automation_running 
    self ._brew_automation_running =False 
    self ._brew_automation_ctx =None 
    self ._brew_automation_recovery =None 
    self ._brew_board_ingredient_done =[]
    self ._brew_automation_reset_hand_poll ()
    aid =self ._brew_automation_after_id 
    self ._brew_automation_after_id =None 
    if aid is not None :
        try :
            self .root .after_cancel (aid )
        except (tk .TclError ,ValueError ):
            pass 
    if was and reason :
        self ._append_game_log (f"[Automation] Paused: {reason}")
    if resync_hotkey :
        self ._brew_automation_hotkey_sync ()


def _brew_automation_start (self )->None :
    if self ._brew_automation_running :
        return 
    if not self ._brew_automation_prereqs_ok ():
        if (
        self ._game_prereq_window_ok 
        and self ._game_prereq_objects_ok 
        and self .potions 
        and not self ._brew_piece_color_config_ok ()
        ):
            messagebox .showwarning (
            "Automation",
            "Red, green, and blue piece RGB and empty-board RGB in config are still all zero (or missing). "
            "Run Config Colors (guided) or enter them in the automation config panel, then try again.",
            parent =self .root ,
            )
        else :
            messagebox .showwarning (
            "Automation",
            "Run Get window and Get locations first (both must succeed).",
            parent =self .root ,
            )
        return 
    ok ,msg =self ._brew_automation_strategy_ok ()
    if not ok :
        messagebox .showwarning ("Automation",msg ,parent =self .root )
        return 
    if sys .platform !="win32":
        messagebox .showerror (
        "Automation",
        "Mouse automation is only supported on Windows.",
        parent =self .root ,
        )
        return 
    self ._brew_automation_running =True 
    self ._brew_automation_ctx =None 
    self ._append_game_log (
    "[Automation] Started (Board Rule). Logs: next/current pieces, then each move. Left Ctrl pauses."
    )
    self ._brew_automation_after_id =self .root .after (
    0 ,self ._brew_automation_tick_move_to_parking 
    )


def _brew_automation_reschedule (self ,delay_ms :int ,fn )->None :
    if not self ._brew_automation_running :
        return 
    self ._brew_automation_after_id =self .root .after (delay_ms ,fn )


def _brew_log_automation_hand_summary (
self ,
*,
nl :str |None ,
nr :str |None ,
cl :str |None ,
cr :str |None ,
nl_rgb :tuple [int ,int ,int ]|None =None ,
nr_rgb :tuple [int ,int ,int ]|None =None ,
cl_rgb :tuple [int ,int ,int ]|None =None ,
cr_rgb :tuple [int ,int ,int ]|None =None ,
)->None :
    """One readable line: next/current labels plus per-slot ring median RGB when available."""
    def _fmt_rgb (t :tuple [int ,int ,int ]|None )->str :
        if not isinstance (t ,tuple )or len (t )!=3 :
            return "(?, ?, ?)"
        return f"({int(t[0])},{int(t[1])},{int(t[2])})"

    n1 =nl if nl is not None else "?"
    n2 =nr if nr is not None else "?"
    c1 =cl if cl is not None else "?"
    c2 =cr if cr is not None else "?"
    self ._append_game_log (
    "[Automation] "
    f"next L {n1} {_fmt_rgb(nl_rgb)}  R {n2} {_fmt_rgb(nr_rgb)}  |  "
    f"current L {c1} {_fmt_rgb(cl_rgb)}  R {c2} {_fmt_rgb(cr_rgb)}"
    )


def _brew_automation_tick_move_to_parking (self )->None :
    self ._brew_automation_after_id =None 
    if not self ._brew_automation_running :
        return 
    self ._brew_automation_reset_hand_poll ()
    ok ,msg =self ._brew_automation_strategy_ok ()
    if not ok :
        self ._brew_automation_stop (msg )
        return 
    try :
        from tlopo_client.window import TlopoGameWindow ,win32_set_foreground_window 
        from brew_core.object_recognition import (
        capture_recognition_bundle_for_ui ,
        run_get_objects_pipeline ,
        )
        import brew_core.port_royal_automation as pra 
    except ImportError as e :
        self ._brew_automation_stop (f"import failed: {e}")
        return 

    det =TlopoGameWindow (log =lambda _m :None )
    if not det .find_window ()or not det .is_valid ():
        self ._append_game_log ("[Automation] TLOPO window not found; retrying…")
        self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
        return 

    brew_hwnd =0 
    if sys .platform =="win32":
        try :
            brew_hwnd =int (self .root .winfo_id ())
        except (tk .TclError ,TypeError ,ValueError ):
            brew_hwnd =0 

    rect =None 
    results :list [Any ]=[]
    try :
        if sys .platform =="win32"and brew_hwnd >0 :
            det .bring_to_foreground_for_capture ()
            time .sleep (0.05 )
        rect =det .get_client_rect_mss_aligned ()
        if not rect :
            self ._append_game_log ("[Automation] No client rectangle; retrying…")
            self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
            return 
        results ,cap_ok ,_piece =run_get_objects_pipeline (
        rect ,
        log =self ._game_error_log ,
        verbose_logs =False ,
        )
        if not cap_ok or not results :
            self ._append_game_log ("[Automation] Capture failed; retrying…")
            self ._brew_automation_reschedule (450 ,self ._brew_automation_tick_move_to_parking )
            return 
    finally :
        if sys .platform =="win32"and brew_hwnd >0 :
            try :
                win32_set_foreground_window (brew_hwnd )
            except Exception :
                pass 

    park =pra .find_object_center (results ,"mouse_parking")or pra .find_object_center (
    results ,"drop_mouse"
    )
    if park is None or rect is None :
        self ._append_game_log ("[Automation] mouse_parking not found; retrying…")
        self ._brew_automation_reschedule (500 ,self ._brew_automation_tick_move_to_parking )
        return 

    psx ,psy =pra .client_xy_to_screen (rect ,park [0 ],park [1 ])
    if not pra .win32_move_cursor_screen (psx ,psy ):
        self ._brew_automation_stop ("could not move cursor (SetCursorPos failed)")
        return 

    self ._brew_automation_ctx ={"brew_hwnd":brew_hwnd }
    self ._brew_automation_board_wait_attempts =0 
    self ._brew_automation_reschedule (0 ,self ._brew_automation_tick_wait_for_hand_not_board )


def _brew_automation_tick_wait_for_hand_not_board (self )->None :
    """At parking: poll until both current-piece rings look unlike calibrated empty-board RGB, then read/drop."""
    self ._brew_automation_after_id =None 
    if not self ._brew_automation_running :
        return 
    ok ,msg =self ._brew_automation_strategy_ok ()
    if not ok :
        self ._brew_automation_stop (msg )
        return 
    try :
        from tlopo_client.window import TlopoGameWindow ,win32_set_foreground_window 
        from brew_core.object_recognition import capture_recognition_bundle_for_ui ,run_get_objects_pipeline 
        import brew_core.port_royal_automation as pra 
    except ImportError as e :
        self ._brew_automation_stop (f"import failed: {e}")
        return 

    det =TlopoGameWindow (log =lambda _m :None )
    if not det .find_window ()or not det .is_valid ():
        self ._append_game_log ("[Automation] TLOPO window not found; retrying…")
        self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
        return 

    brew_hwnd =0 
    if self ._brew_automation_ctx and isinstance (self ._brew_automation_ctx ,dict ):
        try :
            brew_hwnd =int (self ._brew_automation_ctx .get ("brew_hwnd")or 0 )
        except (TypeError ,ValueError ):
            brew_hwnd =0 
    if brew_hwnd ==0 and sys .platform =="win32":
        try :
            brew_hwnd =int (self .root .winfo_id ())
        except (tk .TclError ,TypeError ,ValueError ):
            brew_hwnd =0 

    rect =None 
    frame_bgra =None 
    results :list [Any ]=[]
    piece_info :dict [str ,Any ]={}
    try :
        if sys .platform =="win32"and brew_hwnd >0 :
            det .bring_to_foreground_for_capture ()
            time .sleep (0.05 )
        rect =det .get_client_rect_mss_aligned ()
        if not rect :
            self ._append_game_log ("[Automation] No client rectangle; retrying…")
            self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
            return 
        results ,cap_ok ,piece_info =run_get_objects_pipeline (
        rect ,
        log =self ._game_error_log ,
        verbose_logs =False ,
        )
        if not cap_ok or not results :
            self ._append_game_log ("[Automation] Capture failed; retrying…")
            self ._brew_automation_reschedule (450 ,self ._brew_automation_tick_move_to_parking )
            return 
    finally :
        if sys .platform =="win32"and brew_hwnd >0 :
            try :
                win32_set_foreground_window (brew_hwnd )
            except Exception :
                pass 

    if getattr (self ,"_brew_automation_recovery",None )is not None :
        if rect is None or not results :
            self ._brew_automation_reschedule (450 ,self ._brew_automation_tick_recovery )
            return 
        self ._brew_automation_recovery_after_capture (
        det =det ,
        brew_hwnd =brew_hwnd ,
        rect =rect ,
        results =results ,
        pra =pra ,
        )
        return 

    # Fail popup: continue → recovery list flow (scroll + row), not parking.
    if (
    getattr (self ,"_brew_automation_recovery",None )is None 
    and (int (self ._potion_failed_continue_r )|int (self ._potion_failed_continue_g )|int (self ._potion_failed_continue_b ))!=0 
    ):
        pfc_obj =next (
        (r for r in results if str (r .get ("label",""))=="potion_failed_continue"),
        None ,
        )
        if rect is not None and isinstance (pfc_obj ,dict ):
            try :
                bundle_pfc =capture_recognition_bundle_for_ui (rect ,log =self ._game_error_log )
                frame_bgra =bundle_pfc .get ("frame_bgra")if isinstance (bundle_pfc ,dict )else None 
            except Exception :
                frame_bgra =None 
        pfc_rgb =self ._sample_result_box_median_rgb (frame_bgra ,pfc_obj )if isinstance (pfc_obj ,dict )else None 
        if self ._potion_failed_continue_color_matches (pfc_rgb ):
            pfc_center =pra .find_object_center (results ,"potion_failed_continue")
            if pfc_center is not None and rect is not None :
                n_pt =len (self .potions )if self .potions else 0 
                idx =max (0 ,min (self ._current_potion_index ,n_pt -1 ))if n_pt else 0 
                pot =self .potions [idx ]if self .potions and n_pt else {}
                nm =str (pot .get ("display_name")if isinstance (pot ,dict )else "?")
                clicks ,row ,top =brew_recovery .plan_potion_list_scroll (idx ,n_pt )
                self ._brew_automation_recovery ={
                "phase":"wait_list",
                "scroll_remaining":clicks ,
                "row":row ,
                "target_name":nm ,
                "target_idx":idx ,
                "list_wait_attempts":0 ,
                "down_miss":0 ,
                "row_miss":0 ,
                }
                self ._append_game_log (
                f"[Automation] Recovery: fail continue for «{nm}» (index {idx +1}/{n_pt}), "
                f"{clicks}× potion_list_down → row {row} (list top index {top})."
                )
                # Entering recovery means the current round is done; reset board memory now
                # so the next round planner starts from a clean state.
                self ._hex_cell_fill_colors .clear ()
                self ._hex_cell_outline_colors .clear ()
                self .bg_canvas .delete ("board_memory_piece")
                self ._brew_reset_board_memory ()
                if self ._view =="game":
                    self ._draw_hex_grid_layer ()
                    self ._raise_overlay_tags ()
                fcx ,fcy =pra .client_xy_to_screen (rect ,pfc_center [0 ],pfc_center [1 ])
                try :
                    if sys .platform =="win32"and brew_hwnd >0 :
                        det .bring_to_foreground_for_capture ()
                        time .sleep (self ._brew_automation_foreground_settle_s )
                    pra .win32_left_click_at_screen (
                    fcx ,
                    fcy ,
                    settle_s =self ._brew_automation_action_delay_s ,
                    pre_click_settle_s =self ._brew_automation_pre_click_settle_s ,
                    )
                    if self ._brew_automation_post_click_settle_s >0 :
                        time .sleep (self ._brew_automation_post_click_settle_s )
                    self ._append_game_log (
                    f"[Automation] Recovery: Potion Failed Continue clicked at RGB {pfc_rgb}."
                    )
                finally :
                    if sys .platform =="win32"and brew_hwnd >0 :
                        try :
                            win32_set_foreground_window (brew_hwnd )
                        except Exception :
                            pass 
                self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_recovery )
                return 

                # If the completion popup is up and matches configured Brew Again RGB, click it.
    if (int (self ._brew_again_r )|int (self ._brew_again_g )|int (self ._brew_again_b ))!=0 :
        ra_obj =next (
        (r for r in results if str (r .get ("label",""))=="brew_again"),
        None ,
        )
        if rect is not None and isinstance (ra_obj ,dict ):
            try :
                bundle2 =capture_recognition_bundle_for_ui (rect ,log =self ._game_error_log )
                frame_bgra =bundle2 .get ("frame_bgra")if isinstance (bundle2 ,dict )else None 
            except Exception :
                frame_bgra =None 
        ra_rgb =self ._sample_result_box_median_rgb (frame_bgra ,ra_obj )if isinstance (ra_obj ,dict )else None 
        if self ._brew_again_color_matches (ra_rgb ):
            ra_center =pra .find_object_center (results ,"brew_again")
            park_center =pra .find_object_center (results ,"mouse_parking")or pra .find_object_center (
            results ,"drop_mouse"
            )
            if ra_center is not None and rect is not None :
                bsx ,bsy =pra .client_xy_to_screen (rect ,ra_center [0 ],ra_center [1 ])
                try :
                    if sys .platform =="win32"and brew_hwnd >0 :
                        det .bring_to_foreground_for_capture ()
                        time .sleep (self ._brew_automation_foreground_settle_s )
                    pra .win32_left_click_at_screen (
                    bsx ,
                    bsy ,
                    settle_s =self ._brew_automation_action_delay_s ,
                    pre_click_settle_s =self ._brew_automation_pre_click_settle_s ,
                    )
                    if self ._brew_automation_post_click_settle_s >0 :
                        time .sleep (self ._brew_automation_post_click_settle_s )
                    if park_center is not None and rect is not None :
                        psx ,psy =pra .client_xy_to_screen (rect ,park_center [0 ],park_center [1 ])
                        pra .win32_move_cursor_screen (psx ,psy )
                    # Brew Again starts a brand-new board; clear simulated overlay state
                    # so the app visuals match the fresh in-game board immediately.
                    self ._hex_cell_fill_colors .clear ()
                    self ._hex_cell_outline_colors .clear ()
                    self .bg_canvas .delete ("board_memory_piece")
                    self ._brew_reset_board_memory ()
                    if self ._view =="game":
                        self ._draw_hex_grid_layer ()
                        self ._raise_overlay_tags ()
                    self ._append_game_log (
                    f"[Automation] Brew Again clicked at RGB {ra_rgb}; moved cursor to parking."
                    )
                finally :
                    if sys .platform =="win32"and brew_hwnd >0 :
                        try :
                            win32_set_foreground_window (brew_hwnd )
                        except Exception :
                            pass 
            # After Brew Again, an optional confirmation popup can appear.
            if (
            rect is not None 
            and (int (self ._brew_again_ok_r )|int (self ._brew_again_ok_g )|int (self ._brew_again_ok_b ))!=0 
            ):
                try :
                    bundle3 =capture_recognition_bundle_for_ui (rect ,log =self ._game_error_log )
                    frame3 =bundle3 .get ("frame_bgra")if isinstance (bundle3 ,dict )else None 
                    results3 ,cap3 ,_piece3 =run_get_objects_pipeline (
                    rect ,
                    log =self ._game_error_log ,
                    verbose_logs =False ,
                    )
                except Exception :
                    frame3 =None 
                    cap3 =False 
                    results3 =[]
                if cap3 and isinstance (results3 ,list ):
                    aok_obj =next (
                    (r for r in results3 if str (r .get ("label",""))=="brew_again_ok"),
                    None ,
                    )
                    aok_rgb =self ._sample_result_box_median_rgb (frame3 ,aok_obj )if isinstance (aok_obj ,dict )else None 
                    if self ._brew_again_ok_color_matches (aok_rgb ):
                        aok_center =pra .find_object_center (results3 ,"brew_again_ok")
                        park2 =pra .find_object_center (results3 ,"mouse_parking")or pra .find_object_center (
                        results3 ,"drop_mouse"
                        )
                        if aok_center is not None :
                            okx ,oky =pra .client_xy_to_screen (rect ,aok_center [0 ],aok_center [1 ])
                            try :
                                if sys .platform =="win32"and brew_hwnd >0 :
                                    det .bring_to_foreground_for_capture ()
                                    time .sleep (self ._brew_automation_foreground_settle_s )
                                pra .win32_left_click_at_screen (
                                okx ,
                                oky ,
                                settle_s =self ._brew_automation_action_delay_s ,
                                pre_click_settle_s =self ._brew_automation_pre_click_settle_s ,
                                )
                                if self ._brew_automation_post_click_settle_s >0 :
                                    time .sleep (self ._brew_automation_post_click_settle_s )
                                if park2 is not None :
                                    psx2 ,psy2 =pra .client_xy_to_screen (rect ,park2 [0 ],park2 [1 ])
                                    pra .win32_move_cursor_screen (psx2 ,psy2 )
                                self ._append_game_log (
                                f"[Automation] Brew Again OK clicked at RGB {aok_rgb}; moved cursor to parking."
                                )
                            finally :
                                if sys .platform =="win32"and brew_hwnd >0 :
                                    try :
                                        win32_set_foreground_window (brew_hwnd )
                                    except Exception :
                                        pass 
            self ._brew_automation_reschedule (250 ,self ._brew_automation_tick_move_to_parking )
            return 

    if not isinstance (piece_info ,dict )or piece_info .get ("error")is not None :
        err =piece_info .get ("error")if isinstance (piece_info ,dict )else None 
        self ._append_game_log (
        f"[Automation] Piece read failed{f': {err}' if err else ''}; retrying…"
        )
        self ._brew_automation_reschedule (450 ,self ._brew_automation_tick_move_to_parking )
        return 

    if not pra .current_pair_rings_not_empty_board (
    piece_info ,
    self ._brew_board_await_r ,
    self ._brew_board_await_g ,
    self ._brew_board_await_b ,
    ):
        self ._brew_automation_board_wait_attempts +=1 
        if self ._brew_automation_board_wait_attempts >pra .BOARD_WAIT_MAX_ATTEMPTS :
            self ._append_game_log (
            "[Automation] Gave up waiting for hand vs board color — tune empty-board RGB or lighting."
            )
            self ._brew_automation_board_wait_attempts =0 
            self ._brew_automation_reschedule (900 ,self ._brew_automation_tick_move_to_parking )
            return 
        self ._brew_automation_reschedule (
        self ._brew_automation_board_wait_poll_interval_ms ,
        self ._brew_automation_tick_wait_for_hand_not_board 
        )
        return 

    self ._brew_automation_board_wait_attempts =0 
    self ._brew_automation_reschedule (0 ,self ._brew_automation_tick_after_parking_delay )


def _brew_automation_tick_after_parking_delay (self )->None :
    """Fresh capture at parking, settled hand read, board-rule plan (or ROI fallback), optional flip, immediate drop."""
    self ._brew_automation_after_id =None 
    if not self ._brew_automation_running :
        return 
    ok ,msg =self ._brew_automation_strategy_ok ()
    if not ok :
        self ._brew_automation_stop (msg )
        return 
    try :
        from tlopo_client.window import TlopoGameWindow ,win32_set_foreground_window 
        from brew_core.object_recognition import run_get_objects_pipeline 
        import brew_core.port_royal_automation as pra 
    except ImportError as e :
        self ._brew_automation_stop (f"import failed: {e}")
        return 

    det =TlopoGameWindow (log =lambda _m :None )
    if not det .find_window ()or not det .is_valid ():
        self ._append_game_log ("[Automation] TLOPO window not found before drop; retrying…")
        self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
        return 

    brew_hwnd =0 
    if self ._brew_automation_ctx and isinstance (self ._brew_automation_ctx ,dict ):
        try :
            brew_hwnd =int (self ._brew_automation_ctx .get ("brew_hwnd")or 0 )
        except (TypeError ,ValueError ):
            brew_hwnd =0 
    if brew_hwnd ==0 and sys .platform =="win32":
        try :
            brew_hwnd =int (self .root .winfo_id ())
        except (tk .TclError ,TypeError ,ValueError ):
            brew_hwnd =0 

    rect =None 
    results :list [Any ]=[]
    piece_info :dict [str ,Any ]={}
    try :
        if sys .platform =="win32"and brew_hwnd >0 :
            det .bring_to_foreground_for_capture ()
            time .sleep (0.05 )
        rect =det .get_client_rect_mss_aligned ()
        if not rect :
            self ._append_game_log ("[Automation] No client rectangle; retrying…")
            self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
            return 
        results ,cap_ok ,piece_info =run_get_objects_pipeline (
        rect ,
        log =self ._game_error_log ,
        verbose_logs =False ,
        )
        if not cap_ok or not results :
            self ._append_game_log ("[Automation] Capture failed; retrying…")
            self ._brew_automation_reschedule (450 ,self ._brew_automation_tick_move_to_parking )
            return 
        if not isinstance (piece_info ,dict )or piece_info .get ("error")is not None :
            err =piece_info .get ("error")if isinstance (piece_info ,dict )else None 
            self ._append_game_log (
            f"[Automation] Piece read failed{f': {err}' if err else ''}; retrying…"
            )
            self ._brew_automation_reschedule (450 ,self ._brew_automation_tick_move_to_parking )
            return 
    finally :
        if sys .platform =="win32"and brew_hwnd >0 :
            try :
                win32_set_foreground_window (brew_hwnd )
            except Exception :
                pass 

                # Fresh capture: read pair, require settled classifier, plan, optional R-click, drop.
    colors =pra .parse_automation_piece_colors (piece_info )
    cl ,cr =pra .automation_current_pair_labels (colors )
    nl ,nr =pra .automation_next_pair_labels (colors )
    # Prefer calibrated ring-median labels (per-slot grid) when available.
    cl_cal =pra .calibrated_label_for_slot_ring (
    "current_piece_left",
    colors .current_left .ring_rgb ,
    ring_median_grid =self ._brew_ring_median_grid ,
    piece_display_rgb =self ._brew_piece_display_rgb ,
    )
    cr_cal =pra .calibrated_label_for_slot_ring (
    "current_piece_right",
    colors .current_right .ring_rgb ,
    ring_median_grid =self ._brew_ring_median_grid ,
    piece_display_rgb =self ._brew_piece_display_rgb ,
    )
    nl_cal =pra .calibrated_label_for_slot_ring (
    "next_piece_left",
    colors .next_left .ring_rgb ,
    ring_median_grid =self ._brew_ring_median_grid ,
    piece_display_rgb =self ._brew_piece_display_rgb ,
    )
    nr_cal =pra .calibrated_label_for_slot_ring (
    "next_piece_right",
    colors .next_right .ring_rgb ,
    ring_median_grid =self ._brew_ring_median_grid ,
    piece_display_rgb =self ._brew_piece_display_rgb ,
    )
    if cl_cal :
        cl =cl_cal 
    if cr_cal :
        cr =cr_cal 
    if nl_cal :
        nl =nl_cal 
    if nr_cal :
        nr =nr_cal 
    unknown_slots :list [str ]=[]
    for nm ,tok in (
    ("next left",nl ),
    ("next right",nr ),
    ("current left",cl ),
    ("current right",cr ),
    ):
        if tok is None or tok =="Unknown":
            unknown_slots .append (nm )
    if unknown_slots :
        self ._brew_automation_stop (
        "Color read unmatched for "
        +", ".join (unknown_slots )
        +". Re-run 3. Config Colors."
        )
        return 
    if cl is None or cr is None :
        self ._brew_automation_reset_hand_poll ()
        self ._brew_log_automation_hand_summary (
        nl =nl ,
        nr =nr ,
        cl =cl ,
        cr =cr ,
        nl_rgb =colors .next_left .ring_rgb ,
        nr_rgb =colors .next_right .ring_rgb ,
        cl_rgb =colors .current_left .ring_rgb ,
        cr_rgb =colors .current_right .ring_rgb ,
        )
        self ._append_game_log ("[Automation] Current pair not read; retrying…")
        self ._brew_automation_reschedule (400 ,self ._brew_automation_tick_move_to_parking )
        return 

    self ._brew_automation_hand_poll_attempts +=1 
    settled_ok =pra .automation_current_hand_read_looks_settled (
    colors ,
    cl ,
    cr ,
    piece_display_rgb =dict (self ._brew_piece_display_rgb ),
    ring_median_grid =dict (self ._brew_ring_median_grid ),
    )
    if not settled_ok :
        self ._brew_automation_hand_pair_prev =None 
        if self ._brew_automation_hand_poll_attempts >pra .HAND_POLL_MAX_ATTEMPTS :
            self ._append_game_log (
            "[Automation] Hand read stayed low-confidence — tune guided ring/display RGB."
            )
            self ._brew_automation_reset_hand_poll ()
            self ._brew_automation_reschedule (800 ,self ._brew_automation_tick_move_to_parking )
            return 
        self ._brew_automation_reschedule (
        self ._brew_automation_hand_poll_interval_ms ,
        self ._brew_automation_tick_after_parking_delay 
        )
        return 

    prev =self ._brew_automation_hand_pair_prev 
    if prev is None :
        self ._brew_automation_hand_pair_prev =(cl ,cr )
        self ._brew_automation_reschedule (
        self ._brew_automation_hand_poll_interval_ms ,
        self ._brew_automation_tick_after_parking_delay 
        )
        return 
    if (cl ,cr )!=prev :
        self ._brew_automation_hand_pair_prev =(cl ,cr )
        self ._brew_automation_reschedule (
        self ._brew_automation_hand_poll_interval_ms ,
        self ._brew_automation_tick_after_parking_delay 
        )
        return 

    self ._brew_automation_reset_hand_poll ()

    user_flip =self ._brew_automation_flip_current_order 
    vl ,vr =(cr ,cl )if user_flip else (cl ,cr )
    island_slug =_brew_automation_island_slug (self )
    slot ,auto_swap ,plan_mode =_brew_automation_plan_slot_with_roi (
    self ,
    pra ,
    island_slug =island_slug ,
    vl =str (vl ),
    vr =str (vr ),
    nl =str (nl )if nl is not None else None ,
    nr =str (nr )if nr is not None else None ,
    )
    if slot is None :
        vlt =pra .normalize_island_piece_token (vl )
        vrt =pra .normalize_island_piece_token (vr )
        self ._append_game_log (
        f"[Automation] No board-rule/ROI slot for {vl}/{vr} → planner {vlt}/{vrt}"
        f" ({plan_mode}; vision {cl}/{cr}{'; user read-order flip' if user_flip else ''}); retrying…"
        )
        self ._brew_automation_reschedule (600 ,self ._brew_automation_tick_move_to_parking )
        return 

    drop_labels =pra .sorted_drop_labels_by_cx (results )
    if not drop_labels or slot <1 or slot >len (drop_labels ):
        self ._append_game_log ("[Automation] drop_* labels missing or slot out of range; retrying…")
        self ._brew_automation_reschedule (500 ,self ._brew_automation_tick_move_to_parking )
        return 

    d_lab =drop_labels [slot -1 ]
    drop_c =pra .find_object_center (results ,d_lab )
    if drop_c is None or rect is None :
        self ._append_game_log (f"[Automation] Center for {d_lab} not found; retrying…")
        self ._brew_automation_reschedule (500 ,self ._brew_automation_tick_move_to_parking )
        return 

    park =pra .find_object_center (results ,"mouse_parking")or pra .find_object_center (
    results ,"drop_mouse"
    )
    if auto_swap and (park is None or rect is None ):
        self ._append_game_log (
        "[Automation] In-game flip needed but mouse_parking not found; retrying…"
        )
        self ._brew_automation_reschedule (500 ,self ._brew_automation_tick_move_to_parking )
        return 

    psx =psy =0 
    if park is not None and rect is not None :
        psx ,psy =pra .client_xy_to_screen (rect ,park [0 ],park [1 ])
    dsx ,dsy =pra .client_xy_to_screen (rect ,drop_c [0 ],drop_c [1 ])

    try :
        if sys .platform =="win32"and brew_hwnd >0 :
            det .bring_to_foreground_for_capture ()
            time .sleep (self ._brew_automation_foreground_settle_s )
        if auto_swap :
            pra .win32_right_click_at_screen (
            psx ,
            psy ,
            settle_s =self ._brew_automation_action_delay_s ,
            pre_click_settle_s =self ._brew_automation_pre_click_settle_s ,
            )
            if self ._brew_automation_post_click_settle_s >0 :
                time .sleep (self ._brew_automation_post_click_settle_s )
        if not pra .win32_move_cursor_screen (dsx ,dsy ):
            self ._brew_automation_stop ("could not move cursor to drop slot")
            return 
        if self ._brew_automation_action_delay_s >0 :
            time .sleep (self ._brew_automation_action_delay_s )
        pra .win32_left_click_at_current_pos (
        pre_click_settle_s =self ._brew_automation_pre_click_settle_s 
        )
        if self ._brew_automation_post_click_settle_s >0 :
            time .sleep (self ._brew_automation_post_click_settle_s )
        if self ._brew_automation_post_drop_sleep_s >0 :
            time .sleep (self ._brew_automation_post_drop_sleep_s )
            # Move to parking immediately after drop.
        if park is not None and rect is not None :
            psx_p ,psy_p =pra .client_xy_to_screen (rect ,park [0 ],park [1 ])
            if pra .win32_move_cursor_screen (psx_p ,psy_p ):
                if self ._brew_automation_post_drop_sleep_s >0 :
                    time .sleep (self ._brew_automation_post_drop_sleep_s )
    finally :
        if sys .platform =="win32"and brew_hwnd >0 :
            try :
                win32_set_foreground_window (brew_hwnd )
            except Exception :
                pass 

                # oldBot parity: update board-memory sim immediately after the drop path succeeds.
    self ._brew_board_memory_apply_automation_drop (
    slot =int (slot ),
    auto_swap =bool (auto_swap ),
    vl =str (vl ),
    vr =str (vr ),
    cl =str (cl ),
    cr =str (cr ),
    )

    # oldBot ``run.py --delay``: extra idle after each drop before next parking/read cycle.
    drop_poll_delay_s =max (0.0 ,float (self ._brew_automation_delay_s ))
    if drop_poll_delay_s >0 :
        time .sleep (drop_poll_delay_s )

    pl =pra .normalize_island_piece_token (vl )
    pr =pra .normalize_island_piece_token (vr )
    play_l ,play_r =(pr ,pl )if auto_swap else (pl ,pr )
    self ._brew_log_automation_hand_summary (
    nl =nl ,
    nr =nr ,
    cl =cl ,
    cr =cr ,
    nl_rgb =colors .next_left .ring_rgb ,
    nr_rgb =colors .next_right .ring_rgb ,
    cl_rgb =colors .current_left .ring_rgb ,
    cr_rgb =colors .current_right .ring_rgb ,
    )
    move_bits :list [str ]=[]
    if auto_swap :
        move_bits .append ("right-click at parking")
    move_bits .append (f"left-click {d_lab}")
    mode_txt ="rule exact"if plan_mode =="rule-exact"else "ROI fallback"
    move_bits .append (f"{island_slug.replace('_',' ')} pair starting at column {slot} ({mode_txt})")
    move_bits .append (f"board columns played as {play_l} then {play_r}")
    if user_flip :
        move_bits .append ("(vision order flipped via board right-click)")
    self ._append_game_log ("[Automation] move: "+"; ".join (move_bits )+".")

    self ._brew_automation_reschedule (0 ,self ._brew_automation_tick_move_to_parking )


