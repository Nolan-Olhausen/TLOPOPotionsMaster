from __future__ import annotations

import sys
import tkinter as tk
import tkinter.messagebox as messagebox

import variables.global_variables as gv
from core_helpers import island_display_for_gui ,potion_is_any_island
from ui_layout.simple_mode_layout import _refresh_simple_active_potion_label

def _confirm_any_island_before_game (self ,index :int )->bool :
    """
    If the clicked potion is Any Island, warn that Port Royal is recommended for the
    Port Royal board strategy. Returns True to open the game view, False to stay on catalog.
    """
    if not self .potions :
        return False 
    index =max (0 ,min (index ,len (self .potions )-1 ))
    pot =self .potions [index ]
    isl =island_display_for_gui (str (pot .get ("island")or ""))
    if potion_is_any_island (pot ):
        return messagebox .askokcancel (
        "Any Island potion",
        "This recipe is Any Island. It is recommended to brew Any Island potions on "
        "Port Royal so you can use the Port Royal board strategy.\n\n"
        "Continue to the brewing board anyway?",
        parent =self .root ,
        )
    if isl in ("Cuba","Tortuga & Bilgewater","Padres del Fuego"):
        return messagebox .askokcancel (
        f"{isl} potion warning",
        "This island introduces a 4th color, so there is no fail-proof strategy.\n\n"
        "Higher-level ingredients reduce your chance of success.\n\n"
        "The app can recover failed games and navigate back to the selected potion, "
        "but some brews will still fail.\n\n"
        "Continue to the brewing board anyway?",
        parent =self .root ,
        )
    return True 


def _enter_game_view (self ,index :int )->None :
    if not self .potions :
        return 
    if self ._game_template is None :
        print (
        "Missing Brewing/GUI/BrewingGameGUI.png — add that file to open the brewing screen.",
        file =sys .stderr ,
        )
        return 
    index =max (0 ,min (index ,len (self .potions )-1 ))
    self ._view ="game"
    self ._credits_visible =False 
    # Get Window / Get Locations state is app-level — do not reset when opening another potion.
    self ._brew_automation_armed =False 
    self ._list_selected_index =index 
    self ._current_potion_index =index 
    self ._brew_strategy_choice =""
    self ._hex_cell_fill_colors .clear ()
    self ._hex_cell_outline_colors .clear ()
    self ._brew_reset_board_memory ()
    self ._brew_automation_stop ()
    self ._brew_automation_flip_current_order =False 
    self ._recipe_scroll_px =0 
    self ._hover_index =None 
    self ._list_hover_row =None 
    self .bg_canvas .delete ("list_ui")
    self .bg_canvas .delete ("recipe_ui")
    self ._redraw_background ()
    self ._layout_overlays ()


def _exit_game_view (self )->None :
    if self ._view !="game":
        return 
    self ._brew_automation_armed =False 
    self ._brew_automation_hotkey_stop ()
    self ._brew_automation_stop ("left game view",resync_hotkey =False )
    self ._destroy_game_strategy_embed ()
    self ._hex_cell_fill_colors .clear ()
    self ._hex_cell_outline_colors .clear ()
    self .bg_canvas .delete ("board_memory_piece")
    self ._brew_reset_board_memory ()
    self ._brew_board_sim =None 
    self ._brew_board_memory =None 
    self ._board_memory_photo_refs .clear ()
    self ._view ="catalog"
    self .bg_canvas .config (cursor ="")
    self .bg_canvas .delete ("game_ui")
    self .bg_canvas .delete ("recipe_ui")
    self ._hover_index =None 
    self ._list_hover_row =None 
    self ._redraw_background ()
    self ._layout_overlays ()
    self ._show_potion (self ._list_selected_index )


def _show_potion (self ,index :int )->None :
    if not self .potions :
        return 
    index =max (0 ,min (index ,len (self .potions )-1 ))
    self ._current_potion_index =index 
    self ._recipe_scroll_px =0 
    self ._draw_recipe_canvas_layer ()
    self ._raise_overlay_tags ()
    if self ._view =="game":
        self ._refresh_brew_strategy_dropdown ()
    _refresh_simple_active_potion_label (self )


