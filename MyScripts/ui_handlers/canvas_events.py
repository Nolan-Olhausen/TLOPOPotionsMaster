from __future__ import annotations

import sys
import tkinter as tk

def _hit_back_link (self ,x :int ,y :int )->bool :
    if self ._view !="game":
        return False 
    bx0 ,by0 ,bx1 ,by1 =self ._back_hit_rect 
    # (bx1, by1) are exclusive right/bottom edges (half-open hit test).
    return bx0 <=x <bx1 and by0 <=y <by1 


def _hit_overlay_toggle (self ,x :int ,y :int )->bool :
    ox0 ,oy0 ,ox1 ,oy1 =self ._overlay_toggle_rect 
    return ox0 <=x <ox1 and oy0 <=y <oy1 


def _hit_logs_toggle (self ,x :int ,y :int )->bool :
    lx0 ,ly0 ,lx1 ,ly1 =self ._logs_toggle_rect 
    return lx0 <=x <lx1 and ly0 <=y <ly1 


def _hit_log_clear (self ,x :int ,y :int )->bool :
    if not self ._game_log_visible :
        return False 
    cx0 ,cy0 ,cx1 ,cy1 =self ._log_clear_rect 
    if cx1 <=cx0 or cy1 <=cy0 :
        return False 
    return cx0 <=x <cx1 and cy0 <=y <cy1 


def _hit_get_window_button (self ,x :int ,y :int )->bool :
    wx0 ,wy0 ,wx1 ,wy1 =self ._get_window_btn_rect 
    return wx0 <=x <wx1 and wy0 <=y <wy1 


def _hit_get_objects_button (self ,x :int ,y :int )->bool :
    if not self ._game_prereq_window_ok :
        return False 
    ox0 ,oy0 ,ox1 ,oy1 =self ._get_objects_btn_rect 
    return ox0 <=x <ox1 and oy0 <=y <oy1 


def _hit_guided_config_button (self ,x :int ,y :int )->bool :
    gx0 ,gy0 ,gx1 ,gy1 =self ._guided_config_btn_rect 
    return gx0 <=x <gx1 and gy0 <=y <gy1 


def _hit_credits_button (self ,x :int ,y :int )->bool :
    if self ._view !="catalog":
        return False 
    cx0 ,cy0 ,cx1 ,cy1 =self ._credits_btn_rect 
    return cx0 <=x <cx1 and cy0 <=y <cy1 


def _hit_automation_start_button (self ,x :int ,y :int )->bool :
    if self ._view !="game":
        return False 
    ax0 ,ay0 ,ax1 ,ay1 =self ._automation_start_btn_rect 
    if not (ax0 <=x <ax1 and ay0 <=y <ay1 ):
        return False 
    return self ._brew_automation_armed or self ._brew_automation_prereqs_ok ()


def _hit_app_chrome_controls (self ,x :int ,y :int )->bool :
    """Shared top/lower buttons: config, logs, overlay, window, locations, guided."""
    if self ._hit_config_toggle (x ,y ):
        return True 
    if self ._hit_logs_toggle (x ,y ):
        return True 
    if self ._hit_overlay_toggle (x ,y ):
        return True 
    if self ._hit_get_window_button (x ,y ):
        return True 
    if self ._hit_get_objects_button (x ,y ):
        return True 
    if self ._hit_guided_config_button (x ,y ):
        return True 
    return False 


def _try_handle_app_chrome_click (self ,x :int ,y :int )->bool :
    if not self ._hit_app_chrome_controls (x ,y ):
        return False 
    if self ._hit_config_toggle (x ,y ):
        self ._game_config_visible =not self ._game_config_visible 
        self ._refresh_config_toggle_label ()
        self ._draw_game_config_layer ()
        top_cfg =getattr (self ,"_game_config_top",None )
        if top_cfg is not None :
            try :
                if top_cfg .winfo_exists ():
                    top_cfg .lift ()
            except tk .TclError :
                pass 
        self .bg_canvas .tag_raise ("game_ui")
        return True 
    if self ._hit_logs_toggle (x ,y ):
        self ._game_log_visible =not self ._game_log_visible 
        self ._refresh_logs_toggle_label ()
        self ._draw_game_log_layer ()
        top_log =getattr (self ,"_game_log_top",None )
        if top_log is not None :
            try :
                if top_log .winfo_exists ():
                    top_log .lift ()
            except tk .TclError :
                pass 
        self .bg_canvas .tag_raise ("game_ui")
        return True 
    if self ._hit_get_window_button (x ,y ):
        self ._on_get_window_clicked ()
        return True 
    if self ._hit_get_objects_button (x ,y ):
        self ._on_get_objects_clicked ()
        return True 
    if self ._hit_guided_config_button (x ,y ):
        self ._open_guided_color_wizard ()
        return True 
    if self ._hit_overlay_toggle (x ,y ):
        self ._on_shape_overlay_clicked ()
        return True 
    return False 


def _on_canvas_button3 (self ,event :tk .Event )->None :
    if self ._view !="game":
        return 
    self ._brew_automation_flip_current_order =not self ._brew_automation_flip_current_order 
    state ="right token treated as left (flipped)"if self ._brew_automation_flip_current_order else "left-to-right order (normal)"
    self ._append_game_log (f"[Automation] Current pair read order: {state}")


def _wheel_delta (self ,event :tk .Event )->int :
    num =getattr (event ,"num",None )
    if num ==4 :
        return 28 
    if num ==5 :
        return -28 
    if sys .platform =="darwin":
        return int (-1 *event .delta )
    return int (-event .delta /120 )*28 


def _on_bg_mousewheel (self ,event :tk .Event )->None :
    delta =self ._wheel_delta (event )
    lx ,ly ,lw ,lh =self ._list_rect 
    if lx <=event .x <lx +lw and ly <=event .y <ly +lh :
        if self ._list_max_scroll >0 :
            self ._list_scroll_px =max (0 ,min (self ._list_max_scroll ,self ._list_scroll_px +delta ))
            self ._draw_list_canvas_layer ()
            self ._raise_overlay_tags ()
        return 

    rx ,ry ,rw ,rh =self ._recipe_rect 
    if not (rx <=event .x <rx +rw and ry <=event .y <ry +rh ):
        return 
    if self ._recipe_max_scroll <=0 :
        return 
    self ._recipe_scroll_px =max (0 ,min (self ._recipe_max_scroll ,self ._recipe_scroll_px +delta ))
    self ._draw_recipe_canvas_layer ()
    self ._raise_overlay_tags ()


def _hit_list_scrollbar (self ,x :int ,y :int )->bool :
    return (
    self ._list_sb_x0 <=x <=self ._list_sb_x1 
    and self ._list_sb_y0 <=y <=self ._list_sb_y1 
    and self ._list_max_scroll >0 
    )


def _hit_list_thumb (self ,x :int ,y :int )->bool :
    return self ._hit_list_scrollbar (x ,y )and self ._list_thumb_y0 <=y <=self ._list_thumb_y1 


def _on_canvas_motion (self ,event :tk .Event )->None :
    if self ._list_scroll_drag is not None :
        return 
    simple_game_list =self ._view =="game"and getattr (self ,"_brew_simple_ui",False )
    if simple_game_list :
        idx =self ._list_row_at (event .x ,event .y )
        if idx is not None :
            self .bg_canvas .config (cursor ="hand2")
            if idx !=self ._list_hover_row :
                self ._list_hover_row =idx 
                self ._draw_list_canvas_layer ()
                self ._raise_overlay_tags ()
            return 
        if self ._list_hover_row is not None :
            self ._list_hover_row =None 
            self ._draw_list_canvas_layer ()
            self ._raise_overlay_tags ()
    if self ._view =="game":
        cur =(
        "hand2"
        if self ._hit_back_link (event .x ,event .y )
        or self ._hit_automation_start_button (event .x ,event .y )
        or self ._hit_app_chrome_controls (event .x ,event .y )
        else ""
        )
        self .bg_canvas .config (cursor =cur )
        return 
    if self ._hit_app_chrome_controls (event .x ,event .y ):
        self .bg_canvas .config (cursor ="hand2")
        return 
    if self ._hit_credits_button (event .x ,event .y ):
        self .bg_canvas .config (cursor ="hand2")
        return 
    idx =self ._list_row_at (event .x ,event .y )
    if idx is not None :
        if idx !=self ._hover_index :
            self ._hover_index =idx 
            self ._show_potion (idx )
        if idx !=self ._list_hover_row :
            self ._list_hover_row =idx 
            self ._draw_list_canvas_layer ()
            self ._raise_overlay_tags ()
    else :
        if self ._hover_index is not None :
            self ._hover_index =None 
            self ._show_potion (self ._list_selected_index )
        if self ._list_hover_row is not None :
            self ._list_hover_row =None 
            self ._draw_list_canvas_layer ()
            self ._raise_overlay_tags ()


def _on_canvas_leave (self ,_event :tk .Event )->None :
    if self ._list_scroll_drag is not None :
        return 
    self .bg_canvas .config (cursor ="")
    if self ._view =="game":
        if getattr (self ,"_brew_simple_ui",False )and self ._list_hover_row is not None :
            self ._list_hover_row =None 
            self ._draw_list_canvas_layer ()
            self ._raise_overlay_tags ()
        return 
    self ._hover_index =None 
    self ._list_hover_row =None 
    if self .potions :
        self ._show_potion (self ._list_selected_index )
        self ._draw_list_canvas_layer ()
        self ._raise_overlay_tags ()


def _on_canvas_button1 (self ,event :tk .Event )->None :
    self .bg_canvas .focus_set ()
    if self ._try_handle_app_chrome_click (event .x ,event .y ):
        return 
    if self ._view =="catalog" and self ._hit_credits_button (event .x ,event .y ):
        self ._toggle_brew_credits_panel ()
        return 
    if self ._view =="game":
        if self ._hit_automation_start_button (event .x ,event .y ):
            self ._on_automation_start_clicked ()
            return 
        if self ._hit_back_link (event .x ,event .y ):
            self ._exit_game_view ()
            return 
        if getattr (self ,"_brew_simple_ui",False ):
            if self ._list_max_scroll >0 and self ._hit_list_scrollbar (event .x ,event .y ):
                if self ._hit_list_thumb (event .x ,event .y ):
                    self ._list_scroll_drag =int (event .y -self ._list_thumb_y0 )
                else :
                    track_len =max (1 ,self ._list_viewport_inner -self ._list_thumb_h )
                    rel =event .y -self ._list_body_top -self ._list_thumb_h //2 
                    target =int (rel /track_len *self ._list_max_scroll )
                    self ._list_scroll_px =max (0 ,min (self ._list_max_scroll ,target ))
                    self ._draw_list_canvas_layer ()
                    self ._raise_overlay_tags ()
                return 
            idx =self ._list_row_at (event .x ,event .y )
            if idx is not None :
                self ._select_list_index (idx )
                return 
        return 
    if self ._list_max_scroll >0 and self ._hit_list_scrollbar (event .x ,event .y ):
        if self ._hit_list_thumb (event .x ,event .y ):
            self ._list_scroll_drag =int (event .y -self ._list_thumb_y0 )
        else :
            track_len =max (1 ,self ._list_viewport_inner -self ._list_thumb_h )
            rel =event .y -self ._list_body_top -self ._list_thumb_h //2 
            target =int (rel /track_len *self ._list_max_scroll )
            self ._list_scroll_px =max (0 ,min (self ._list_max_scroll ,target ))
            self ._draw_list_canvas_layer ()
            self ._raise_overlay_tags ()
        return 

    idx =self ._list_row_at (event .x ,event .y )
    if idx is not None :
        if not self ._confirm_any_island_before_game (idx ):
            return 
        self ._enter_game_view (idx )


def _on_canvas_b1_motion (self ,event :tk .Event )->None :
    if self ._list_scroll_drag is None :
        return 
    grab =self ._list_scroll_drag 
    track_top =self ._list_body_top 
    track_len =max (1 ,self ._list_viewport_inner -self ._list_thumb_h )
    thumb_top =event .y -grab 
    rel =thumb_top -track_top 
    new_scroll =int (rel /track_len *self ._list_max_scroll )
    self ._list_scroll_px =max (0 ,min (self ._list_max_scroll ,new_scroll ))
    self ._draw_list_canvas_layer ()
    self ._raise_overlay_tags ()


def _on_canvas_b1_release (self ,_event :tk .Event )->None :
    self ._list_scroll_drag =None 


