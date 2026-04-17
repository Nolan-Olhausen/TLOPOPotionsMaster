from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

import variables.brew_typography as brew_ty
import variables.global_variables as gv
from core_helpers.app_utilities import (
    _bbox_norm_to_screen_rect,
    _hex_to_rgb,
    _sample_mean_hex_image_pixels,
)
from ui_layout.simple_mode_layout import _layout_simple_compact_overlays

try:
    from PIL import Image, ImageTk  # type: ignore[import-untyped]

    PIL_OK = True
except Exception:
    Image = None  # type: ignore[assignment]
    ImageTk = None  # type: ignore[assignment]
    PIL_OK = False

try:
    _LANCZOS = Image.Resampling.LANCZOS if Image is not None else None
except Exception:
    _LANCZOS = None  # type: ignore[assignment]


def _scaled_layout_pt (base :float ,scale :float )->int :
    """Clamp scaled typography so list/strategy stay readable at extreme window sizes."""
    return max (6 ,min (44 ,int (round (float (base )*scale ))))


def _sync_ui_fonts_to_letterbox (self )->None :
    """Scale Tk fonts and list rhythm to match the letterboxed template height (``_layout_font_scale``)."""
    scale =float (getattr (self ,"_layout_font_scale",1.0 )or 1.0 )

    def sp (base :float )->int :
        return _scaled_layout_pt (base ,scale )

    try :
        self ._list_heading_font .configure (size =sp (brew_ty .LIST_HEADING_PT ))
        self ._list_font .configure (size =sp (brew_ty .LIST_ROW_PT ))
    except (tk .TclError ,AttributeError ):
        pass 

    ft =getattr (self ,"_font_title",None )
    if isinstance (ft ,tkfont .Font ):
        try :
            ft .configure (size =sp (brew_ty .RECIPE_POTION_TITLE_PT ))
        except tk .TclError :
            pass 
    elif isinstance (ft ,tuple )and ft :
        self ._font_title =(self ._font_family ,sp (brew_ty .RECIPE_POTION_TITLE_PT ),tkfont .BOLD )

    fm =getattr (self ,"_font_recipe_meta",None )
    if isinstance (fm ,tkfont .Font ):
        try :
            fm .configure (size =sp (brew_ty .RECIPE_META_LINE_PT ))
        except tk .TclError :
            pass 
    elif isinstance (fm ,tuple )and fm :
        self ._font_recipe_meta =(self ._font_family ,sp (brew_ty .RECIPE_META_LINE_PT ),tkfont .BOLD )

    fi =getattr (self ,"_font_recipe_ingredient",None )
    if isinstance (fi ,tkfont .Font ):
        try :
            fi .configure (size =sp (brew_ty .RECIPE_INGREDIENT_LINE_PT ))
        except tk .TclError :
            pass 
    elif isinstance (fi ,tuple )and fi :
        self ._font_recipe_ingredient =(self ._font_family ,sp (brew_ty .RECIPE_INGREDIENT_LINE_PT ),tkfont .BOLD )

    meta =getattr (self ,"_font_meta",None )
    if isinstance (meta ,tkfont .Font ):
        try :
            meta .configure (size =sp (brew_ty .PANEL_AND_OVERLAY_BODY_PT ))
        except tk .TclError :
            pass 
    elif isinstance (meta ,tuple )and meta :
        self ._font_meta =(self ._font_ui_family ,sp (brew_ty .PANEL_AND_OVERLAY_BODY_PT ),tkfont .BOLD )

    self ._font_strategy_menu =(self ._font_ui_family ,sp (10 ))
    self ._font_strategy_choice =(self ._font_ui_family ,sp (float (gv .GAME_STRATEGY_CHOICE_FONT_SIZE )))

    try :
        _list_ls =int (self ._list_font .metrics ("linespace"))
        self ._list_row_h =_list_ls +brew_ty .LIST_ROW_GAP_EXTRA 
        self ._list_title_block_h =(
        gv .LIST_TITLE_TOP_PAD 
        +int (self ._list_heading_font .metrics ("linespace"))
        +gv .LIST_TITLE_GAP_BELOW 
        )
    except (tk .TclError ,AttributeError ):
        pass 

    self ._brew_strategy_menu_wrap_px =max (160 ,min (620 ,int (280 *scale )))


def _initial_layout (self )->None :
    self ._redraw_background ()
    self ._layout_overlays ()


def _overlay_panel_bounds (self )->tuple [int ,int ,int ,int ]:
    """Pixel rect for embedding log/config: game art area in game view, list panel in catalog."""
    offx ,offy ,dw ,dh =self ._img_rect 
    bbox =gv .GAME_ART_BBOX if self ._view =="game"else gv .LIST_BBOX 
    x0 ,y0 ,x1 ,y1 =bbox 
    gx =int (offx +x0 *dw )
    gy =int (offy +y0 *dh )
    gw =max (48 ,int ((x1 -x0 )*dw ))
    gh =max (48 ,int ((y1 -y0 )*dh ))
    return gx ,gy ,gw ,gh 


def _game_art_screen_rect (self )->tuple [int ,int ,int ,int ]:
    """Pixel rect of ``GAME_ART_BBOX`` on the **current** letterboxed template (catalog or game).

    Use this to position/size the automation config panel so it matches the brewing-board slot
    instead of the list column (``LIST_BBOX``).
    """
    offx ,offy ,dw ,dh =self ._img_rect 
    x0 ,y0 ,x1 ,y1 =gv .GAME_ART_BBOX 
    gx =int (offx +x0 *dw )
    gy =int (offy +y0 *dh )
    gw =max (48 ,int ((x1 -x0 )*dw ))
    gh =max (48 ,int ((y1 -y0 )*dh ))
    return gx ,gy ,gw ,gh 


def _layout_app_level_chrome (self ,place )->None :
    """Config, logs, overlay, get window/locations, guided — visible on catalog and game."""
    cx0 ,cy0 ,crw ,crh =place (gv .GAME_CONFIG_TOGGLE_BBOX )
    self ._config_toggle_rect =(cx0 ,cy0 ,cx0 +crw ,cy0 +crh )
    self .bg_canvas .create_rectangle (
    cx0 ,
    cy0 ,
    cx0 +crw ,
    cy0 +crh ,
    fill =gv .GAME_UI_BUTTON_FILL ,
    outline =gv .GAME_UI_BUTTON_OUTLINE ,
    width =2 ,
    tags =("game_ui","config_toggle_btn"),
    )
    ccx =cx0 +crw //2 
    ccy =cy0 +crh //2 
    cfg_lbl ="Hide config"if self ._game_config_visible else "Config Panel"
    self .bg_canvas .create_text (
    ccx ,
    ccy ,
    text =cfg_lbl ,
    font =self ._font_meta ,
    fill =gv .GAME_UI_BUTTON_TEXT ,
    anchor ="center",
    tags =("game_ui","config_toggle_label"),
    )

    lx0 ,ly0 ,lrw ,lrh =place (gv .GAME_LOGS_TOGGLE_BBOX )
    self ._logs_toggle_rect =(lx0 ,ly0 ,lx0 +lrw ,ly0 +lrh )
    self .bg_canvas .create_rectangle (
    lx0 ,
    ly0 ,
    lx0 +lrw ,
    ly0 +lrh ,
    fill =gv .GAME_UI_BUTTON_FILL ,
    outline =gv .GAME_UI_BUTTON_OUTLINE ,
    width =2 ,
    tags =("game_ui","logs_toggle_btn"),
    )
    llx =lx0 +lrw //2 
    lly =ly0 +lrh //2 
    logs_lbl ="Hide logs"if self ._game_log_visible else "Logs"
    self .bg_canvas .create_text (
    llx ,
    lly ,
    text =logs_lbl ,
    font =self ._font_meta ,
    fill =gv .GAME_UI_BUTTON_TEXT ,
    anchor ="center",
    tags =("game_ui","logs_toggle_label"),
    )

    ox0 ,oy0 ,orw ,orh =place (gv .GAME_OVERLAY_TOGGLE_BBOX )
    self ._overlay_toggle_rect =(ox0 ,oy0 ,ox0 +orw ,oy0 +orh )
    self .bg_canvas .create_rectangle (
    ox0 ,
    oy0 ,
    ox0 +orw ,
    oy0 +orh ,
    fill =gv .GAME_UI_BUTTON_FILL ,
    outline =gv .GAME_UI_BUTTON_OUTLINE ,
    width =2 ,
    tags =("game_ui","overlay_toggle_btn"),
    )
    ocx =ox0 +orw //2 
    ocy =oy0 +orh //2 
    overlay_lbl =(
    "Hide overlay"
    if self ._game_tlopo_overlay is not None and self ._game_tlopo_overlay .active 
    else "Object overlay"
    )
    self .bg_canvas .create_text (
    ocx ,
    ocy ,
    text =overlay_lbl ,
    font =self ._font_meta ,
    fill =gv .GAME_UI_BUTTON_TEXT ,
    anchor ="center",
    justify ="center",
    width =max (36 ,orw -6 ),
    tags =("game_ui","overlay_toggle_label"),
    )

    wx0 ,wy0 ,wrw ,wrh =place (gv .GAME_GET_WINDOW_BBOX )
    self ._get_window_btn_rect =(wx0 ,wy0 ,wx0 +wrw ,wy0 +wrh )
    self .bg_canvas .create_rectangle (
    wx0 ,
    wy0 ,
    wx0 +wrw ,
    wy0 +wrh ,
    fill =gv .GAME_UI_BUTTON_FILL ,
    outline =gv .GAME_UI_BUTTON_OUTLINE ,
    width =2 ,
    tags =("game_ui","get_window_btn"),
    )
    wcx =wx0 +wrw //2 
    wcy =wy0 +wrh //2 
    self .bg_canvas .create_text (
    wcx ,
    wcy ,
    text =self ._game_get_window_caption ,
    font =self ._font_meta ,
    fill =gv .GAME_UI_BUTTON_TEXT ,
    anchor ="center",
    justify ="center",
    width =max (72 ,wrw -10 ),
    tags =("game_ui","get_window_label"),
    )

    gox ,goy ,gorw ,gorh =place (gv .GAME_GET_OBJECTS_BBOX )
    self ._get_objects_btn_rect =(gox ,goy ,gox +gorw ,goy +gorh )
    ob_fill ,ob_outline ,ob_text =self ._get_objects_button_style ()
    self .bg_canvas .create_rectangle (
    gox ,
    goy ,
    gox +gorw ,
    goy +gorh ,
    fill =ob_fill ,
    outline =ob_outline ,
    width =2 ,
    tags =("game_ui","get_objects_btn"),
    )
    gocx =gox +gorw //2 
    gocy =goy +gorh //2 
    self .bg_canvas .create_text (
    gocx ,
    gocy ,
    text =self ._game_get_objects_caption ,
    font =self ._font_meta ,
    fill =ob_text ,
    anchor ="center",
    justify ="center",
    width =max (72 ,gorw -10 ),
    tags =("game_ui","get_objects_label"),
    )

    gx0 ,gy0 ,grw ,grh =place (gv .GAME_GUIDED_CONFIG_BBOX )
    self ._guided_config_btn_rect =(gx0 ,gy0 ,gx0 +grw ,gy0 +grh )
    self .bg_canvas .create_rectangle (
    gx0 ,
    gy0 ,
    gx0 +grw ,
    gy0 +grh ,
    fill =gv .GAME_UI_BUTTON_FILL ,
    outline =gv .GAME_UI_BUTTON_OUTLINE ,
    width =2 ,
    tags =("game_ui","guided_config_btn"),
    )
    gcx =gx0 +grw //2 
    gcy =gy0 +grh //2 
    self .bg_canvas .create_text (
    gcx ,
    gcy ,
    text =self ._guided_config_caption (),
    font =self ._font_meta ,
    fill =gv .GAME_UI_BUTTON_TEXT ,
    anchor ="center",
    justify ="center",
    width =max (72 ,grw -6 ),
    tags =("game_ui","guided_config_label"),
    )


def _schedule_resize (self ,event :tk .Event )->None :
    if event .widget is not self .root :
        return 
    if self ._resize_job is not None :
        self .root .after_cancel (self ._resize_job )
    self ._resize_job =self .root .after (120 ,self ._resize_done )


def _resize_done (self )->None :
    self ._resize_job =None 
    self ._redraw_background ()
    self ._layout_overlays ()


def _redraw_background (self )->None :
    """Paint the full canvas black and **letterbox** the active template (uniform scale, centered).

    Normalized UI bboxes (``gv.*_BBOX``) are interpreted in template space; ``_layout_overlays``
    maps them into the current ``_img_rect``. Extra window area stays **black** (pillarbox /
    letterbox bars) so the layout keeps the template aspect ratio.
    """
    self .bg_canvas .update_idletasks ()
    w =max (self .root .winfo_width (),1 )
    h =max (self .root .winfo_height (),1 )

    if getattr (self ,"_brew_simple_ui",False ):
        self ._img_rect =(0 ,0 ,w ,h )
        ref_h =720.0 
        raw =h /ref_h 
        self ._layout_font_scale =max (0.55 ,min (2.2 ,round (raw *20 )/20.0 ))
        self ._recipe_panel_bg =gv .BREW_SIMPLE_UI_PANEL_BG 
        self ._list_panel_bg =gv .BREW_SIMPLE_UI_PANEL_BG 
        self ._bg_imgtk =None 
        self .bg_canvas .delete ("bg")
        self .bg_canvas .configure (bg =gv .BREW_SIMPLE_UI_CANVAS_BG )
    else :
        pil =self ._active_pil_template ()
        if pil is not None and PIL_OK and ImageTk is not None and _LANCZOS is not None :
            iw ,ih =pil .size 
            scale =min (w /iw ,h /ih )
            dw =max (1 ,int (iw *scale ))
            dh =max (1 ,int (ih *scale ))
            offx =(w -dw )//2 
            offy =(h -dh )//2 
            self ._img_rect =(offx ,offy ,dw ,dh )
            raw =dh /float (ih )if ih >0 else 1.0 
            self ._layout_font_scale =max (0.55 ,min (2.2 ,round (raw *20 )/20.0 ))
            resized =pil .resize ((dw ,dh ),_LANCZOS )
            rgb_black =_hex_to_rgb (gv.BLACK )
            canvas_img =Image .new ("RGB",(w ,h ),rgb_black )
            canvas_img .paste (resized ,(offx ,offy ))

            if self ._view =="catalog":
                r_bbox ,l_bbox =gv.RECIPE_BBOX ,gv.LIST_BBOX 
            else :
                r_bbox ,l_bbox =gv.RECIPE_BBOX ,gv.GAME_ART_BBOX 
            rl ,rt ,rr ,rb =_bbox_norm_to_screen_rect (offx ,offy ,dw ,dh ,r_bbox )
            ll ,lt ,lr ,lb =_bbox_norm_to_screen_rect (offx ,offy ,dw ,dh ,l_bbox )
            sr =_sample_mean_hex_image_pixels (canvas_img ,rl ,rt ,rr ,rb )
            sl =_sample_mean_hex_image_pixels (canvas_img ,ll ,lt ,lr ,lb )
            self ._recipe_panel_bg =sr 
            self ._list_panel_bg =sl 

            self ._bg_imgtk =ImageTk .PhotoImage (canvas_img )
            self .bg_canvas .delete ("bg")
            self .bg_canvas .create_image (0 ,0 ,image =self ._bg_imgtk ,anchor ="nw",tags ="bg")
            self .bg_canvas .tag_lower ("bg")
        else :
            self ._img_rect =(0 ,0 ,w ,h )
            self ._layout_font_scale =1.0 
            self ._recipe_panel_bg =gv.BLACK 
            self ._list_panel_bg =gv.BLACK 
            self .bg_canvas .delete ("bg")
            self .bg_canvas .configure (bg =gv.BLACK )

    self ._sync_ui_fonts_to_letterbox ()

    self ._prev_list_sample =self ._list_panel_bg 

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


def _layout_overlays (self )->None :
    w =max (self .root .winfo_width (),1 )
    h =max (self .root .winfo_height (),1 )
    offx ,offy ,dw ,dh =self ._img_rect 

    def place (bbox :tuple [float ,float ,float ,float ])->tuple [int ,int ,int ,int ]:
        """Map normalized template bbox to pixels. Min32×32 for hit targets; when clamped,
        keep the rect centered on the template band so thin regions (e.g. switch recipe)
        stay aligned across window sizes."""
        x0 ,y0 ,x1 ,y1 =bbox 
        x =int (offx +x0 *dw )
        y =int (offy +y0 *dh )
        rw_nat =int ((x1 -x0 )*dw )
        rh_nat =int ((y1 -y0 )*dh )
        rw =max (32 ,rw_nat )
        rh =max (32 ,rh_nat )
        if rw >rw_nat :
            x_left =int (offx +x0 *dw )
            x_right =int (offx +x1 *dw )
            x =(x_left +x_right )//2 -rw //2 
        if rh >rh_nat :
            y_top =int (offy +y0 *dh )
            y_bot =int (offy +y1 *dh )
            y =(y_top +y_bot )//2 -rh //2 
        return x ,y ,rw ,rh 

    self ._destroy_game_strategy_embed ()
    self ._destroy_credits_embed ()
    self .bg_canvas .delete ("game_ui")
    self .bg_canvas .delete ("hex_grid")
    self .bg_canvas .delete ("credits_layer")
    if self ._view =="catalog":
        self ._back_hit_rect =(0 ,0 ,0 ,0 )
        self ._automation_start_btn_rect =(0 ,0 ,0 ,0 )
        simple_ui =getattr (self ,"_brew_simple_ui",False )
        if simple_ui :
            _layout_simple_compact_overlays (self ,include_game_controls =False )
            self ._draw_list_canvas_layer ()
            self ._draw_recipe_canvas_layer ()
            if self ._game_log_visible :
                self ._draw_game_log_layer ()
            if self ._game_config_visible :
                self ._draw_game_config_layer ()
            self .bg_canvas .tag_raise ("list_ui")
            self .bg_canvas .tag_raise ("recipe_ui")
            self .bg_canvas .tag_raise ("game_ui")
            if getattr (self ,"_credits_visible",False ):
                self ._draw_credits_layer ()
            if self .bg_canvas .find_withtag ("credits_layer"):
                self .bg_canvas .tag_raise ("credits_layer")
        else :
            rx ,ry ,rw ,rh =place (gv.RECIPE_BBOX )
            self ._recipe_rect =(rx ,ry ,rw ,rh )

            lx ,ly ,lw ,lh =place (gv.LIST_BBOX )
            self ._list_rect =(lx ,ly ,lw ,lh )

            self ._layout_app_level_chrome (place )

            crx0 ,cry0 ,crw ,crh =place (gv .CATALOG_CREDITS_BBOX )
            self ._credits_btn_rect =(crx0 ,cry0 ,crx0 +crw ,cry0 +crh )
            self .bg_canvas .create_rectangle (
            crx0 ,
            cry0 ,
            crx0 +crw ,
            cry0 +crh ,
            fill =gv .GAME_UI_BUTTON_FILL ,
            outline =gv .GAME_UI_BUTTON_OUTLINE ,
            width =2 ,
            tags =("game_ui","credits_btn"),
            )
            crcx =crx0 +crw //2 
            crcy =cry0 +crh //2 
            self .bg_canvas .create_text (
            crcx ,
            crcy ,
            text ="Credits",
            font =self ._font_meta ,
            fill =gv .GAME_UI_BUTTON_TEXT ,
            anchor ="center",
            tags =("game_ui","credits_label"),
            )

            self ._draw_list_canvas_layer ()
            self ._draw_recipe_canvas_layer ()
            if self ._game_log_visible :
                self ._draw_game_log_layer ()
            if self ._game_config_visible :
                self ._draw_game_config_layer ()
            self .bg_canvas .tag_raise ("list_ui")
            self .bg_canvas .tag_raise ("recipe_ui")
            self .bg_canvas .tag_raise ("game_ui")
            if getattr (self ,"_credits_visible",False ):
                self ._draw_credits_layer ()
            if self .bg_canvas .find_withtag ("credits_layer"):
                self .bg_canvas .tag_raise ("credits_layer")
    else :
        self ._credits_btn_rect =(0 ,0 ,0 ,0 )
        simple_ui =getattr (self ,"_brew_simple_ui",False )
        if simple_ui :
            _layout_simple_compact_overlays (self ,include_game_controls =True )
            self ._draw_list_canvas_layer ()
            self ._draw_recipe_canvas_layer ()
            self ._draw_hex_grid_layer ()
            self .bg_canvas .tag_raise ("list_ui")
            self .bg_canvas .tag_raise ("recipe_ui")
            if self ._game_log_visible :
                self ._draw_game_log_layer ()
            if self ._game_config_visible :
                self ._draw_game_config_layer ()
            self .bg_canvas .tag_raise ("game_ui")
        else :
            rx ,ry ,rw ,rh =place (gv.RECIPE_BBOX )
            self ._recipe_rect =(rx ,ry ,rw ,rh )
            self ._list_rect =(0 ,0 ,0 ,0 )
            # Simple game draws the potion list on canvas; fancy does not. Clear stale ``list_ui``.
            self ._draw_list_canvas_layer ()

            gx ,gy ,gw ,gh =place (gv.GAME_ART_BBOX )
            self ._game_board_rect =(gx ,gy ,gw ,gh )

            bx0 ,by0 ,brw ,brh =place (gv.GAME_BACK_BBOX )
            self ._back_hit_rect =(bx0 ,by0 ,bx0 +brw ,by0 +brh )
            tcx =bx0 +brw //2 
            tcy =by0 +brh //2 
            self .bg_canvas .create_text (
            tcx ,
            tcy ,
            text ="switch recipe",
            font =self ._font_recipe_meta ,
            fill =gv.MUTED ,
            anchor ="center",
            tags =("game_ui","back_btn_text"),
            )

            self ._layout_app_level_chrome (place )

            sx0 ,sy0 ,srw ,srh =place (gv.GAME_STRATEGY_BBOX )
            self ._draw_game_strategy_embed (sx0 ,sy0 ,srw ,srh )

            ax0 ,ay0 ,arw ,arh =place (gv.GAME_AUTOMATION_START_BBOX )
            self ._automation_start_btn_rect =(ax0 ,ay0 ,ax0 +arw ,ay0 +arh )
            as_fill ,as_outline ,as_text ,as_lbl =self ._automation_start_button_style ()
            self .bg_canvas .create_rectangle (
            ax0 ,
            ay0 ,
            ax0 +arw ,
            ay0 +arh ,
            fill =as_fill ,
            outline =as_outline ,
            width =2 ,
            tags =("game_ui","automation_start_btn"),
            )
            acx =ax0 +arw //2 
            acy =ay0 +arh //2 
            self .bg_canvas .create_text (
            acx ,
            acy ,
            text =as_lbl ,
            font =self ._font_meta ,
            fill =as_text ,
            anchor ="center",
            justify ="center",
            width =max (56 ,arw -8 ),
            tags =("game_ui","automation_start_label"),
            )

            self ._draw_recipe_canvas_layer ()
            self ._draw_hex_grid_layer ()
            self .bg_canvas .tag_raise ("hex_grid")
            if self .bg_canvas .find_withtag ("board_memory_piece"):
                self .bg_canvas .tag_raise ("board_memory_piece")
            self .bg_canvas .tag_raise ("recipe_ui")
            if self ._game_log_visible :
                self ._draw_game_log_layer ()
            if self ._game_config_visible :
                self ._draw_game_config_layer ()
            self .bg_canvas .tag_raise ("game_ui")


