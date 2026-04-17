from __future__ import annotations

from typing import Any 

import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as messagebox
import variables.brew_typography as brew_ty
import variables.global_variables as gv

def _rgb888_to_hex(r: int, g: int, b: int) -> str:
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02x}{g:02x}{b:02x}"

def _tlopo_piece_color_word(token: str) -> str:
    return gv._TLOPO_PIECE_COLOR_WORDS.get(token, token)

def _empty_brew_ring_median_grid() -> dict[str, dict[str, tuple[int, int, int]]]:
    return {
        "next_piece_left": {},
        "next_piece_right": {},
        "current_piece_left": {},
        "current_piece_right": {},
    }

def _brew_rgb_config_minimum_ok(
    piece_rgb: dict[str, tuple[int, int, int]],
    board_r: int,
    board_g: int,
    board_b: int,
) -> bool:
    for tok in ("R", "G", "B"):
        r, g, b = piece_rgb.get(tok, (0, 0, 0))
        if (r | g | b) == 0:
            return False
    if (int(board_r) | int(board_g) | int(board_b)) == 0:
        return False
    return True

def _normalize_live_game_visual_mode(v: str | None) -> str:
    s = str(v or "").strip().lower()
    if s == "none":
        return "None"
    if s == "exact":
        return "Exact"
    return "Simple"

def _hit_config_toggle (self ,x :int ,y :int )->bool :
    cx0 ,cy0 ,cx1 ,cy1 =self ._config_toggle_rect 
    return cx0 <=x <cx1 and cy0 <=y <cy1 


def _refresh_config_toggle_label (self )->None :
    ids =self .bg_canvas .find_withtag ("config_toggle_label")
    if ids :
        self .bg_canvas .itemconfigure (
        ids [0 ],
        text ="Hide config"if self ._game_config_visible else "Config Panel",
        )


def _destroy_game_config_embed (self )->None :
    top =getattr (self ,"_game_config_top",None )
    if top is not None :
        try :
            top .destroy ()
        except tk .TclError :
            pass 
        self ._game_config_top =None 
    self ._game_config_shell =None 


def _bind_mousewheel_recursive (widget :tk .Misc ,callback )->None :
    widget .bind ("<MouseWheel>",callback ,add ="+")
    widget .bind ("<Button-4>",callback ,add ="+")
    widget .bind ("<Button-5>",callback ,add ="+")
    for child in widget .winfo_children ():
        _bind_mousewheel_recursive (child ,callback )


def _pack_game_config_ring_slot_block (
    self ,parent :tk .Frame ,slot_key :str ,*,panel_font :Any |None =None 
)->None :
    row_font =panel_font if panel_font is not None else self ._font_meta 
    title =(
    gv._TLOPO_NEXT_PIECE_TITLES .get (slot_key )
    or gv._TLOPO_CURRENT_PIECE_TITLES .get (slot_key )
    or slot_key .replace ("_"," ").title ()
    )
    tk .Label (
    parent ,
    text =title ,
    font =(self ._font_family ,13 ,tkfont .BOLD ),
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    anchor =tk .W ,
    ).pack (anchor =tk .W ,pady =(6 ,2 ))
    for tok in gv._CONFIG_PIECE_DISPLAY_ORDER :
        row =tk .Frame (parent ,bg =gv.GAME_LOG_PANEL_FILL )
        row .pack (anchor =tk .W ,fill =tk .X ,pady =1 )
        disp =_tlopo_piece_color_word (tok )
        tk .Label (
        row ,
        text =f"{disp} ({tok})",
        font =row_font ,
        fg =gv.GAME_LOG_TEXT ,
        bg =gv.GAME_LOG_PANEL_FILL ,
        width =12 ,
        anchor =tk .W ,
        ).pack (side =tk .LEFT )
        try :
            rv =int (self ._game_config_ring_r_vars [slot_key ][tok ].get ()or "0")
            gvv =int (self ._game_config_ring_g_vars [slot_key ][tok ].get ()or "0")
            bv =int (self ._game_config_ring_b_vars [slot_key ][tok ].get ()or "0")
            rv =max (0 ,min (255 ,rv ))
            gvv =max (0 ,min (255 ,gvv ))
            bv =max (0 ,min (255 ,bv ))
        except ValueError :
            rv =gvv =bv =0 
        phx =_rgb888_to_hex (rv ,gvv ,bv )if (rv |gvv |bv )else "#2a2a2e"
        pcv =tk .Canvas (
        row ,
        width =22 ,
        height =22 ,
        highlightthickness =1 ,
        highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
        bg =gv.GAME_LOG_PANEL_FILL ,
        )
        pcv .pack (side =tk .LEFT ,padx =(4 ,6 ))
        pcv .create_rectangle (1 ,1 ,21 ,21 ,fill =phx ,outline =gv.GAME_LOG_PANEL_OUTLINE )
        for lab ,var in (
        ("R",self ._game_config_ring_r_vars [slot_key ][tok ]),
        ("G",self ._game_config_ring_g_vars [slot_key ][tok ]),
        ("B",self ._game_config_ring_b_vars [slot_key ][tok ]),
        ):
            tk .Label (
            row ,
            text =lab ,
            font =row_font ,
            fg =gv.GAME_LOG_TEXT ,
            bg =gv.GAME_LOG_PANEL_FILL ,
            ).pack (side =tk .LEFT )
            tk .Entry (
            row ,
            textvariable =var ,
            width =3 ,
            font =row_font ,
            bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
            fg =gv.GAME_LOG_TEXT ,
            insertbackground =gv.GAME_LOG_TEXT ,
            highlightthickness =1 ,
            highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
            highlightcolor =gv.GAME_LOG_PANEL_OUTLINE ,
            ).pack (side =tk .LEFT ,padx =(2 ,4 ))


def _draw_game_config_layer (self )->None :
    if not self ._game_config_visible :
        self ._destroy_game_config_embed ()
        try :
            self .bg_canvas .delete ("game_config_layer")
        except tk .TclError :
            pass 
        return 
    prev =getattr (self ,"_game_config_top",None )
    if prev is not None :
        try :
            if prev .winfo_exists ():
                prev .lift ()
                return 
        except tk .TclError :
            pass 
    self ._destroy_game_config_embed ()
    try :
        self .bg_canvas .delete ("game_config_layer")
    except tk .TclError :
        pass 
    self ._sync_board_bgr_vars_from_state ()
    self ._sync_piece_cfg_rgb_vars_from_state ()
    self ._sync_ring_median_grid_vars_from_state ()

    win =tk .Toplevel (self .root )
    self ._game_config_top =win 
    win .title ("Automation config")
    win .transient (self .root )
    try :
        win .geometry (gv .GAME_CONFIG_POPUP_GEOMETRY )
    except tk .TclError :
        pass 
    cfg_title =(
    getattr (self ,"_font_family","TkDefaultFont"),
    brew_ty .RECIPE_POTION_TITLE_PT ,
    tkfont .BOLD ,
    )
    cfg_meta =(
    self ._font_ui_family ,
    brew_ty .PANEL_AND_OVERLAY_BODY_PT ,
    tkfont .BOLD ,
    )

    def _on_config_popup_delete ()->None :
        self ._game_config_visible =False 
        self ._refresh_config_toggle_label ()
        self ._destroy_game_config_embed ()

    win .protocol ("WM_DELETE_WINDOW",_on_config_popup_delete )

    inner_w =int (gv .GAME_CONFIG_POPUP_CANVAS_W )

    shell =tk .Frame (win ,bg =gv.GAME_LOG_PANEL_FILL ,highlightthickness =0 )
    shell .pack (fill =tk .BOTH ,expand =True )
    scroll_wrap =tk .Frame (shell ,bg =gv.GAME_LOG_PANEL_FILL )
    scroll_wrap .pack (fill =tk .BOTH ,expand =True ,padx =4 ,pady =4 )
    cv =tk .Canvas (
    scroll_wrap ,
    height =int (gv .GAME_CONFIG_POPUP_CANVAS_H ),
    width =inner_w ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    highlightthickness =0 ,
    )
    scr_vis =tk .Canvas (
    scroll_wrap ,
    width =12 ,
    bg =gv.GAME_LOG_SCROLLBAR_TROUGH ,
    highlightthickness =0 ,
    bd =0 ,
    )
    inner =tk .Frame (cv ,bg =gv.GAME_LOG_PANEL_FILL )
    inner_win =cv .create_window ((0 ,0 ),window =inner ,anchor =tk .NW )

    def _inner_cfg (_e :tk .Event |None =None )->None :
        cv .configure (scrollregion =cv .bbox ("all"))

    def _cv_cfg (e :tk .Event )->None :
        try :
            cv .itemconfigure (inner_win ,width =e .width )
        except tk .TclError :
            pass 

    def _sync_scroll_visual (first :str ,last :str )->None :
        try :
            f =max (0.0 ,min (1.0 ,float (first )))
            l =max (0.0 ,min (1.0 ,float (last )))
        except (TypeError ,ValueError ):
            return
        scr_vis .delete ("all")
        w =max (2 ,int (scr_vis .winfo_width ()))
        h =max (4 ,int (scr_vis .winfo_height ()))
        scr_vis .create_rectangle (0 ,0 ,w ,h ,fill =gv.GAME_LOG_SCROLLBAR_TROUGH ,outline ="")
        if l -f >=0.999 :
            thumb_y0 ,thumb_y1 =1 ,h -1 
        else :
            y0 =int (f *h )
            y1 =int (l *h )
            min_h =18 
            if y1 -y0 <min_h :
                y1 =min (h -1 ,y0 +min_h )
            thumb_y0 =max (1 ,min (h -2 ,y0 ))
            thumb_y1 =max (thumb_y0 +2 ,min (h -1 ,y1 ))
        scr_vis .create_rectangle (
        1 ,
        thumb_y0 ,
        w -1 ,
        thumb_y1 ,
        fill =gv.GAME_LOG_SCROLLBAR_BG ,
        outline =gv.GAME_LOG_PANEL_OUTLINE ,
        width =1 ,
        )

    def _on_scroll_vis_click (ev :tk .Event )->str :
        h =max (1 ,int (scr_vis .winfo_height ()))
        frac =max (0.0 ,min (1.0 ,float (ev .y )/float (h )))
        cv .yview_moveto (frac )
        return "break"

    inner .bind ("<Configure>",lambda _e :_inner_cfg ())
    cv .bind ("<Configure>",_cv_cfg )

    def _mw (ev :tk .Event )->str |None :
        steps =0 
        delta =int (getattr (ev ,"delta",0 )or 0 )
        if delta :
            steps =int (-delta /120 )
            if steps ==0 :
                steps =-1 if delta >0 else 1 
        elif getattr (ev ,"num",None )==4 :
            steps =-1 
        elif getattr (ev ,"num",None )==5 :
            steps =1 
        if steps :
            cv .yview_scroll (steps ,"units")
            return "break"
        return None

    cv .configure (
    yscrollcommand =lambda f ,l :(
    _sync_scroll_visual (f ,l ),
    ),
    )
    cv .pack (side =tk .LEFT ,fill =tk .BOTH ,expand =True )
    scr_vis .pack (side =tk .RIGHT ,fill =tk .Y )
    scr_vis .bind ("<Configure>",lambda _e :_sync_scroll_visual (*cv .yview ()))
    scr_vis .bind ("<Button-1>",_on_scroll_vis_click )
    scr_vis .bind ("<B1-Motion>",_on_scroll_vis_click )

    tk .Label (
    inner ,
    text ="Automation config",
    font =cfg_title ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    ).pack (anchor =tk .W ,padx =8 ,pady =(6 ,2 ))
    tk .Label (
    inner ,
    text =(
    "For color values, it is highly recommended to use the" + 
    " *3. Config Colors* (or *Re-config* if it already has been ran before) guided color wizard. The color previews " +
    "will look very different from the actual in-game colors, this " +
    "is because the colors are samples from a collection of pixels " +
    "from the piece rings and takes an average. They will likely " +
    "have a much more *grey* appearance as the piece rings have " +
    "many dark pixels. The automation relies on a specific " +
    "shape of the piece rings to gather the pixels to use for " +
    "the averages, it is not recommended to alter what the color " +
    "wizard sets."
    ),
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    wraplength =max (160 ,inner_w -24 ),
    justify =tk .LEFT ,
    ).pack (anchor =tk .W ,padx =8 ,pady =(0 ,8 ))

    tk .Label (
    inner ,
    text ="Extra delay at the end automation loop (seconds):",
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    ).pack (anchor =tk .W ,padx =8 ,pady =0 )
    tk .Entry (
    inner ,
    textvariable =self ._game_config_delay_var ,
    width =10 ,
    font =cfg_meta ,
    bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
    fg =gv.GAME_LOG_TEXT ,
    insertbackground =gv.GAME_LOG_TEXT ,
    highlightthickness =1 ,
    highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
    highlightcolor =gv.GAME_LOG_PANEL_OUTLINE ,
    ).pack (anchor =tk .W ,padx =8 ,pady =4 )
    tk .Label (
    inner ,
    text ="Global automation timing (the default values are the " +
    "recommended minimum values, any lower and it is very likely " +
    "to cause issues with the automation. These are also likely " +
    "dependent on your system, what I found to be the minimum " +
    "values to work on my system may not work on yours, if any " +
    "of the following are occuring I recommend increasing these values:" +
    "\n - Pieces are not dropping in the correct locations" +
    "\n - The visual board does not match the actual games board" +
    "\n - It takes multiple attempts to click the *Brew Again* button):",
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    wraplength =max (160 ,inner_w -24 ),
    justify =tk .LEFT ,
    ).pack (anchor =tk .W ,padx =8 ,pady =(8 ,2 ))
    timing_grid =tk .Frame (inner ,bg =gv.GAME_LOG_PANEL_FILL )
    timing_grid .pack (anchor =tk .W ,padx =8 ,pady =(0 ,6 ))

    lbl_w =26 

    def _timing_row (r :int ,label :str ,var :tk .StringVar )->None :
        tk .Label (
        timing_grid ,
        text =label ,
        font =cfg_meta ,
        fg =gv.GAME_LOG_TEXT ,
        bg =gv.GAME_LOG_PANEL_FILL ,
        anchor =tk .W ,
        width =lbl_w ,
        ).grid (row =r ,column =0 ,sticky ="w",padx =(0 ,6 ),pady =1 )
        tk .Entry (
        timing_grid ,
        textvariable =var ,
        width =8 ,
        font =cfg_meta ,
        bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
        fg =gv.GAME_LOG_TEXT ,
        insertbackground =gv.GAME_LOG_TEXT ,
        highlightthickness =1 ,
        highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
        highlightcolor =gv.GAME_LOG_PANEL_OUTLINE ,
        ).grid (row =r ,column =1 ,sticky ="w",pady =1 )

    _timing_row (0 ,"Foreground settle (s)",self ._game_config_foreground_settle_var )
    _timing_row (1 ,"Action delay (s)",self ._game_config_action_delay_var )
    _timing_row (2 ,"Pre-click settle (s)",self ._game_config_pre_click_settle_var )
    _timing_row (3 ,"Post-click settle (s)",self ._game_config_post_click_settle_var )
    _timing_row (4 ,"Post-drop sleep (s)",self ._game_config_post_drop_sleep_var )
    _timing_row (5 ,"Hand poll interval (ms)",self ._game_config_hand_poll_interval_ms_var )
    _timing_row (6 ,"Board wait poll (ms)",self ._game_config_board_wait_poll_interval_ms_var )
    tk .Label (
    inner ,
    text ="Live Game Visual:",
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    ).pack (anchor =tk .W ,padx =8 ,pady =(4 ,0 ))
    live_opt =tk .OptionMenu (
    inner ,
    self ._game_config_live_visual_var ,
    *gv.BREW_LIVE_GAME_VISUAL_CHOICES ,
    )
    live_opt .configure (
    font =cfg_meta ,
    bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
    fg =gv.GAME_LOG_TEXT ,
    activebackground =gv.GAME_LOG_PANEL_OUTLINE ,
    activeforeground =gv.GAME_LOG_TEXT ,
    highlightthickness =1 ,
    highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
    highlightcolor =gv.GAME_LOG_PANEL_OUTLINE ,
    )
    live_opt ["menu"].configure (
    bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
    fg =gv.GAME_LOG_TEXT ,
    activebackground =gv.GAME_LOG_PANEL_OUTLINE ,
    activeforeground =gv.GAME_LOG_TEXT ,
    font =cfg_meta ,
    )
    live_opt .pack (anchor =tk .W ,padx =8 ,pady =4 )

    tk .Checkbutton (
    inner ,
    text ="Simple UI (no themed background, no recipe/board art)",
    variable =self ._game_config_simple_ui_var ,
    font =cfg_meta ,
    fg =gv .GAME_LOG_TEXT ,
    bg =gv .GAME_LOG_PANEL_FILL ,
    activebackground =gv .GAME_LOG_PANEL_FILL ,
    activeforeground =gv .GAME_LOG_TEXT ,
    selectcolor =gv .GAME_LOG_TEXT_WIDGET_BG ,
    highlightthickness =0 ,
    anchor =tk .W ,
    ).pack (anchor =tk .W ,padx =8 ,pady =(2 ,4 ))

    tk .Label (
    inner ,
    text ="Empty board — median RGB for background board:",
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    ).pack (anchor =tk .W ,padx =8 ,pady =(10 ,0 ))
    brow =tk .Frame (inner ,bg =gv.GAME_LOG_PANEL_FILL )
    brow .pack (anchor =tk .W ,padx =8 ,pady =4 )
    br =int (self ._brew_board_await_r )
    bg_ =int (self ._brew_board_await_g )
    bb =int (self ._brew_board_await_b )
    bhx =_rgb888_to_hex (br ,bg_ ,bb )if (br or bg_ or bb )else "#2a2a2e"
    bcv =tk .Canvas (
    brow ,
    width =28 ,
    height =28 ,
    highlightthickness =1 ,
    highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    )
    bcv .pack (side =tk .LEFT ,padx =(0 ,8 ))
    bcv .create_rectangle (1 ,1 ,27 ,27 ,fill =bhx ,outline =gv.GAME_LOG_PANEL_OUTLINE )
    for lab ,var in (
    ("R",self ._game_config_board_r_var ),
    ("G",self ._game_config_board_g_var ),
    ("B",self ._game_config_board_b_var ),
    ):
        tk .Label (
        brow ,text =lab ,font =cfg_meta ,fg =gv.GAME_LOG_TEXT ,bg =gv.GAME_LOG_PANEL_FILL 
        ).pack (side =tk .LEFT )
        tk .Entry (
        brow ,
        textvariable =var ,
        width =5 ,
        font =cfg_meta ,
        bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
        fg =gv.GAME_LOG_TEXT ,
        insertbackground =gv.GAME_LOG_TEXT ,
        highlightthickness =1 ,
        highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
        highlightcolor =gv.GAME_LOG_PANEL_OUTLINE ,
        ).pack (side =tk .LEFT ,padx =(4 ,10 ))

    tk .Label (
    inner ,
    text ="Brew Again button — median RGB for auto re-brew detection:",
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    ).pack (anchor =tk .W ,padx =8 ,pady =(6 ,0 ))
    arow =tk .Frame (inner ,bg =gv.GAME_LOG_PANEL_FILL )
    arow .pack (anchor =tk .W ,padx =8 ,pady =4 )
    ar =int (self ._brew_again_r )
    ag =int (self ._brew_again_g )
    ab =int (self ._brew_again_b )
    ahx =_rgb888_to_hex (ar ,ag ,ab )if (ar or ag or ab )else "#2a2a2e"
    acv =tk .Canvas (
    arow ,
    width =28 ,
    height =28 ,
    highlightthickness =1 ,
    highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    )
    acv .pack (side =tk .LEFT ,padx =(0 ,8 ))
    acv .create_rectangle (1 ,1 ,27 ,27 ,fill =ahx ,outline =gv.GAME_LOG_PANEL_OUTLINE )
    for lab ,var in (
    ("R",self ._game_config_brew_again_r_var ),
    ("G",self ._game_config_brew_again_g_var ),
    ("B",self ._game_config_brew_again_b_var ),
    ):
        tk .Label (
        arow ,text =lab ,font =cfg_meta ,fg =gv.GAME_LOG_TEXT ,bg =gv.GAME_LOG_PANEL_FILL 
        ).pack (side =tk .LEFT )
        tk .Entry (
        arow ,
        textvariable =var ,
        width =5 ,
        font =cfg_meta ,
        bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
        fg =gv.GAME_LOG_TEXT ,
        insertbackground =gv.GAME_LOG_TEXT ,
        highlightthickness =1 ,
        highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
        highlightcolor =gv.GAME_LOG_PANEL_OUTLINE ,
        ).pack (side =tk .LEFT ,padx =(4 ,10 ))

    tk .Label (
    inner ,
    text ="Brew Again OK button — median RGB for confirmation click detection:",
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    ).pack (anchor =tk .W ,padx =8 ,pady =(6 ,0 ))
    aok_row =tk .Frame (inner ,bg =gv.GAME_LOG_PANEL_FILL )
    aok_row .pack (anchor =tk .W ,padx =8 ,pady =4 )
    aor =int (self ._brew_again_ok_r )
    aog =int (self ._brew_again_ok_g )
    aob =int (self ._brew_again_ok_b )
    aohx =_rgb888_to_hex (aor ,aog ,aob )if (aor or aog or aob )else "#2a2a2e"
    aocv =tk .Canvas (
    aok_row ,
    width =28 ,
    height =28 ,
    highlightthickness =1 ,
    highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    )
    aocv .pack (side =tk .LEFT ,padx =(0 ,8 ))
    aocv .create_rectangle (1 ,1 ,27 ,27 ,fill =aohx ,outline =gv.GAME_LOG_PANEL_OUTLINE )
    for lab ,var in (
    ("R",self ._game_config_brew_again_ok_r_var ),
    ("G",self ._game_config_brew_again_ok_g_var ),
    ("B",self ._game_config_brew_again_ok_b_var ),
    ):
        tk .Label (
        aok_row ,text =lab ,font =cfg_meta ,fg =gv.GAME_LOG_TEXT ,bg =gv.GAME_LOG_PANEL_FILL 
        ).pack (side =tk .LEFT )
        tk .Entry (
        aok_row ,
        textvariable =var ,
        width =5 ,
        font =cfg_meta ,
        bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
        fg =gv.GAME_LOG_TEXT ,
        insertbackground =gv.GAME_LOG_TEXT ,
        highlightthickness =1 ,
        highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
        highlightcolor =gv.GAME_LOG_PANEL_OUTLINE ,
        ).pack (side =tk .LEFT ,padx =(4 ,10 ))

    tk .Label (
    inner ,
    text ="Potion Failed Continue button — median RGB for fail popup continue:",
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    ).pack (anchor =tk .W ,padx =8 ,pady =(6 ,0 ))
    pfc_row =tk .Frame (inner ,bg =gv.GAME_LOG_PANEL_FILL )
    pfc_row .pack (anchor =tk .W ,padx =8 ,pady =4 )
    pfcr =int (self ._potion_failed_continue_r )
    pfcg =int (self ._potion_failed_continue_g )
    pfcb =int (self ._potion_failed_continue_b )
    pfchx =_rgb888_to_hex (pfcr ,pfcg ,pfcb )if (pfcr or pfcg or pfcb )else "#2a2a2e"
    pfccv =tk .Canvas (
    pfc_row ,
    width =28 ,
    height =28 ,
    highlightthickness =1 ,
    highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    )
    pfccv .pack (side =tk .LEFT ,padx =(0 ,8 ))
    pfccv .create_rectangle (1 ,1 ,27 ,27 ,fill =pfchx ,outline =gv.GAME_LOG_PANEL_OUTLINE )
    for lab ,var in (
    ("R",self ._game_config_potion_failed_continue_r_var ),
    ("G",self ._game_config_potion_failed_continue_g_var ),
    ("B",self ._game_config_potion_failed_continue_b_var ),
    ):
        tk .Label (
        pfc_row ,text =lab ,font =cfg_meta ,fg =gv.GAME_LOG_TEXT ,bg =gv.GAME_LOG_PANEL_FILL 
        ).pack (side =tk .LEFT )
        tk .Entry (
        pfc_row ,
        textvariable =var ,
        width =5 ,
        font =cfg_meta ,
        bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
        fg =gv.GAME_LOG_TEXT ,
        insertbackground =gv.GAME_LOG_TEXT ,
        highlightthickness =1 ,
        highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
        highlightcolor =gv.GAME_LOG_PANEL_OUTLINE ,
        ).pack (side =tk .LEFT ,padx =(4 ,10 ))

    ring_macro =tk .Frame (inner ,bg =gv.GAME_LOG_PANEL_FILL )
    ring_macro .pack (fill =tk .BOTH ,expand =True ,padx =8 ,pady =(10 ,4 ))

    lf_next =tk .LabelFrame (
    ring_macro ,
    text ="Next (queue)",
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    padx =6 ,
    pady =6 ,
    )
    lf_next .pack (side =tk .LEFT ,fill =tk .BOTH ,expand =True ,padx =(0 ,5 ))
    self ._pack_game_config_ring_slot_block (
    lf_next ,"next_piece_left",panel_font =cfg_meta 
    )
    self ._pack_game_config_ring_slot_block (
    lf_next ,"next_piece_right",panel_font =cfg_meta 
    )

    lf_cur =tk .LabelFrame (
    ring_macro ,
    text ="Current (in play)",
    font =cfg_meta ,
    fg =gv.GAME_LOG_TEXT ,
    bg =gv.GAME_LOG_PANEL_FILL ,
    padx =6 ,
    pady =6 ,
    )
    lf_cur .pack (side =tk .LEFT ,fill =tk .BOTH ,expand =True ,padx =(5 ,0 ))
    self ._pack_game_config_ring_slot_block (
    lf_cur ,"current_piece_left",panel_font =cfg_meta 
    )
    self ._pack_game_config_ring_slot_block (
    lf_cur ,"current_piece_right",panel_font =cfg_meta 
    )

    btn_row =tk .Frame (inner ,bg =gv.GAME_LOG_PANEL_FILL )
    btn_row .pack (anchor =tk .W ,padx =8 ,pady =(12 ,12 ))
    tk .Button (
    btn_row ,
    text ="Apply",
    font =cfg_meta ,
    command =self ._apply_config_delay_from_ui ,
    ).pack (side =tk .LEFT ,padx =(0 ,8 ))
    tk .Button (
    btn_row ,
    text ="Restore defaults",
    font =cfg_meta ,
    command =self ._restore_game_config_defaults ,
    ).pack (side =tk .LEFT )

    _bind_mousewheel_recursive (shell ,_mw )

    self ._game_config_shell =shell 
    self .root .after_idle (_inner_cfg )


def _restore_game_config_defaults (self )->None :
    if not messagebox .askokcancel (
    "Restore defaults",
    "Reset extra delay to "
    f"{gv.BREW_AUTOMATION_DELAY_DEFAULT_S}s and set all board, piece display, and ring RGB values to 0? "
    "This saves to brew_gui_settings.json immediately.",
    parent =self .root ,
    ):
        return 
    self ._brew_automation_delay_s =float (gv.BREW_AUTOMATION_DELAY_DEFAULT_S )
    self ._game_config_delay_var .set (str (gv.BREW_AUTOMATION_DELAY_DEFAULT_S ))
    self ._brew_automation_foreground_settle_s =float (gv.BREW_AUTOMATION_FOREGROUND_SETTLE_DEFAULT_S )
    self ._brew_automation_action_delay_s =float (gv.BREW_AUTOMATION_ACTION_DELAY_DEFAULT_S )
    self ._brew_automation_pre_click_settle_s =float (gv.BREW_AUTOMATION_PRE_CLICK_SETTLE_DEFAULT_S )
    self ._brew_automation_post_click_settle_s =float (gv.BREW_AUTOMATION_POST_CLICK_SETTLE_DEFAULT_S )
    self ._brew_automation_post_drop_sleep_s =float (gv.BREW_AUTOMATION_POST_DROP_SLEEP_DEFAULT_S )
    self ._brew_automation_hand_poll_interval_ms =int (gv.BREW_AUTOMATION_HAND_POLL_INTERVAL_DEFAULT_MS )
    self ._brew_automation_board_wait_poll_interval_ms =int (gv.BREW_AUTOMATION_BOARD_WAIT_POLL_INTERVAL_DEFAULT_MS )
    self ._sync_automation_timing_vars_from_state ()
    self ._brew_live_game_visual =gv.BREW_LIVE_GAME_VISUAL_DEFAULT 
    self ._game_config_live_visual_var .set (gv.BREW_LIVE_GAME_VISUAL_DEFAULT )
    self ._brew_simple_ui =False 
    self ._game_config_simple_ui_var .set (False )
    self ._brew_board_await_r =0 
    self ._brew_board_await_g =0 
    self ._brew_board_await_b =0 
    self ._brew_again_r =0 
    self ._brew_again_g =0 
    self ._brew_again_b =0 
    self ._brew_again_ok_r =0 
    self ._brew_again_ok_g =0 
    self ._brew_again_ok_b =0 
    self ._potion_failed_continue_r =0 
    self ._potion_failed_continue_g =0 
    self ._potion_failed_continue_b =0 
    self ._brew_piece_display_rgb .clear ()
    self ._brew_ring_median_grid =_empty_brew_ring_median_grid ()
    self ._sync_board_bgr_vars_from_state ()
    self ._sync_piece_cfg_rgb_vars_from_state ()
    self ._sync_ring_median_grid_vars_from_state ()
    self ._save_brew_gui_settings ()
    self ._refresh_game_action_button_labels ()
    self ._brew_automation_hotkey_sync ()
    self ._redraw_background ()
    self ._layout_overlays ()
    self ._raise_overlay_tags ()
    self ._append_game_log (
    f"[Config] Restored defaults: delay {gv.BREW_AUTOMATION_DELAY_DEFAULT_S}s, live visual "
    f"{gv.BREW_LIVE_GAME_VISUAL_DEFAULT}, timings reset, all RGB cleared, simple UI off."
    )
    if self ._game_config_visible :
        self ._draw_game_config_layer ()


def _apply_config_delay_from_ui (self )->None :
    raw =(self ._game_config_delay_var .get ()or "").strip ().replace (",",".")
    try :
        v =float (raw )
    except ValueError :
        self ._append_game_log ("[Config] Invalid delay; restored last value.")
        self ._game_config_delay_var .set (str (self ._brew_automation_delay_s ))
        return 
    v =max (0.0 ,min (5.0 ,v ))
    live_mode =_normalize_live_game_visual_mode (self ._game_config_live_visual_var .get ())

    def _parse_float (var :tk .StringVar ,name :str ,lo :float ,hi :float )->float |None :
        s =(var .get ()or "").strip ().replace (",",".")
        try :
            x =float (s )
        except ValueError :
            self ._append_game_log (f"[Config] Invalid {name}; use {lo:g}–{hi:g}.")
            return None 
        return max (lo ,min (hi ,x ))

    def _parse_int (var :tk .StringVar ,name :str ,lo :int ,hi :int )->int |None :
        s =(var .get ()or "").strip ()
        try :
            x =int (s )
        except ValueError :
            self ._append_game_log (f"[Config] Invalid {name}; use {lo}–{hi}.")
            return None 
        return max (lo ,min (hi ,x ))

    fg_settle =_parse_float (
    self ._game_config_foreground_settle_var ,
    "foreground settle",
    0.0 ,
    2.0 ,
    )
    action_delay =_parse_float (
    self ._game_config_action_delay_var ,
    "action delay",
    0.0 ,
    2.0 ,
    )
    pre_click =_parse_float (
    self ._game_config_pre_click_settle_var ,
    "pre-click settle",
    0.0 ,
    1.0 ,
    )
    post_click =_parse_float (
    self ._game_config_post_click_settle_var ,
    "post-click settle",
    0.0 ,
    1.0 ,
    )
    post_drop =_parse_float (
    self ._game_config_post_drop_sleep_var ,
    "post-drop sleep",
    0.0 ,
    2.0 ,
    )
    hand_poll_ms =_parse_int (
    self ._game_config_hand_poll_interval_ms_var ,
    "hand poll interval",
    30 ,
    1000 ,
    )
    board_wait_ms =_parse_int (
    self ._game_config_board_wait_poll_interval_ms_var ,
    "board wait poll interval",
    30 ,
    2000 ,
    )
    if (
    fg_settle is None 
    or action_delay is None 
    or pre_click is None 
    or post_click is None 
    or post_drop is None 
    or hand_poll_ms is None 
    or board_wait_ms is None 
    ):
        self ._sync_automation_timing_vars_from_state ()
        return 

    def _parse_byte (var :tk .StringVar ,name :str )->int |None :
        s =(var .get ()or "").strip ()
        try :
            x =int (s )
        except ValueError :
            self ._append_game_log (f"[Config] Invalid {name}; use 0–255.")
            return None 
        return max (0 ,min (255 ,x ))

    br =_parse_byte (self ._game_config_board_r_var ,"board R")
    bg_ =_parse_byte (self ._game_config_board_g_var ,"board G")
    bb =_parse_byte (self ._game_config_board_b_var ,"board B")
    ar =_parse_byte (self ._game_config_brew_again_r_var ,"brew_again R")
    ag =_parse_byte (self ._game_config_brew_again_g_var ,"brew_again G")
    ab =_parse_byte (self ._game_config_brew_again_b_var ,"brew_again B")
    aor =_parse_byte (self ._game_config_brew_again_ok_r_var ,"brew_again_ok R")
    aog =_parse_byte (self ._game_config_brew_again_ok_g_var ,"brew_again_ok G")
    aob =_parse_byte (self ._game_config_brew_again_ok_b_var ,"brew_again_ok B")
    pfcr =_parse_byte (self ._game_config_potion_failed_continue_r_var ,"potion_failed_continue R")
    pfcg =_parse_byte (self ._game_config_potion_failed_continue_g_var ,"potion_failed_continue G")
    pfcb =_parse_byte (self ._game_config_potion_failed_continue_b_var ,"potion_failed_continue B")
    if br is None or bg_ is None or bb is None or ar is None or ag is None or ab is None or aor is None or aog is None or aob is None or pfcr is None or pfcg is None or pfcb is None :
        self ._game_config_delay_var .set (str (self ._brew_automation_delay_s ))
        self ._sync_automation_timing_vars_from_state ()
        self ._sync_board_bgr_vars_from_state ()
        self ._sync_piece_cfg_rgb_vars_from_state ()
        self ._sync_ring_median_grid_vars_from_state ()
        return 

    def _ring_slot_caption (sk :str )->str :
        return (
        gv._TLOPO_NEXT_PIECE_TITLES .get (sk )
        or gv._TLOPO_CURRENT_PIECE_TITLES .get (sk )
        or sk 
        )

    parsed_ring :dict [str ,dict [str ,tuple [int ,int ,int ]]]={
    sk :{}for sk in gv._GAME_CONFIG_RING_GRID_SLOTS 
    }
    for sk in gv._GAME_CONFIG_RING_GRID_SLOTS :
        cap =_ring_slot_caption (sk )
        for t in gv._CONFIG_PIECE_DISPLAY_ORDER :
            pr =_parse_byte (self ._game_config_ring_r_vars [sk ][t ],f"{cap} {t} R")
            pg =_parse_byte (self ._game_config_ring_g_vars [sk ][t ],f"{cap} {t} G")
            pb =_parse_byte (self ._game_config_ring_b_vars [sk ][t ],f"{cap} {t} B")
            if pr is None or pg is None or pb is None :
                self ._game_config_delay_var .set (str (self ._brew_automation_delay_s ))
                self ._sync_automation_timing_vars_from_state ()
                self ._sync_board_bgr_vars_from_state ()
                self ._sync_piece_cfg_rgb_vars_from_state ()
                self ._sync_ring_median_grid_vars_from_state ()
                return 
            if pr ==0 and pg ==0 and pb ==0 :
                continue 
            parsed_ring [sk ][t ]=(pr ,pg ,pb )

    new_piece :dict [str ,tuple [int ,int ,int ]]={}
    for t in gv._CONFIG_PIECE_DISPLAY_ORDER :
        lr =_parse_byte (
        self ._game_config_ring_r_vars ["current_piece_left"][t ],
        f"Current (left) {t} R",
        )
        lg =_parse_byte (
        self ._game_config_ring_g_vars ["current_piece_left"][t ],
        f"Current (left) {t} G",
        )
        lb =_parse_byte (
        self ._game_config_ring_b_vars ["current_piece_left"][t ],
        f"Current (left) {t} B",
        )
        rr =_parse_byte (
        self ._game_config_ring_r_vars ["current_piece_right"][t ],
        f"Current (right) {t} R",
        )
        rg =_parse_byte (
        self ._game_config_ring_g_vars ["current_piece_right"][t ],
        f"Current (right) {t} G",
        )
        rb =_parse_byte (
        self ._game_config_ring_b_vars ["current_piece_right"][t ],
        f"Current (right) {t} B",
        )
        if lr is None or lg is None or lb is None or rr is None or rg is None or rb is None :
            self ._game_config_delay_var .set (str (self ._brew_automation_delay_s ))
            self ._sync_automation_timing_vars_from_state ()
            self ._sync_board_bgr_vars_from_state ()
            self ._sync_piece_cfg_rgb_vars_from_state ()
            self ._sync_ring_median_grid_vars_from_state ()
            return 
        if lr ==0 and lg ==0 and lb ==0 and rr ==0 and rg ==0 and rb ==0 :
            continue 
        if (lr |lg |lb )!=0 :
            new_piece [t ]=(lr ,lg ,lb )
        else :
            new_piece [t ]=(rr ,rg ,rb )

    self ._brew_automation_delay_s =v 
    self ._game_config_delay_var .set (str (v ))
    self ._brew_automation_foreground_settle_s =fg_settle 
    self ._brew_automation_action_delay_s =action_delay 
    self ._brew_automation_pre_click_settle_s =pre_click 
    self ._brew_automation_post_click_settle_s =post_click 
    self ._brew_automation_post_drop_sleep_s =post_drop 
    self ._brew_automation_hand_poll_interval_ms =hand_poll_ms 
    self ._brew_automation_board_wait_poll_interval_ms =board_wait_ms 
    self ._sync_automation_timing_vars_from_state ()
    self ._brew_live_game_visual =live_mode 
    self ._game_config_live_visual_var .set (live_mode )
    self ._append_game_log (f"[Config] Extra delay after each drop (oldBot --delay) = {v}s")
    self ._append_game_log (f"[Config] Live Game Visual = {live_mode}")
    self ._brew_board_await_r =br 
    self ._brew_board_await_g =bg_ 
    self ._brew_board_await_b =bb 
    self ._brew_again_r =ar 
    self ._brew_again_g =ag 
    self ._brew_again_b =ab 
    self ._brew_again_ok_r =aor 
    self ._brew_again_ok_g =aog 
    self ._brew_again_ok_b =aob 
    self ._potion_failed_continue_r =pfcr 
    self ._potion_failed_continue_g =pfcg 
    self ._potion_failed_continue_b =pfcb 
    self ._sync_board_bgr_vars_from_state ()
    self ._append_game_log (
    f"[Config] Board await RGB = ({self._brew_board_await_r}, "
    f"{self._brew_board_await_g}, {self._brew_board_await_b})"
    )
    self ._append_game_log (
    f"[Config] Brew Again RGB = ({self._brew_again_r}, {self._brew_again_g}, {self._brew_again_b})"
    )
    self ._append_game_log (
    f"[Config] Brew Again OK RGB = ({self._brew_again_ok_r}, {self._brew_again_ok_g}, {self._brew_again_ok_b})"
    )
    self ._append_game_log (
    f"[Config] Potion Failed Continue RGB = ({self._potion_failed_continue_r}, {self._potion_failed_continue_g}, {self._potion_failed_continue_b})"
    )
    for sk in gv._GAME_CONFIG_RING_GRID_SLOTS :
        self ._brew_ring_median_grid [sk ]=dict (parsed_ring [sk ])
    self ._brew_piece_display_rgb =new_piece 
    self ._sync_piece_cfg_rgb_vars_from_state ()
    self ._sync_ring_median_grid_vars_from_state ()
    self ._append_game_log (
    "[Config] Ring median grid, board await, and piece display RGB saved."
    )
    self ._brew_simple_ui =bool (self ._game_config_simple_ui_var .get ())
    self ._save_brew_gui_settings ()
    self ._refresh_game_action_button_labels ()
    self ._brew_automation_hotkey_sync ()
    self ._redraw_background ()
    self ._layout_overlays ()
    self ._raise_overlay_tags ()


def _brew_piece_color_config_ok (self )->bool :
    return _brew_rgb_config_minimum_ok (
    self ._brew_piece_display_rgb ,
    self ._brew_board_await_r ,
    self ._brew_board_await_g ,
    self ._brew_board_await_b ,
    )


def _guided_config_caption (self )->str :
    return (
    gv.GAME_CAPTION_GUIDED_OPTIONAL 
    if self ._brew_piece_color_config_ok ()
    else gv.GAME_CAPTION_GUIDED_IDLE 
    )


