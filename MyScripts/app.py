"""
Brewing helper — potion catalog GUI (Tkinter).

This file is the **application shell**: it loads the catalog, constructs ``PotionPickerApp``, wires Tk
callbacks, and runs ``main()``. Almost all behavior lives in sibling packages; names on
``PotionPickerApp`` are mostly **class attribute bindings** to functions imported as ``_bind_*``
aliases so callables like ``self._draw_hex_grid_layer`` stay stable for Tk and for other modules.

**UI overview**

- **Backgrounds**: ``Brewing/GUI/BrewingListGUI.jpg`` (catalog) and ``BrewingGameGUI.png`` (detail),
  letterboxed on a black canvas (uniform scale, aspect preserved; extra window area stays black).
  Typography and recipe thumbnails scale with the fitted template height.
- **Recipe column**: title, meta, and ingredients are drawn on the main canvas (no recipe frame).
- **Potion list**: names on the same canvas; wheel, scrollbar, and keys scroll the list. Click a
  potion for detail; Escape or the back control returns to the list.
- **Game view**: flat-top hex grid over ``GAME_ART_BBOX``; geometry from ``BREW_BOARD_HEX_GRID`` in
  ``hexGrid/``. Cell styling uses ``self._hex_cell_fill_colors`` and
  ``self._hex_cell_outline_colors``; redraw via ``_draw_hex_grid_layer``.
- **Pieces**: thumbnails from PNGs (alpha over the art). Canonical filenames live under
  ``Brewing/pieces/`` as ``{Color}{level}{NameNoSpaces}.png`` (e.g. ``Red3PoisonExtract.png``;
  catalog color ``black`` maps to grey piece art).
- **Typography**: list/recipe/panel text sizes — ``variables/brew_typography.py`` (Cormorant bundle
  under ``MyScripts/fonts/``).

**Where the code lives**

- ``tlopo_client/`` — game window discovery (Win32) and aspect / polygon geometry.
- ``brew_core/`` — board memory bridge, ROI recognition, next-piece color ID, Port Royal automation, overlay.
- ``variables/`` — shared constants.
- ``core_helpers/`` — paths, catalog, strategy labels, reporting, runtime/DPI helpers, misc utilities.
- ``hexGrid/`` — hex grid geometry and Port Royal column outlines.
- ``state_helpers/`` — settings load/save and Tk StringVar sync from app state.
- ``config_helpers/`` — automation/config panel and hit-testing.
- ``layer_helpers/`` — canvas layers (list, recipe, hex, log, board memory) and piece thumbnails.
- ``ui_layout/`` — resize and overlay layout lifecycle.
- ``ui_handlers/`` — canvas events, list navigation, view transitions.
- ``ui_helpers/`` — log embed, strategy/board UI, cross-cutting UI actions, game log coordination.
- ``guided_wizard/`` — guided color calibration.
- ``integration_handlers/`` — Get window / Get locations, overlay, TLOPO client rect.
- ``automation/`` — Port Royal automation state machine, hotkey wiring, brew-again checks.

**Entry point**

``main()`` enables optional process DPI awareness on Windows, patches ``mss`` before screenshots,
loads the potion catalog, builds ``PotionPickerApp``, and starts ``mainloop``.
"""

from __future__ import annotations

import json
import os
import sys
import tkinter as tk
import tkinter .font as tkfont 
from pathlib import Path
from typing import Any

from config_helpers import (
    _apply_config_delay_from_ui,
    _brew_piece_color_config_ok,
    _destroy_game_config_embed,
    _draw_game_config_layer,
    _guided_config_caption,
    _hit_config_toggle as _bind_hit_config_toggle,
    _pack_game_config_ring_slot_block,
    _refresh_config_toggle_label,
    _restore_game_config_defaults,
)
from core_helpers import (
    _empty_brew_ring_median_grid,
    BREW_CORMORANT_USE_FONT_FILE,
    _brew_windows_normalize_tk_font_scaling as _bind_brew_windows_normalize_tk_font_scaling,
    _patch_mss_skip_process_dpi_awareness as _bind_patch_mss_skip_process_dpi_awareness,
    brew_prepare_cormorant_fonts,
    _sample_bbox_mean_color,
    brew_bundled_cormorant_available,
    get_catalog_path,
    get_cormorant_bold_path,
    get_cormorant_regular_path,
    get_gui_dir,
    get_pieces_dir,
    load_catalog,
    resolve_serif_family,
    resolve_ui_sans_family,
    resolve_game_template_path,
    resolve_list_template_path,
)
from guided_wizard import _open_guided_color_wizard
from ui_helpers.strategy_board import (
    _brew_strategy_wrap_two_lines as _bind_brew_strategy_wrap_two_lines,
    _apply_brew_strategy_choice as _bind_apply_brew_strategy_choice,
    _brew_reset_board_memory as _bind_brew_reset_board_memory,
    _ingredient_for_board_line_color as _bind_ingredient_for_board_line_color,
    _brew_board_memory_apply_automation_drop as _bind_brew_board_memory_apply_automation_drop,
    _rebuild_brew_strategy_menu as _bind_rebuild_brew_strategy_menu,
    _destroy_game_strategy_embed as _bind_destroy_game_strategy_embed,
    _draw_game_strategy_embed as _bind_draw_game_strategy_embed,
    _refresh_brew_strategy_dropdown as _bind_refresh_brew_strategy_dropdown,
)
from ui_helpers.game_log_embed import (
    _destroy_game_log_embed as _bind_destroy_game_log_embed,
    _game_log_text_key_guard as _bind_game_log_text_key_guard,
    _sync_game_log_text_body as _bind_sync_game_log_text_body,
)
from ui_helpers.credits_panel import (
    _destroy_credits_embed as _bind_destroy_credits_embed,
    _draw_credits_layer as _bind_draw_credits_layer,
    _toggle_brew_credits_panel as _bind_toggle_brew_credits_panel,
)
from ui_helpers import (
    _active_pil_template as _bind_active_pil_template,
    _append_game_log as _bind_append_game_log,
    _automation_start_button_style as _bind_automation_start_button_style,
    _brew_automation_hotkey_sync as _bind_brew_automation_hotkey_sync,
    _clear_game_log as _bind_clear_game_log,
    _get_objects_button_style as _bind_get_objects_button_style,
    _on_automation_start_clicked as _bind_on_automation_start_clicked,
    _on_escape as _bind_on_escape,
    _on_root_delete_protocol as _bind_on_root_delete_protocol,
    _raise_overlay_tags as _bind_raise_overlay_tags,
    _refresh_automation_start_button as _bind_refresh_automation_start_button,
    _refresh_game_action_button_labels as _bind_refresh_game_action_button_labels,
    _refresh_logs_toggle_label as _bind_refresh_logs_toggle_label,
)
from ui_handlers.view_transitions import (
    _confirm_any_island_before_game as _bind_confirm_any_island_before_game,
    _enter_game_view as _bind_enter_game_view,
    _exit_game_view as _bind_exit_game_view,
    _show_potion as _bind_show_potion,
)
from ui_handlers.list_navigation import (
    _ensure_list_row_visible as _bind_ensure_list_row_visible,
    _list_row_at as _bind_list_row_at,
    _on_list_key_down as _bind_on_list_key_down,
    _on_list_key_up as _bind_on_list_key_up,
    _on_list_page_down as _bind_on_list_page_down,
    _on_list_page_up as _bind_on_list_page_up,
    _select_list_index as _bind_select_list_index,
)
from ui_layout import (
    _game_art_screen_rect as _bind_game_art_screen_rect,
    _initial_layout as _bind_initial_layout,
    _layout_app_level_chrome as _bind_layout_app_level_chrome,
    _layout_overlays as _bind_layout_overlays,
    _overlay_panel_bounds as _bind_overlay_panel_bounds,
    _redraw_background as _bind_redraw_background,
    _resize_done as _bind_resize_done,
    _schedule_resize as _bind_schedule_resize,
    _sync_ui_fonts_to_letterbox as _bind_sync_ui_fonts_to_letterbox,
)
from integration_handlers import (
    _refresh_overlay_toggle_label as _bind_refresh_overlay_toggle_label,
    _stop_tlopo_shape_overlay as _bind_stop_tlopo_shape_overlay,
    _game_error_log as _bind_game_error_log,
    _on_get_objects_clicked as _bind_on_get_objects_clicked,
    _on_get_window_clicked as _bind_on_get_window_clicked,
    _on_shape_overlay_clicked as _bind_on_shape_overlay_clicked,
    _sample_result_box_median_rgb as _bind_sample_result_box_median_rgb,
    _tlopo_client_rect_for_overlay as _bind_tlopo_client_rect_for_overlay,
)
from automation import (
    _brew_again_color_matches as _bind_brew_again_color_matches,
    _brew_again_ok_color_matches as _bind_brew_again_ok_color_matches,
    _potion_failed_continue_color_matches as _bind_potion_failed_continue_color_matches,
    _brew_automation_recovery_after_capture as _bind_brew_automation_recovery_after_capture,
    _brew_automation_hotkey_start as _bind_brew_automation_hotkey_start,
    _brew_automation_hotkey_stop as _bind_brew_automation_hotkey_stop,
    _brew_automation_prereqs_ok as _bind_brew_automation_prereqs_ok,
    _brew_automation_reschedule as _bind_brew_automation_reschedule,
    _brew_automation_reset_hand_poll as _bind_brew_automation_reset_hand_poll,
    _brew_automation_start as _bind_brew_automation_start,
    _brew_automation_stop as _bind_brew_automation_stop,
    _brew_automation_strategy_ok as _bind_brew_automation_strategy_ok,
    _brew_automation_tick_after_parking_delay as _bind_brew_automation_tick_after_parking_delay,
    _brew_automation_tick_move_to_parking as _bind_brew_automation_tick_move_to_parking,
    _brew_automation_tick_recovery as _bind_brew_automation_tick_recovery,
    _brew_automation_tick_wait_for_hand_not_board as _bind_brew_automation_tick_wait_for_hand_not_board,
    _brew_automation_hotkey_entry_ok as _bind_brew_automation_hotkey_entry_ok,
    _brew_automation_toggle_from_hotkey as _bind_brew_automation_toggle_from_hotkey,
    _on_global_bare_ctrl_toggle as _bind_on_global_bare_ctrl_toggle,
    _brew_log_automation_hand_summary as _bind_brew_log_automation_hand_summary,
)
from ui_handlers import (
    _hit_back_link as _bind_hit_back_link,
    _hit_app_chrome_controls as _bind_hit_app_chrome_controls,
    _hit_overlay_toggle as _bind_hit_overlay_toggle,
    _hit_logs_toggle as _bind_hit_logs_toggle,
    _hit_log_clear as _bind_hit_log_clear,
    _hit_get_window_button as _bind_hit_get_window_button,
    _hit_get_objects_button as _bind_hit_get_objects_button,
    _hit_guided_config_button as _bind_hit_guided_config_button,
    _hit_credits_button as _bind_hit_credits_button,
    _hit_automation_start_button as _bind_hit_automation_start_button,
    _try_handle_app_chrome_click as _bind_try_handle_app_chrome_click,
    _on_canvas_button3 as _bind_on_canvas_button3,
    _wheel_delta as _bind_wheel_delta,
    _on_bg_mousewheel as _bind_on_bg_mousewheel,
    _hit_list_scrollbar as _bind_hit_list_scrollbar,
    _hit_list_thumb as _bind_hit_list_thumb,
    _on_canvas_motion as _bind_on_canvas_motion,
    _on_canvas_leave as _bind_on_canvas_leave,
    _on_canvas_button1 as _bind_on_canvas_button1,
    _on_canvas_b1_motion as _bind_on_canvas_b1_motion,
    _on_canvas_b1_release as _bind_on_canvas_b1_release,
)
from state_helpers import (
    _load_brew_gui_settings as _bind_load_brew_gui_settings,
    _save_brew_gui_settings as _bind_save_brew_gui_settings,
    _sync_automation_timing_vars_from_state as _bind_sync_automation_timing_vars_from_state,
    _sync_board_bgr_vars_from_state as _bind_sync_board_bgr_vars_from_state,
    _sync_piece_cfg_rgb_vars_from_state as _bind_sync_piece_cfg_rgb_vars_from_state,
    _sync_ring_median_grid_vars_from_state as _bind_sync_ring_median_grid_vars_from_state,
)
from layer_helpers import (
    _draw_board_memory_pieces_layer as _bind_draw_board_memory_pieces_layer,
    _draw_game_log_layer as _bind_draw_game_log_layer,
    _draw_hex_grid_layer as _bind_draw_hex_grid_layer,
    _draw_list_canvas_layer as _bind_draw_list_canvas_layer,
    _draw_recipe_canvas_layer as _bind_draw_recipe_canvas_layer,
    _load_piece_thumbnail as _bind_load_piece_thumbnail,
    _resolve_exact_piece_png_for_gem as _bind_resolve_exact_piece_png_for_gem,
    _sync_board_strategy_hex_fills as _bind_sync_board_strategy_hex_fills,
)
import variables.global_variables as gv 
import variables.brew_typography as brew_ty 

try :
    from PIL import Image

    PIL_OK =True 
    try :
        _LANCZOS =Image .Resampling .LANCZOS 
    except AttributeError :
        _LANCZOS =Image .LANCZOS # type: ignore[attr-defined]
except ImportError :
    Image =None # type: ignore[assignment]
    PIL_OK =False 
    _LANCZOS =None # type: ignore[assignment]

# Pillow is optional: list/game backgrounds and panel color sampling in ``PotionPickerApp.__init__``;
# piece thumbnails use PIL when installed (see ``layer_helpers``).

# ---------------------------------------------------------------------------
# PotionPickerApp — state and Tk wiring only; behavior via _bind_* assignments below __init__.
# ---------------------------------------------------------------------------


class PotionPickerApp :
    """Main window: ``__init__`` sets attributes, loads assets, and binds events; all other
    ``self._…`` callables are bound to implementations in helper packages (see module docstring).

    **Fonts:** point sizes live in ``variables/brew_typography.py``. ``__init__`` builds
    ``self._font_*`` from those values; Cormorant vs system fallback is handled there.
    """

    def __init__ (self ,root :tk .Tk ,potions :list [dict ],*,catalog_path :Path )->None :
        self .root =root 
        _brew_windows_normalize_tk_font_scaling (root )
        self .potions =potions 
        self .catalog_path =catalog_path 
        self .pieces_dir =get_pieces_dir ()
        self .gui_dir =get_gui_dir ()
        self ._thumb_cache :dict [str ,tk .PhotoImage ]={}
        self ._thumb_keepalive :list [tk .PhotoImage ]=[]
        self ._board_memory_photo_refs :list [tk .PhotoImage ]=[]
        self ._brew_board_sim :Any =None 
        self ._brew_board_memory :Any =None 
        self ._brew_board_ingredient_done :list [bool ]=[]

        self ._list_bg_path =resolve_list_template_path (self .gui_dir )
        self ._game_bg_path =resolve_game_template_path (self .gui_dir )
        self ._catalog_template =None 
        self ._game_template =None 
        if self ._list_bg_path and PIL_OK and Image is not None :
            self ._catalog_template =Image .open (self ._list_bg_path ).convert ("RGB")
        elif self ._list_bg_path and not PIL_OK :
            print (
                "Install Pillow (pip install -r requirements.txt) to use Brewing/GUI backgrounds.",
            file =sys .stderr ,
            )
        if self ._game_bg_path and PIL_OK and Image is not None :
            self ._game_template =Image .open (self ._game_bg_path ).convert ("RGB")

        self ._view :str ="catalog"
        self ._back_hit_rect =(0 ,0 ,0 ,0 )
        self ._overlay_toggle_rect =(0 ,0 ,0 ,0 )
        self ._get_window_btn_rect =(0 ,0 ,0 ,0 )
        self ._get_objects_btn_rect =(0 ,0 ,0 ,0 )
        self ._guided_config_btn_rect =(0 ,0 ,0 ,0 )
        self ._credits_btn_rect =(0 ,0 ,0 ,0 )
        self ._credits_visible :bool =False 
        self ._credits_shell :tk .Frame |None =None 
        self ._automation_start_btn_rect =(0 ,0 ,0 ,0 )
        self ._brew_automation_armed :bool =False 
        self ._guided_wizard_top :tk .Toplevel |None =None 
        self ._logs_toggle_rect =(0 ,0 ,0 ,0 )
        self ._log_clear_rect =(0 ,0 ,0 ,0 )
        self ._game_log_visible =False 
        self ._game_log_lines :list [str ]=[]
        self ._game_log_top :tk .Toplevel |None =None 
        self ._game_log_shell :tk .Frame |None =None 
        self ._game_log_txt :tk .Text |None =None 
        self ._game_board_rect =(0 ,0 ,1 ,1 )
        # (col, row) → #RRGGBB; strategy / future features can set fills and/or outline overrides.
        self ._hex_cell_fill_colors :dict [tuple [int ,int ],str ]={}
        self ._hex_cell_outline_colors :dict [tuple [int ,int ],str ]={}
        self ._game_get_window_caption =gv.GAME_CAPTION_WINDOW_IDLE 
        self ._game_get_objects_caption =gv.GAME_CAPTION_OBJECTS_IDLE 
        self ._game_prereq_window_ok =False 
        self ._game_prereq_objects_ok =False 
        self ._game_tlopo_overlay =None 
        self ._game_strategy_shell :tk .Frame |None =None 
        self ._game_strategy_row :tk .Frame |None =None 
        self ._game_strategy_text_lbl :tk .Label |None =None 
        self ._game_strategy_menu :tk .Menu |None =None 
        self ._brew_strategy_choice :str =""
        self ._game_config_visible =False 
        self ._config_toggle_rect =(0 ,0 ,0 ,0 )
        self ._game_config_top :tk .Toplevel |None =None 
        self ._game_config_shell :tk .Frame |None =None 
        self ._game_config_delay_var =tk .StringVar (value =str (gv.BREW_AUTOMATION_DELAY_DEFAULT_S ))
        self ._game_config_foreground_settle_var =tk .StringVar (value =str (gv.BREW_AUTOMATION_FOREGROUND_SETTLE_DEFAULT_S ))
        self ._game_config_action_delay_var =tk .StringVar (value =str (gv.BREW_AUTOMATION_ACTION_DELAY_DEFAULT_S ))
        self ._game_config_pre_click_settle_var =tk .StringVar (value =str (gv.BREW_AUTOMATION_PRE_CLICK_SETTLE_DEFAULT_S ))
        self ._game_config_post_click_settle_var =tk .StringVar (value =str (gv.BREW_AUTOMATION_POST_CLICK_SETTLE_DEFAULT_S ))
        self ._game_config_post_drop_sleep_var =tk .StringVar (value =str (gv.BREW_AUTOMATION_POST_DROP_SLEEP_DEFAULT_S ))
        self ._game_config_hand_poll_interval_ms_var =tk .StringVar (value =str (gv.BREW_AUTOMATION_HAND_POLL_INTERVAL_DEFAULT_MS ))
        self ._game_config_board_wait_poll_interval_ms_var =tk .StringVar (value =str (gv.BREW_AUTOMATION_BOARD_WAIT_POLL_INTERVAL_DEFAULT_MS ))
        self ._game_config_live_visual_var =tk .StringVar (value =gv.BREW_LIVE_GAME_VISUAL_DEFAULT )
        self ._game_config_simple_ui_var =tk .BooleanVar (value =False )
        self ._brew_simple_ui :bool =False 
        self ._brew_automation_delay_s =float (gv.BREW_AUTOMATION_DELAY_DEFAULT_S )
        self ._brew_automation_foreground_settle_s =float (gv.BREW_AUTOMATION_FOREGROUND_SETTLE_DEFAULT_S )
        self ._brew_automation_action_delay_s =float (gv.BREW_AUTOMATION_ACTION_DELAY_DEFAULT_S )
        self ._brew_automation_pre_click_settle_s =float (gv.BREW_AUTOMATION_PRE_CLICK_SETTLE_DEFAULT_S )
        self ._brew_automation_post_click_settle_s =float (gv.BREW_AUTOMATION_POST_CLICK_SETTLE_DEFAULT_S )
        self ._brew_automation_post_drop_sleep_s =float (gv.BREW_AUTOMATION_POST_DROP_SLEEP_DEFAULT_S )
        self ._brew_automation_hand_poll_interval_ms =int (gv.BREW_AUTOMATION_HAND_POLL_INTERVAL_DEFAULT_MS )
        self ._brew_automation_board_wait_poll_interval_ms =int (gv.BREW_AUTOMATION_BOARD_WAIT_POLL_INTERVAL_DEFAULT_MS )
        self ._brew_live_game_visual =gv.BREW_LIVE_GAME_VISUAL_DEFAULT 
        self ._brew_board_await_b =0 
        self ._brew_board_await_g =0 
        self ._brew_board_await_r =0 
        self ._brew_again_r =0 
        self ._brew_again_g =0 
        self ._brew_again_b =0 
        self ._brew_again_ok_r =0 
        self ._brew_again_ok_g =0 
        self ._brew_again_ok_b =0 
        self ._potion_failed_continue_r =0 
        self ._potion_failed_continue_g =0 
        self ._potion_failed_continue_b =0 
        self ._game_config_board_b_var =tk .StringVar (value ="0")
        self ._game_config_board_g_var =tk .StringVar (value ="0")
        self ._game_config_board_r_var =tk .StringVar (value ="0")
        self ._game_config_brew_again_r_var =tk .StringVar (value ="0")
        self ._game_config_brew_again_g_var =tk .StringVar (value ="0")
        self ._game_config_brew_again_b_var =tk .StringVar (value ="0")
        self ._game_config_brew_again_ok_r_var =tk .StringVar (value ="0")
        self ._game_config_brew_again_ok_g_var =tk .StringVar (value ="0")
        self ._game_config_brew_again_ok_b_var =tk .StringVar (value ="0")
        self ._game_config_potion_failed_continue_r_var =tk .StringVar (value ="0")
        self ._game_config_potion_failed_continue_g_var =tk .StringVar (value ="0")
        self ._game_config_potion_failed_continue_b_var =tk .StringVar (value ="0")
        self ._brew_piece_display_rgb :dict [str ,tuple [int ,int ,int ]]={}
        self ._brew_ring_median_grid :dict [str ,dict [str ,tuple [int ,int ,int ]]]=_empty_brew_ring_median_grid ()
        self ._game_config_piece_r_vars ={
        t :tk .StringVar (value ="0")for t in gv._CONFIG_PIECE_DISPLAY_ORDER 
        }
        self ._game_config_piece_g_vars ={
        t :tk .StringVar (value ="0")for t in gv._CONFIG_PIECE_DISPLAY_ORDER 
        }
        self ._game_config_piece_b_vars ={
        t :tk .StringVar (value ="0")for t in gv._CONFIG_PIECE_DISPLAY_ORDER 
        }
        self ._game_config_ring_r_vars :dict [str ,dict [str ,tk .StringVar ]]={
        sk :{t :tk .StringVar (value ="0")for t in gv._CONFIG_PIECE_DISPLAY_ORDER }
        for sk in gv._GAME_CONFIG_RING_GRID_SLOTS 
        }
        self ._game_config_ring_g_vars :dict [str ,dict [str ,tk .StringVar ]]={
        sk :{t :tk .StringVar (value ="0")for t in gv._CONFIG_PIECE_DISPLAY_ORDER }
        for sk in gv._GAME_CONFIG_RING_GRID_SLOTS 
        }
        self ._game_config_ring_b_vars :dict [str ,dict [str ,tk .StringVar ]]={
        sk :{t :tk .StringVar (value ="0")for t in gv._CONFIG_PIECE_DISPLAY_ORDER }
        for sk in gv._GAME_CONFIG_RING_GRID_SLOTS 
        }
        self ._load_brew_gui_settings ()
        self ._brew_automation_running =False 
        self ._brew_automation_after_id :str |None =None 
        self ._brew_automation_flip_current_order =False 
        self ._brew_automation_ctx :dict [str ,Any ]|None =None 
        self ._brew_automation_recovery :dict [str ,Any ]|None =None 
        self ._brew_automation_hotkey_listener :Any =None 
        self ._brew_automation_hand_pair_prev :tuple [str ,str ]|None =None 
        self ._brew_automation_hand_poll_attempts =0 
        self ._brew_automation_board_wait_attempts =0 

        if self ._brew_simple_ui :
            self ._recipe_panel_bg =gv .BREW_SIMPLE_UI_PANEL_BG 
            self ._list_panel_bg =gv .BREW_SIMPLE_UI_PANEL_BG 
        elif self ._catalog_template is not None and PIL_OK :
            self ._recipe_panel_bg =_sample_bbox_mean_color (self ._catalog_template ,gv.RECIPE_BBOX )
            self ._list_panel_bg =_sample_bbox_mean_color (self ._catalog_template ,gv.LIST_BBOX )
        else :
            self ._recipe_panel_bg =gv.FALLBACK_PANEL 
            self ._list_panel_bg =gv.FALLBACK_PANEL 

        # Fonts: sizes from ``variables/brew_typography.py``. Cormorant: ``MyScripts/fonts/`` + OFL.
        self ._font_ui_family =resolve_ui_sans_family (root )
        _reg_p =get_cormorant_regular_path ()
        _bold_p =get_cormorant_bold_path ()
        _cormorant_mode :str |None =None 
        if brew_bundled_cormorant_available ():
            _cormorant_mode =brew_prepare_cormorant_fonts (root ,_reg_p ,_bold_p )
        _pt =brew_ty 
        if _cormorant_mode ==BREW_CORMORANT_USE_FONT_FILE :
            _reg =str (_reg_p )
            _bold =str (_bold_p )
            self ._font_recipe_ingredient =tkfont .Font (
            root ,file =_reg ,size =_pt .RECIPE_INGREDIENT_LINE_PT 
            )
            self ._font_family =self ._font_recipe_ingredient .actual ("family")
            self ._font_title =tkfont .Font (
            root ,file =_bold ,size =_pt .RECIPE_POTION_TITLE_PT 
            )
            self ._font_recipe_meta =tkfont .Font (
            root ,file =_reg ,size =_pt .RECIPE_META_LINE_PT 
            )
            self ._font_meta =tkfont .Font (
            root ,
            family =self ._font_ui_family ,
            size =_pt .PANEL_AND_OVERLAY_BODY_PT ,
            )
        elif _cormorant_mode :
            self ._font_family =_cormorant_mode 
            self ._font_title =tkfont .Font (
            root ,
            family =_cormorant_mode ,
            size =_pt .RECIPE_POTION_TITLE_PT ,
            weight =tkfont .BOLD ,
            )
            self ._font_recipe_meta =tkfont .Font (
            root ,
            family =_cormorant_mode ,
            size =_pt .RECIPE_META_LINE_PT ,
            weight =tkfont .BOLD ,
            )
            self ._font_recipe_ingredient =tkfont .Font (
            root ,
            family =_cormorant_mode ,
            size =_pt .RECIPE_INGREDIENT_LINE_PT ,
            weight =tkfont .BOLD ,
            )
            self ._font_meta =tkfont .Font (
            root ,
            family =self ._font_ui_family ,
            size =_pt .PANEL_AND_OVERLAY_BODY_PT ,
            )
        else :
            self ._font_family =resolve_serif_family (root )
            self ._font_title =(self ._font_family ,_pt .RECIPE_POTION_TITLE_PT ,tkfont .BOLD )
            self ._font_recipe_meta =(self ._font_family ,_pt .RECIPE_META_LINE_PT,tkfont .BOLD )
            self ._font_recipe_ingredient =(self ._font_family ,_pt .RECIPE_INGREDIENT_LINE_PT,tkfont .BOLD )
            self ._font_meta =(self ._font_ui_family ,_pt .PANEL_AND_OVERLAY_BODY_PT,tkfont .BOLD )
        self ._font_strategy_menu =(self ._font_ui_family ,10 )
        self ._font_strategy_choice =(self ._font_ui_family ,gv.GAME_STRATEGY_CHOICE_FONT_SIZE )
        self ._brew_strategy_menu_wrap_px =280 

        self ._bg_imgtk :tk .PhotoImage |None =None 
        self ._img_rect =(0 ,0 ,1024 ,768 )
        self ._layout_font_scale =1.0 
        self ._resize_job :str |None =None 
        self ._hover_index :int |None =None 
        self ._recipe_rect =(0 ,0 ,1 ,1 )
        self ._recipe_scroll_px =0 
        self ._recipe_max_scroll =0 
        self ._current_potion_index =0 
        self ._recipe_photo_refs :list [tk .PhotoImage ]=[]

        self ._list_rect =(0 ,0 ,1 ,1 )
        self ._list_scroll_px =0 
        self ._list_max_scroll =0 
        self ._list_selected_index =0 
        self ._list_hover_row :int |None =None 
        self ._list_thumb_h =24 
        self ._list_viewport_inner =1 
        self ._list_scroll_drag :int |None =None 
        self ._list_sb_x0 =0 
        self ._list_sb_x1 =0 
        self ._list_sb_y0 =0 
        self ._list_sb_y1 =0 
        self ._list_thumb_y0 =0 
        self ._list_thumb_y1 =0 
        self ._prev_list_sample :str |None =None 

        if _cormorant_mode ==BREW_CORMORANT_USE_FONT_FILE :
            self ._list_heading_font =tkfont .Font (
            root ,file =str (_bold_p ),size =_pt .LIST_HEADING_PT 
            )
            self ._list_font =tkfont .Font (
            root ,file =str (_reg_p ),size =_pt .LIST_ROW_PT 
            )
        elif _cormorant_mode :
            self ._list_heading_font =tkfont .Font (
            root ,
            family =_cormorant_mode ,
            size =_pt .LIST_HEADING_PT ,
            weight =tkfont .BOLD ,
            )
            self ._list_font =tkfont .Font (
            root ,
            family =_cormorant_mode ,
            size =_pt .LIST_ROW_PT ,
            weight =tkfont .NORMAL ,
            )
        else :
            self ._list_heading_font =tkfont .Font (
            root ,
            family =self ._font_family ,
            size =_pt .LIST_HEADING_PT ,
            weight =tkfont .BOLD ,
            )
            self ._list_font =tkfont .Font (
            root ,
            family =self ._font_family ,
            size =_pt .LIST_ROW_PT ,
            weight =tkfont .BOLD ,
            )
        _list_ls =int (self ._list_font .metrics ("linespace"))
        self ._list_row_h =_list_ls +_pt .LIST_ROW_GAP_EXTRA 
        self ._list_title_block_h =(
        gv.LIST_TITLE_TOP_PAD 
        +int (self ._list_heading_font .metrics ("linespace"))
        +gv.LIST_TITLE_GAP_BELOW 
        )
        self ._list_body_top =0 
        self ._list_body_bottom =0 

        root .title ("TLOPO Potions Master")
        root .minsize (900 ,640 )
        root .geometry ("1024x768")
        root .configure (bg =gv.BLACK )

        self .bg_canvas =tk .Canvas (root ,highlightthickness =0 ,bg =gv.BLACK ,bd =0 ,takefocus =True )
        self .bg_canvas .grid (row =0 ,column =0 ,sticky ="nsew")
        root .rowconfigure (0 ,weight =1 )
        root .columnconfigure (0 ,weight =1 )

        self .bg_canvas .bind ("<MouseWheel>",self ._on_bg_mousewheel )
        self .bg_canvas .bind ("<Button-4>",self ._on_bg_mousewheel )
        self .bg_canvas .bind ("<Button-5>",self ._on_bg_mousewheel )
        self .bg_canvas .bind ("<Motion>",self ._on_canvas_motion )
        self .bg_canvas .bind ("<Leave>",self ._on_canvas_leave )
        self .bg_canvas .bind ("<Button-1>",self ._on_canvas_button1 )
        self .bg_canvas .bind ("<Button-3>",self ._on_canvas_button3 )
        self .bg_canvas .bind ("<B1-Motion>",self ._on_canvas_b1_motion )
        self .bg_canvas .bind ("<ButtonRelease-1>",self ._on_canvas_b1_release )
        self .bg_canvas .bind ("<Up>",self ._on_list_key_up )
        self .bg_canvas .bind ("<Down>",self ._on_list_key_down )
        self .bg_canvas .bind ("<Prior>",self ._on_list_page_up )
        self .bg_canvas .bind ("<Next>",self ._on_list_page_down )

        self .root .bind ("<Configure>",self ._schedule_resize ,add ="+")
        self .root .bind ("<Escape>",self ._on_escape ,add ="+")
        self .root .protocol ("WM_DELETE_WINDOW",self ._on_root_delete_protocol )

        if potions :
            self ._show_potion (0 )

        self .root .after (80 ,self ._initial_layout )

    # --- Delegated methods (same ``self._…`` names as pre-refactor; bodies live in helper packages) ---

    # Window protocol and PIL template selection
    _active_pil_template = _bind_active_pil_template
    _on_escape = _bind_on_escape
    _on_root_delete_protocol = _bind_on_root_delete_protocol

    # ``state_helpers``: disk settings ↔ ``StringVar`` / in-memory state
    _sync_board_bgr_vars_from_state = _bind_sync_board_bgr_vars_from_state
    _sync_automation_timing_vars_from_state = _bind_sync_automation_timing_vars_from_state
    _sync_piece_cfg_rgb_vars_from_state = _bind_sync_piece_cfg_rgb_vars_from_state
    _sync_ring_median_grid_vars_from_state = _bind_sync_ring_median_grid_vars_from_state
    _load_brew_gui_settings = _bind_load_brew_gui_settings
    _save_brew_gui_settings = _bind_save_brew_gui_settings

    # ``automation``: global listener start/stop and bare-Ctrl toggle
    _brew_automation_hotkey_stop = _bind_brew_automation_hotkey_stop
    _brew_automation_hotkey_start = _bind_brew_automation_hotkey_start

    _brew_automation_hotkey_sync = _bind_brew_automation_hotkey_sync

    _on_global_bare_ctrl_toggle = _bind_on_global_bare_ctrl_toggle
    _brew_automation_toggle_from_hotkey = _bind_brew_automation_toggle_from_hotkey

    # ``ui_handlers`` / ``ui_layout``: catalog ↔ game, resize, backgrounds, overlay stacking
    _hit_back_link = _bind_hit_back_link
    _hit_app_chrome_controls = _bind_hit_app_chrome_controls
    _try_handle_app_chrome_click = _bind_try_handle_app_chrome_click
    _confirm_any_island_before_game = _bind_confirm_any_island_before_game
    _enter_game_view = _bind_enter_game_view
    _exit_game_view = _bind_exit_game_view
    _initial_layout = _bind_initial_layout
    _schedule_resize = _bind_schedule_resize
    _resize_done = _bind_resize_done
    _redraw_background = _bind_redraw_background
    _sync_ui_fonts_to_letterbox = _bind_sync_ui_fonts_to_letterbox
    _layout_app_level_chrome = _bind_layout_app_level_chrome
    _layout_overlays = _bind_layout_overlays
    _overlay_panel_bounds = _bind_overlay_panel_bounds
    _game_art_screen_rect = _bind_game_art_screen_rect
    _raise_overlay_tags = _bind_raise_overlay_tags
    _hit_overlay_toggle = _bind_hit_overlay_toggle
    _hit_logs_toggle = _bind_hit_logs_toggle

    # ``config_helpers``: automation panel visibility hit target
    _hit_config_toggle = _bind_hit_config_toggle

    # Game chrome hit targets (window, objects, guided, log clear)
    _hit_log_clear = _bind_hit_log_clear
    _hit_get_window_button = _bind_hit_get_window_button
    _hit_get_objects_button = _bind_hit_get_objects_button
    _hit_guided_config_button = _bind_hit_guided_config_button
    _hit_credits_button = _bind_hit_credits_button
    _destroy_credits_embed = _bind_destroy_credits_embed
    _draw_credits_layer = _bind_draw_credits_layer
    _toggle_brew_credits_panel = _bind_toggle_brew_credits_panel

    _automation_start_button_style = _bind_automation_start_button_style

    _hit_automation_start_button = _bind_hit_automation_start_button

    _refresh_automation_start_button = _bind_refresh_automation_start_button
    _on_automation_start_clicked = _bind_on_automation_start_clicked

    # ``ui_helpers.strategy_board`` + ``layer_helpers``: strategy menu and board memory layer
    _brew_strategy_wrap_two_lines = _bind_brew_strategy_wrap_two_lines

    _apply_brew_strategy_choice = _bind_apply_brew_strategy_choice

    _sync_board_strategy_hex_fills = _bind_sync_board_strategy_hex_fills

    _brew_reset_board_memory = _bind_brew_reset_board_memory

    _ingredient_for_board_line_color = _bind_ingredient_for_board_line_color

    _resolve_exact_piece_png_for_gem = _bind_resolve_exact_piece_png_for_gem

    _brew_board_memory_apply_automation_drop = _bind_brew_board_memory_apply_automation_drop

    _draw_board_memory_pieces_layer = _bind_draw_board_memory_pieces_layer

    _rebuild_brew_strategy_menu = _bind_rebuild_brew_strategy_menu

    _destroy_game_strategy_embed = _bind_destroy_game_strategy_embed

    _draw_game_strategy_embed = _bind_draw_game_strategy_embed

    _refresh_brew_strategy_dropdown = _bind_refresh_brew_strategy_dropdown

    # ``ui_helpers.game_log_embed``: embedded log ``Text`` in the game view
    _destroy_game_log_embed = _bind_destroy_game_log_embed
    _game_log_text_key_guard = staticmethod(_bind_game_log_text_key_guard)
    _sync_game_log_text_body = _bind_sync_game_log_text_body

    _append_game_log = _bind_append_game_log
    _clear_game_log = _bind_clear_game_log

    _refresh_logs_toggle_label = _bind_refresh_logs_toggle_label

    # ``config_helpers`` embed: ring grid, delays, piece RGB, restore defaults
    _refresh_config_toggle_label = _refresh_config_toggle_label
    _destroy_game_config_embed = _destroy_game_config_embed
    _pack_game_config_ring_slot_block = _pack_game_config_ring_slot_block
    _draw_game_config_layer = _draw_game_config_layer
    _restore_game_config_defaults = _restore_game_config_defaults
    _apply_config_delay_from_ui = _apply_config_delay_from_ui
    _brew_piece_color_config_ok = _brew_piece_color_config_ok

    _get_objects_button_style = _bind_get_objects_button_style

    _guided_config_caption = _guided_config_caption

    # Automation run/stop, reschedule, and brew-again RGB checks
    _brew_automation_prereqs_ok = _bind_brew_automation_prereqs_ok
    _brew_automation_strategy_ok = _bind_brew_automation_strategy_ok
    _brew_automation_reset_hand_poll = _bind_brew_automation_reset_hand_poll
    _brew_automation_stop = _bind_brew_automation_stop
    _brew_automation_start = _bind_brew_automation_start
    _brew_automation_reschedule = _bind_brew_automation_reschedule
    _brew_log_automation_hand_summary = _bind_brew_log_automation_hand_summary

    _sample_result_box_median_rgb = staticmethod(_bind_sample_result_box_median_rgb)

    _brew_again_color_matches = _bind_brew_again_color_matches
    _brew_again_ok_color_matches = _bind_brew_again_ok_color_matches
    _potion_failed_continue_color_matches = _bind_potion_failed_continue_color_matches
    _brew_automation_recovery_after_capture = _bind_brew_automation_recovery_after_capture

    _brew_automation_tick_move_to_parking = _bind_brew_automation_tick_move_to_parking
    _brew_automation_tick_recovery = _bind_brew_automation_tick_recovery
    _brew_automation_tick_wait_for_hand_not_board = _bind_brew_automation_tick_wait_for_hand_not_board
    _brew_automation_tick_after_parking_delay = _bind_brew_automation_tick_after_parking_delay

    _brew_automation_hotkey_entry_ok = _bind_brew_automation_hotkey_entry_ok

    # Context menu on the main canvas
    _on_canvas_button3 = _bind_on_canvas_button3

    # ``integration_handlers``: shape overlay and client-rect for screenshots
    _refresh_overlay_toggle_label = _bind_refresh_overlay_toggle_label
    _stop_tlopo_shape_overlay = _bind_stop_tlopo_shape_overlay

    _tlopo_client_rect_for_overlay = _bind_tlopo_client_rect_for_overlay
    _on_shape_overlay_clicked = _bind_on_shape_overlay_clicked

    _draw_game_log_layer = _bind_draw_game_log_layer
    _game_error_log = _bind_game_error_log
    _refresh_game_action_button_labels = _bind_refresh_game_action_button_labels
    _on_get_window_clicked = _bind_on_get_window_clicked
    _on_get_objects_clicked = _bind_on_get_objects_clicked

    # ``guided_wizard`` + list/recipe/hex/listeners (``layer_helpers`` / ``ui_handlers``)
    _open_guided_color_wizard = _open_guided_color_wizard
    _draw_hex_grid_layer = _bind_draw_hex_grid_layer
    _wheel_delta = _bind_wheel_delta
    _on_bg_mousewheel = _bind_on_bg_mousewheel
    _draw_recipe_canvas_layer = _bind_draw_recipe_canvas_layer
    _draw_list_canvas_layer = _bind_draw_list_canvas_layer
    _list_row_at = _bind_list_row_at
    _hit_list_scrollbar = _bind_hit_list_scrollbar
    _hit_list_thumb = _bind_hit_list_thumb
    _ensure_list_row_visible = _bind_ensure_list_row_visible
    _select_list_index = _bind_select_list_index
    _on_canvas_motion = _bind_on_canvas_motion
    _on_canvas_leave = _bind_on_canvas_leave
    _on_canvas_button1 = _bind_on_canvas_button1
    _on_canvas_b1_motion = _bind_on_canvas_b1_motion
    _on_canvas_b1_release = _bind_on_canvas_b1_release
    _on_list_key_up = _bind_on_list_key_up
    _on_list_key_down = _bind_on_list_key_down
    _on_list_page_up = _bind_on_list_page_up
    _on_list_page_down = _bind_on_list_page_down
    _load_piece_thumbnail = _bind_load_piece_thumbnail
    _show_potion = _bind_show_potion


# Aliases for ``main()`` and for ``__init__`` (normalize Tk font scaling on the live root).
_brew_windows_normalize_tk_font_scaling = _bind_brew_windows_normalize_tk_font_scaling
_patch_mss_skip_process_dpi_awareness = _bind_patch_mss_skip_process_dpi_awareness


def main ()->None :
    """CLI entry: DPI setup, catalog load, construct app, run Tk main loop."""
    if sys .platform =="win32"and os .environ .get ("BREW_NO_DPI_INIT","").strip ().lower ()not in (
        "1",
        "true",
        "yes",
    ):
        try :
            from tlopo_client.window import enable_process_dpi_awareness

            enable_process_dpi_awareness ()
        except Exception :
            pass 
    _patch_mss_skip_process_dpi_awareness ()

    catalog_path =get_catalog_path ()
    if not catalog_path .is_file ():
        print (f"Missing catalog: {catalog_path}",file =sys .stderr )
        sys .exit (1 )

    try :
        potions =load_catalog (catalog_path )
    except (json .JSONDecodeError ,OSError ,ValueError )as e :
        print (f"Failed to load catalog: {e}",file =sys .stderr )
        sys .exit (1 )

    root =tk .Tk ()
    PotionPickerApp (root ,potions ,catalog_path =catalog_path )
    root .mainloop ()


if __name__ =="__main__":
    main ()
