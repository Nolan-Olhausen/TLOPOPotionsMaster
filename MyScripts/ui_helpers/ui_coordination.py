from __future__ import annotations

import variables.global_variables as gv

def _brew_automation_hotkey_sync (self )->None :
    """Attach Left Ctrl only while automation is running or the Start button is armed (and prereqs hold)."""
    if self ._view !="game":
        self ._brew_automation_hotkey_stop ()
        return 
    if (
    self ._brew_automation_armed 
    and not self ._brew_automation_running 
    and not self ._brew_automation_prereqs_ok ()
    ):
        self ._brew_automation_armed =False 
    want =self ._brew_automation_running or (
    self ._brew_automation_armed and self ._brew_automation_prereqs_ok ()
    )
    if want :
        self ._brew_automation_hotkey_start ()
    else :
        self ._brew_automation_hotkey_stop ()
    self ._refresh_automation_start_button ()


def _raise_overlay_tags (self )->None :
    self .bg_canvas .tag_raise ("list_ui")
    self .bg_canvas .tag_raise ("recipe_ui")
    if self ._view =="game":
        self .bg_canvas .tag_raise ("hex_grid")
        if self .bg_canvas .find_withtag ("board_memory_piece"):
            self .bg_canvas .tag_raise ("board_memory_piece")
    if self .bg_canvas .find_withtag ("game_ui"):
        self .bg_canvas .tag_raise ("game_ui")
    if self .bg_canvas .find_withtag ("credits_layer"):
        self .bg_canvas .tag_raise ("credits_layer")


def _append_game_log (self ,line :str )->None :
    """Append one line to the in-memory game log (visible when the log panel is open)."""
    if line =="":
        self ._game_log_lines .append ("")
    else :
        for part in line .splitlines ():
            self ._game_log_lines .append (part )
    over =len (self ._game_log_lines )-gv.GAME_LOG_MAX_LINES 
    if over >0 :
        self ._game_log_lines =self ._game_log_lines [over :]
    if self ._game_log_visible :
        self ._sync_game_log_text_body ()
        self .bg_canvas .tag_raise ("game_ui")
        if self .bg_canvas .find_withtag ("credits_layer"):
            self .bg_canvas .tag_raise ("credits_layer")


def _clear_game_log (self )->None :
    self ._game_log_lines .clear ()
    if self ._game_log_visible :
        self ._sync_game_log_text_body ()
        self .bg_canvas .tag_raise ("game_ui")
        if self .bg_canvas .find_withtag ("credits_layer"):
            self .bg_canvas .tag_raise ("credits_layer")


def _refresh_game_action_button_labels (self )->None :
    ids =self .bg_canvas .find_withtag ("get_window_label")
    if ids :
        self .bg_canvas .itemconfigure (
        ids [0 ],
        text =self ._game_get_window_caption ,
        justify ="center",
        )
    ob_fill ,ob_outline ,ob_text =self ._get_objects_button_style ()
    ids_orec =self .bg_canvas .find_withtag ("get_objects_btn")
    if ids_orec :
        self .bg_canvas .itemconfigure (
        ids_orec [0 ],
        fill =ob_fill ,
        outline =ob_outline ,
        )
    ids_o =self .bg_canvas .find_withtag ("get_objects_label")
    if ids_o :
        self .bg_canvas .itemconfigure (
        ids_o [0 ],
        text =self ._game_get_objects_caption ,
        fill =ob_text ,
        justify ="center",
        )
    ids_gc =self .bg_canvas .find_withtag ("guided_config_label")
    if ids_gc :
        self .bg_canvas .itemconfigure (
        ids_gc [0 ],
        text =self ._guided_config_caption (),
        justify ="center",
        )
    self ._refresh_automation_start_button ()


