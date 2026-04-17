from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

import brew_core.board_memory as brew_board_memory
import variables.brew_typography as brew_ty
import variables.global_variables as gv
from core_helpers import island_display_for_gui
from hexGrid.hex_grid import (
    BREW_BOARD_HEX_GRID,
    _hex_board_cell_centers_for_cfg,
    _hex_polygon_points,
    _hex_polygon_stretched_rotated,
    hex_memory_piece_fit_px ,
)
from layer_helpers.assets import _load_piece_thumbnail, _resolve_exact_piece_png_for_gem, resolve_piece_png
from layer_helpers.strategy_sync import _sync_board_strategy_hex_fills

def _normalize_live_game_visual_mode(v: str | None) -> str:
    s = str(v or "").strip().lower()
    if s == "none":
        return "None"
    if s == "exact":
        return "Exact"
    return "Simple"

def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.strip().lstrip("#")
    if len(h) != 6:
        return (220, 200, 180)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def _blend_hex_towards_white(h: str, t: float) -> str:
    r, g, b = _hex_to_rgb(h)
    t = max(0.0, min(1.0, t))
    r = int(r + (255 - r) * t)
    g = int(g + (255 - g) * t)
    b = int(b + (255 - b) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

def _shade_hex(h: str, factor: float) -> str:
    r, g, b = _hex_to_rgb(h)
    factor = max(0.35, min(1.65, factor))
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"

def _draw_board_memory_pieces_layer (
self ,
centers :list [tuple [float ,float ]],
circum_r :float ,
cell_indices :list [tuple [int ,int ]],
*,
column_mul :float =1.0 ,
row_mul :float =1.0 ,
phase_deg :float =30.0 ,
grid_rotation_deg :float =0.0 ,
outline_inset_px :float =0.0 ,
)->None :
    """Draw recipe piece PNGs on hex centers from the internal BoardSim (automation only updates)."""
    self .bg_canvas .delete ("board_memory_piece")
    self ._board_memory_photo_refs .clear ()
    mode =_normalize_live_game_visual_mode (self ._brew_live_game_visual )
    if mode =="None":
        return 
    if (
    self ._view !="game"
    or self ._brew_board_sim is None 
    or not brew_board_memory .board_memory_available ()
    ):
        return 
    if not centers or len (cell_indices )!=len (centers ):
        return 
    potion =(
    self .potions [max (0 ,min (self ._current_potion_index ,len (self .potions )-1 ))]
    if self .potions 
    else None 
    )
    idx_map :dict [tuple [int ,int ],tuple [float ,float ]]={
    idx :cen for cen ,idx in zip (centers ,cell_indices )
    }
    # Same geometry as ``_hex_polygon_stretched_rotated`` for the outline (``line_r`` + stretch + phase + rot).
    r_circ_f ,side_f =hex_memory_piece_fit_px (
    float (circum_r ),
    float (phase_deg ),
    float (column_mul ),
    float (row_mul ),
    float (grid_rotation_deg ),
    inset =0.995 ,
    outline_inset_px =float (outline_inset_px ),
    )
    px_target =max (14 ,int (round (side_f )))
    r_oval_base =max (6.0 ,r_circ_f )
    sim =self ._brew_board_sim 
    for br in range (brew_board_memory .ROWS ):
        for bc in range (brew_board_memory .COLS ):
            gem =sim .grid [br ][bc ]
            if gem is None :
                continue 
            hx =brew_board_memory .sim_rc_to_hex_cell (br ,bc )
            if hx is None :
                continue 
            cen =idx_map .get (hx )
            if cen is None :
                continue 
            cx ,cy =cen 
            photo :tk .PhotoImage |None =None 
            if mode =="Exact":
                png =_resolve_exact_piece_png_for_gem (self ,gem ,potion )
                if png is not None :
                    photo =_load_piece_thumbnail (self ,png ,size =px_target )
            if photo is not None :
                self ._board_memory_photo_refs .append (photo )
                self .bg_canvas .create_image (
                cx ,
                cy ,
                image =photo ,
                tags =("board_memory_piece",f"bm_piece_{br}_{bc}"),
                )
                continue 
            if mode =="Exact":
                # Exact mode never falls back to circles; only render real piece art.
                continue 
            fill_hex =gv.COLOR_OUTLINE .get (str (gem .color ),"#6a6a6a")
            if str (gem .color ).lower ()=="grey":
                fill_hex =gv.COLOR_OUTLINE .get ("black","#6a6a6a")
            r_oval =max (6 ,int (round (r_oval_base )))
            self .bg_canvas .create_oval (
            cx -r_oval ,
            cy -r_oval ,
            cx +r_oval ,
            cy +r_oval ,
            fill =fill_hex ,
            outline =gv.GAME_CHROME_WHITE ,
            width =1 ,
            tags =("board_memory_piece",f"bm_piece_{br}_{bc}"),
            )
            self .bg_canvas .create_text (
            cx ,
            cy ,
            text =str (int (getattr (gem ,"level",1 )or 1 )),
            font =(
            self ._font_ui_family ,
            max (8 ,min (44 ,int (round (r_circ_f *0.65 )))),
            tkfont .BOLD ,
            ),
            fill =gv.GAME_CHROME_WHITE ,
            tags =("board_memory_piece",f"bm_piece_{br}_{bc}"),
            )


def _draw_game_log_layer (self )->None :
    if not self ._game_log_visible :
        self ._destroy_game_log_embed ()
        try :
            self .bg_canvas .delete ("game_log_layer")
        except tk .TclError :
            pass 
        self ._log_clear_rect =(0 ,0 ,0 ,0 )
        return 
    prev =getattr (self ,"_game_log_top",None )
    if prev is not None :
        try :
            if prev .winfo_exists ():
                prev .lift ()
                return 
        except tk .TclError :
            pass 
    self ._destroy_game_log_embed ()
    try :
        self .bg_canvas .delete ("game_log_layer")
    except tk .TclError :
        pass 
    self ._log_clear_rect =(0 ,0 ,0 ,0 )

    win =tk .Toplevel (self .root )
    self ._game_log_top =win 
    win .title ("Game log")
    win .transient (self .root )
    try :
        win .geometry (gv .GAME_LOG_POPUP_GEOMETRY )
    except tk .TclError :
        pass 

    def _on_log_popup_delete ()->None :
        self ._game_log_visible =False 
        self ._refresh_logs_toggle_label ()
        self ._destroy_game_log_embed ()

    win .protocol ("WM_DELETE_WINDOW",_on_log_popup_delete )

    shell =tk .Frame (win ,bg =gv.GAME_LOG_PANEL_FILL ,highlightthickness =0 )
    shell .pack (fill =tk .BOTH ,expand =True )

    body_row =tk .Frame (shell ,bg =gv.GAME_LOG_PANEL_FILL )
    body_row .pack (fill =tk .BOTH ,expand =True ,padx =6 ,pady =(6 ,4 ))
    txt =tk .Text (
    body_row ,
    wrap =tk .WORD ,
    font =(self ._font_ui_family ,9 ),
    bg =gv.GAME_LOG_TEXT_WIDGET_BG ,
    fg =gv.GAME_LOG_TEXT ,
    insertbackground =gv.GAME_LOG_TEXT ,
    relief =tk .FLAT ,
    bd =0 ,
    padx =6 ,
    pady =6 ,
    highlightthickness =0 ,
    selectbackground ="#4a6a9a",
    selectforeground =gv.GAME_LOG_TEXT ,
    exportselection =True ,
    undo =False ,
    )
    txt .bind ("<Key>",self ._game_log_text_key_guard )
    sb =tk .Scrollbar (
    body_row ,
    orient =tk .VERTICAL ,
    command =txt .yview ,
    bg =gv.GAME_LOG_SCROLLBAR_BG ,
    troughcolor =gv.GAME_LOG_SCROLLBAR_TROUGH ,
    activebackground =gv.GAME_LOG_SCROLLBAR_BG ,
    highlightthickness =0 ,
    bd =0 ,
    width =12 ,
    )
    txt .configure (yscrollcommand =sb .set )
    txt .pack (side =tk .LEFT ,fill =tk .BOTH ,expand =True )
    sb .pack (side =tk .RIGHT ,fill =tk .Y )

    btn_row =tk .Frame (shell ,bg =gv.GAME_LOG_PANEL_FILL )
    btn_row .pack (fill =tk .X ,padx =6 ,pady =(0 ,6 ))
    tk .Button (
    btn_row ,
    text ="Clear log",
    font =(self ._font_ui_family ,11 ),
    fg =gv.GAME_LOG_TEXT ,
    bg ="#45454a",
    activeforeground =gv.GAME_LOG_TEXT ,
    activebackground ="#5a5a60",
    highlightthickness =1 ,
    highlightbackground =gv.GAME_LOG_PANEL_OUTLINE ,
    command =self ._clear_game_log ,
    ).pack (side =tk .RIGHT )

    self ._game_log_shell =shell 
    self ._game_log_txt =txt 

    body ="\n".join (self ._game_log_lines )
    txt .insert (tk .END ,body if body else "(no messages yet)")
    txt .see (tk .END )


def _draw_hex_grid_layer (self )->None :
    self .bg_canvas .delete ("hex_grid")
    if getattr (self ,"_brew_simple_ui",False ):
        return 
    if self ._view !="game":
        return 
    _sync_board_strategy_hex_fills (self )
    gx ,gy ,gw ,gh =self ._game_board_rect 
    if gw <32 or gh <32 :
        return 
    cfg =BREW_BOARD_HEX_GRID 
    centers ,r ,cell_indices =_hex_board_cell_centers_for_cfg (
    float (gx ),float (gy ),float (gw ),float (gh ),cfg 
    )
    if not centers or len (cell_indices )!=len (centers ):
        return 
    line_r =max (1.5 ,r -max (0.0 ,cfg .outline_radius_inset ))
    ow =max (1 ,int (cfg .outline_width ))
    tess =(cfg .tessellation or "flat_top").lower ()
    if tess not in ("flat_top","pointy_top"):
        tess ="flat_top"
    if cfg .cell_polygon_phase_degrees is not None :
        phase =float (cfg .cell_polygon_phase_degrees )
    else :
        phase =30.0 if tess =="flat_top"else 0.0 
    cm =max (0.05 ,min (2.0 ,cfg .column_spacing_mul ))
    rm =max (0.05 ,min (2.0 ,cfg .row_spacing_mul ))
    rot_g =max (-360.0 ,min (360.0 ,cfg .rotation_degrees ))
    fills =self ._hex_cell_fill_colors 
    outlines =self ._hex_cell_outline_colors 
    ow_pr =min (6 ,ow +gv.PORT_ROYAL_OUTLINE_WIDTH_EXTRA )
    # Tk draws stroke centered on the hex path; use base ``ow`` only so Port Royal ``ow_pr`` does
    # not shrink memory pieces on every cell. Slightly <0.5*ow avoids over-shrinking vs fill.
    outline_half =0.38 *float (ow )
    for (cx ,cy ),(cc ,rr )in zip (centers ,cell_indices ):
        pts =_hex_polygon_stretched_rotated (cx ,cy ,line_r ,phase ,cm ,rm ,rot_g )
        fill =fills .get ((cc ,rr ),"")
        key =(cc ,rr )
        outline =outlines .get (key ,gv.HEX_GRID_OUTLINE )
        line_w =ow_pr if key in outlines else ow 
        self .bg_canvas .create_polygon (
        pts ,
        outline =outline ,
        width =line_w ,
        fill =fill ,
        tags =("hex_grid",f"hex_cell_{cc}_{rr}"),
        )
    self ._draw_board_memory_pieces_layer (
    centers ,
    line_r ,
    cell_indices ,
    column_mul =cm ,
    row_mul =rm ,
    phase_deg =phase ,
    grid_rotation_deg =rot_g ,
    outline_inset_px =outline_half ,
    )


def _draw_recipe_canvas_layer (self )->None :
    self .bg_canvas .delete ("recipe_ui")
    self ._recipe_photo_refs .clear ()
    if getattr (self ,"_brew_simple_ui",False ):
        return 

    rx ,ry ,rw ,rh =self ._recipe_rect 
    if rw <24 or rh <40 :
        return 
    if not self .potions :
        return 

    idx =max (0 ,min (self ._current_potion_index ,len (self .potions )-1 ))
    self ._current_potion_index =idx 
    p =self .potions [idx ]
    name =p .get ("display_name","?")
    level =p .get ("recipe_level","?")
    island =p .get ("island","")
    island_disp =island_display_for_gui (str (island )if island else None )
    meta_text =f"Requires Potions Level: {level}  ·  {island_disp}"

    sc =float (getattr (self ,"_layout_font_scale",1.0 )or 1.0 )
    title_meta_gap =max (2 ,int (round (brew_ty .RECIPE_TITLE_META_GAP_PX *sc )))
    meta_to_ingredients_gap =max (
    title_meta_gap +1 ,
    int (round (brew_ty .RECIPE_META_TO_INGREDIENTS_GAP_PX *sc )),
    )

    cx =rx +rw //2 
    y0 =ry +max (2 ,int (round (4 *sc )))
    title_id =self .bg_canvas .create_text (
    cx ,
    y0 ,
    text =name ,
    font =self ._font_title ,
    fill =gv.INK ,
    anchor ="n",
    tags ="recipe_ui",
    width =max (40 ,rw -20 ),
    justify ="center",
    )
    bb =self .bg_canvas .bbox (title_id )
    y_meta =(bb [3 ]+title_meta_gap )if bb else y0 +max (16 ,int (round (24 *sc )))
    meta_id =self .bg_canvas .create_text (
    cx ,
    y_meta ,
    text =meta_text ,
    font =self ._font_recipe_meta ,
    fill =gv.MUTED ,
    anchor ="n",
    tags ="recipe_ui",
    )
    bb_m =self .bg_canvas .bbox (meta_id )
    content_top =(bb_m [3 ]+meta_to_ingredients_gap )if bb_m else y_meta +max (16 ,int (round (28 *sc )))
    content_bottom =ry +rh -max (6 ,int (round (12 *sc )))
    ps =max (20 ,int (round (gv .PIECE_SIZE *sc )))
    if content_bottom <=content_top +ps :
        return 

    ings =p .get ("ingredients")or []
    row_h =ps +max (2 ,int (round (brew_ty .RECIPE_INGREDIENT_ROW_BELOW_PIECE *sc )))
    if not isinstance (ings ,list ):
        self .bg_canvas .create_text (
        rx +16 ,
        content_top ,
        text ="(invalid ingredients in catalog)",
        font =self ._font_recipe_meta ,
        fill =gv.MUTED ,
        anchor ="nw",
        tags ="recipe_ui",
        )
        self ._recipe_max_scroll =0 
        return 

    n =sum (1 for x in ings if isinstance (x ,dict ))
    total_h =n *row_h 
    viewport =content_bottom -content_top 
    self ._recipe_max_scroll =max (0 ,int (total_h -viewport ))
    self ._recipe_scroll_px =max (0 ,min (self ._recipe_scroll_px ,self ._recipe_max_scroll ))

    iy =0.2
    for ing in ings :
        if not isinstance (ing ,dict ):
            continue 
        row_y =content_top +iy *row_h -self ._recipe_scroll_px 
        iy +=brew_ty .RECIPE_INGREDIENT_ROW_STEP 
        if row_y +row_h <content_top or row_y >content_bottom :
            continue 

        color_key =(ing .get ("color")or "").lower ()
        outline =gv.COLOR_OUTLINE .get (color_key ,"#444444")
        nm =ing .get ("display_name","?")
        png =resolve_piece_png (ing ,self .pieces_dir )
        photo =_load_piece_thumbnail (self ,png ,size =ps )if png else None

        lm =max (8 ,int (round (20 *sc )))
        icx =rx +lm +ps //2 
        icy =row_y +row_h //2 -2 

        if photo :
            self ._recipe_photo_refs .append (photo )
            self .bg_canvas .create_image (icx ,icy ,image =photo ,anchor ="center",tags ="recipe_ui")
        else :
            pts =_hex_polygon_points (float (icx ),float (icy ),float (max (4 ,ps //2 -max (1 ,int (sc )))))
            self .bg_canvas .create_polygon (pts ,fill =gv.HEX_FILL ,outline =outline ,width =2 ,tags ="recipe_ui")

        self .bg_canvas .create_text (
        rx +max (24 ,int (round (80 *sc )))+ps ,
        icy ,
        text =nm ,
        font =self ._font_recipe_ingredient ,
        fill =gv.INK ,
        anchor ="w",
        tags ="recipe_ui",
        )


def _draw_list_canvas_layer (self )->None :
    self .bg_canvas .delete ("list_ui")
    if self ._view !="catalog"and not getattr (self ,"_brew_simple_ui",False ):
        return 
    if not self .potions :
        return 
    lx ,ly ,lw ,lh =self ._list_rect 
    if lw <40 or lh <40 :
        return 

    sc =float (getattr (self ,"_layout_font_scale",1.0 )or 1.0 )
    pad_x =max (8 ,int (round (gv .LIST_INSET_X *sc )))
    row_h =self ._list_row_h 
    sb_w =max (8 ,int (round (gv .LIST_SCROLLBAR_W *sc )))
    self ._list_sb_draw_w =sb_w 
    text_right =lx +lw -sb_w 
    simple_ui =getattr (self ,"_brew_simple_ui",False )
    list_ink =gv .BREW_SIMPLE_UI_TEXT if simple_ui else gv .INK 

    body_top =ly +self ._list_title_block_h -6
    body_bottom =ly +lh -gv.LIST_BODY_BOTTOM_PAD 
    self ._list_body_top =body_top 
    self ._list_body_bottom =body_bottom 

    cx =lx +lw //2 
    self .bg_canvas .create_text (
    cx ,
    ly +gv.LIST_TITLE_TOP_PAD ,
    text =gv.LIST_TITLE_TEXT ,
    font =self ._list_heading_font ,
    fill =list_ink ,
    anchor ="n",
    tags ="list_ui",
    width =max (48 ,lw -24 ),
    justify ="center",
    )

    names =[p .get ("display_name","?")for p in self .potions ]
    n =len (names )
    total_h =n *row_h 
    viewport_h =max (0 ,body_bottom -body_top )
    self ._list_viewport_inner =max (1 ,viewport_h )
    self ._list_max_scroll =max (0 ,int (total_h -viewport_h ))
    self ._list_scroll_px =max (0 ,min (self ._list_max_scroll ,self ._list_scroll_px ))

    y0_base =body_top -self ._list_scroll_px
    hover_fill =(
    _shade_hex (self ._list_panel_bg ,1.12 )
    if simple_ui 
    else _blend_hex_towards_white (self ._list_panel_bg ,0.14 )
    )
    line_px =int (self ._list_font .metrics ("linespace"))
    text_pad_y =max (2 ,(row_h -line_px )//2 )

    for i ,name in enumerate (names ):
        row_top =y0_base +i *row_h 
        if row_top <body_top or row_top +row_h >body_bottom :
            continue 

        max_w =text_right -lx -pad_x +5 
        display =name 
        if self ._list_font .measure (display )>max_w :
            ell ="…"
            while len (display )>1 and self ._list_font .measure (display +ell )>max_w :
                display =display [:-1 ]
            display =display +ell 

        if i ==self ._list_hover_row :
            self .bg_canvas .create_rectangle (
            lx +4 ,
            row_top +4 ,
            text_right ,
            row_top +row_h +4 ,
            fill =hover_fill ,
            outline ="",
            tags ="list_ui",
            )

        self .bg_canvas .create_text (
        lx +pad_x ,
        row_top +text_pad_y ,
        text =display ,
        font =self ._list_font ,
        fill =list_ink ,
        anchor ="nw",
        tags ="list_ui",
        )

    if self ._list_max_scroll >0 :
        tx0 =lx +lw -sb_w -4 
        tx1 =lx +lw -4 
        ty0 =body_top 
        ty1 =body_bottom 
        self ._list_sb_x0 ,self ._list_sb_x1 =tx0 ,tx1 
        self ._list_sb_y0 ,self ._list_sb_y1 =ty0 ,ty1 
        panel =self ._list_panel_bg 
        if simple_ui :
            track_fill =_shade_hex (panel ,0.72 )
            track_outline =gv .BREW_SIMPLE_UI_MUTED 
            thumb_fill =_blend_hex_towards_white (panel ,0.22 )
            thumb_outline =gv .BREW_SIMPLE_UI_TEXT 
        else :
            track_fill =_shade_hex (panel ,0.78 )
            track_outline =_shade_hex (gv.PARCHMENT_EDGE ,0.75 )
            thumb_fill =_blend_hex_towards_white (panel ,0.18 )
            thumb_outline =gv.MUTED 

        self .bg_canvas .create_rectangle (
        tx0 ,
        ty0 ,
        tx1 ,
        ty1 ,
        fill =track_fill ,
        outline =track_outline ,
        width =1 ,
        tags ="list_ui",
        )

        thumb_h =max (24 ,int (viewport_h *viewport_h /max (total_h ,1 )))
        self ._list_thumb_h =thumb_h 
        track_len =max (1 ,viewport_h -thumb_h )
        tpos =int (self ._list_scroll_px /self ._list_max_scroll *track_len )if self ._list_max_scroll else 0 
        t_y0 =ty0 +tpos 
        t_y1 =t_y0 +thumb_h 
        self ._list_thumb_y0 ,self ._list_thumb_y1 =t_y0 ,t_y1 
        self .bg_canvas .create_rectangle (
        tx0 +2 ,
        t_y0 +1 ,
        tx1 -2 ,
        t_y1 -1 ,
        fill =thumb_fill ,
        outline =thumb_outline ,
        width =1 ,
        tags =("list_ui","list_scroll_thumb"),
        )


