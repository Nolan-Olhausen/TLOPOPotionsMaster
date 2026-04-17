from __future__ import annotations

import tkinter as tk
import variables.global_variables as gv

def _list_row_at (self ,x :int ,y :int )->int |None :
    if not self .potions :
        return None 
    lx ,ly ,lw ,lh =self ._list_rect 
    if not (lx <=x <lx +lw and ly <=y <ly +lh ):
        return None 
    body_top =ly +self ._list_title_block_h -6 
    body_bottom =ly +lh -gv.LIST_BODY_BOTTOM_PAD 
    if y <body_top or y >=body_bottom :
        return None 
    sb_w =int (getattr (self ,"_list_sb_draw_w",gv .LIST_SCROLLBAR_W )or gv .LIST_SCROLLBAR_W )
    sb_cut =lx +lw -sb_w -6 
    if x >=sb_cut :
        return None 
    rel_y =y -body_top +self ._list_scroll_px 
    idx =int (rel_y //self ._list_row_h )
    if not (0 <=idx <len (self .potions )):
        return None 
    row_top =body_top +idx *self ._list_row_h -self ._list_scroll_px 
    row_bot =row_top +self ._list_row_h 
    if row_bot <=body_top or row_top >=body_bottom :
        return None 
    return idx 


def _ensure_list_row_visible (self ,index :int )->None :
    if self ._list_max_scroll <=0 :
        return 
    _lx ,ly ,_lw ,lh =self ._list_rect 
    body_top =ly +self ._list_title_block_h -6 
    body_bottom =ly +lh -gv.LIST_BODY_BOTTOM_PAD 
    viewport_h =max (0 ,body_bottom -body_top )
    row_top =index *self ._list_row_h 
    row_bot =row_top +self ._list_row_h 
    view_top =self ._list_scroll_px 
    view_bot =view_top +viewport_h 
    if row_top <view_top :
        self ._list_scroll_px =row_top 
    elif row_bot >view_bot :
        self ._list_scroll_px =max (0 ,row_bot -viewport_h )
    self ._list_scroll_px =max (0 ,min (self ._list_max_scroll ,self ._list_scroll_px ))


def _select_list_index (self ,index :int )->None :
    if not self .potions :
        return 
    index =max (0 ,min (index ,len (self .potions )-1 ))
    prev_index =int (getattr (self ,"_current_potion_index",index ))
    if self ._view =="game"and index !=prev_index :
        self ._brew_strategy_choice =""
        self ._hex_cell_fill_colors .clear ()
        self ._hex_cell_outline_colors .clear ()
        self .bg_canvas .delete ("board_memory_piece")
        self ._brew_reset_board_memory ()
    self ._list_selected_index =index 
    self ._list_hover_row =None 
    self ._hover_index =None 
    self ._show_potion (index )
    self ._draw_list_canvas_layer ()
    self ._ensure_list_row_visible (index )
    self ._draw_list_canvas_layer ()
    self ._raise_overlay_tags ()


def _on_list_key_up (self ,_event :tk .Event )->None :
    if self ._view =="game":
        return 
    if not self .potions :
        return 
    i =max (0 ,self ._list_selected_index -1 )
    self ._select_list_index (i )


def _on_list_key_down (self ,_event :tk .Event )->None :
    if self ._view =="game":
        return 
    if not self .potions :
        return 
    i =min (len (self .potions )-1 ,self ._list_selected_index +1 )
    self ._select_list_index (i )


def _on_list_page_up (self ,_event :tk .Event )->None :
    if self ._view =="game":
        return 
    if self ._list_max_scroll <=0 :
        return 
    step =max (self ._list_row_h ,self ._list_viewport_inner -self ._list_row_h )
    self ._list_scroll_px =max (0 ,self ._list_scroll_px -step )
    self ._draw_list_canvas_layer ()
    self ._raise_overlay_tags ()


def _on_list_page_down (self ,_event :tk .Event )->None :
    if self ._view =="game":
        return 
    if self ._list_max_scroll <=0 :
        return 
    step =max (self ._list_row_h ,self ._list_viewport_inner -self ._list_row_h )
    self ._list_scroll_px =min (self ._list_max_scroll ,self ._list_scroll_px +step )
    self ._draw_list_canvas_layer ()
    self ._raise_overlay_tags ()


