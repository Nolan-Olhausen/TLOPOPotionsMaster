from __future__ import annotations

import sys
import time
import tkinter as tk
import tkinter.font as tkfont
import tkinter.messagebox as messagebox
from pathlib import Path
from typing import Any

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

def _open_guided_color_wizard (self )->None :
    if not (self ._game_prereq_window_ok and self ._game_prereq_objects_ok ):
        messagebox .showwarning (
        "Guided config",
        "Run Get Window and Get Locations first so the client window and shape polygons are ready.",
        parent =self .root ,
        )
        return 
    prev =self ._guided_wizard_top 
    if prev is not None :
        try :
            if prev .winfo_exists ():
                prev .lift ()
                prev .focus_force ()
                return 
        except tk .TclError :
            pass 
        self ._guided_wizard_top =None 

    color_human ={
    "R":"Red",
    "G":"Green",
    "B":"Blue",
    "Grey":"Grey",
    "O":"Orange",
    "P":"Purple",
    }

    w =tk .Toplevel (self .root )
    self ._guided_wizard_top =w 
    # Typography tied to ``brew_typography`` base sizes only — not ``_layout_font_scale`` from the main window.
    wiz_title =(
    getattr (self ,"_font_family","TkDefaultFont"),
    brew_ty .RECIPE_POTION_TITLE_PT ,
    tkfont .BOLD ,
    )
    wiz_meta =(
    self ._font_ui_family ,
    brew_ty .PANEL_AND_OVERLAY_BODY_PT ,
    tkfont .BOLD ,
    )
    w .title ("Guided color calibration")
    w .transient (self .root )
    w .resizable (True ,True )
    try :
        w .geometry (gv.GAME_GUIDED_WIZARD_GEOMETRY )
    except tk .TclError :
        pass 

    outer =tk .Frame (w ,padx =14 ,pady =12 )
    outer .pack (fill =tk .BOTH ,expand =True )

    tk .Label (outer ,text ="Color calibration",font =wiz_title ).pack (anchor =tk .W )
    tk .Label (
    outer ,
    text =(
    "Per row: match the piece in-game, Capture, tweak R/G/B if needed. "
    "Status shows Pending until you use **Save all** (saves empty-board RGB, every pending row, and settings). "
    "Ring samples often look muted — that is normal. "
    "Next columns store ring medians per slot; Current columns also update display RGB for that color."
    ),
    font =wiz_meta ,
    wraplength =gv.GAME_GUIDED_WIZARD_WRAPLENGTH ,
    justify =tk .LEFT ,
    ).pack (anchor =tk .W ,pady =(0 ,8 ))

    scroll_wrap =tk .Frame (outer )
    scroll_wrap .pack (fill =tk .BOTH ,expand =True )
    sb =tk .Scrollbar (scroll_wrap ,orient =tk .VERTICAL )
    sb .pack (side =tk .RIGHT ,fill =tk .Y )
    canvas =tk .Canvas (scroll_wrap ,highlightthickness =0 ,bg ="#2a2a2e")
    canvas .pack (side =tk .LEFT ,fill =tk .BOTH ,expand =True )
    sb .config (command =canvas .yview )
    canvas .config (yscrollcommand =sb .set )

    inner =tk .Frame (canvas ,bg ="#2a2a2e")
    inner_id =canvas .create_window ((0 ,0 ),window =inner ,anchor =tk .NW )

    def _on_inner_cfg (_evt :tk .Event |None =None )->None :
        canvas .configure (scrollregion =canvas .bbox ("all"))

    def _on_canvas_cfg (evt :tk .Event )->None :
        canvas .itemconfigure (inner_id ,width =max (1 ,int (evt .width )))

    inner .bind ("<Configure>",_on_inner_cfg )
    canvas .bind ("<Configure>",_on_canvas_cfg )

    def _wheel_units (evt :tk .Event )->int :
        d =int (getattr (evt ,"delta",0 )or 0 )
        if d !=0 :
            step =int (-1 *(d /120 ))
            if step ==0 :
                return -1 if d >0 else 1 
            return step
        num =getattr (evt ,"num",None )
        if num ==4 :
            return -3
        if num ==5 :
            return 3
        return 0

    def _wheel (evt :tk .Event )->str |None :
        step =_wheel_units (evt )
        if step ==0 :
            return None
        canvas .yview_scroll (step ,"units")
        return "break"

    def _bind_wheel_recursive (widget :tk .Misc )->None :
        widget .bind ("<MouseWheel>",_wheel ,add ="+")
        widget .bind ("<Button-4>",_wheel ,add ="+")
        widget .bind ("<Button-5>",_wheel ,add ="+")
        for child in widget .winfo_children ():
            _bind_wheel_recursive (child )

    row_state :dict [tuple [str ,str ],dict [str ,Any ]]={}

    def _parse_rgb_vars (
    vr :tk .StringVar ,vg :tk .StringVar ,vb :tk .StringVar 
    )->tuple [int ,int ,int ]|None :
        try :
            r =int (str (vr .get ()).strip ())
            g =int (str (vg .get ()).strip ())
            b =int (str (vb .get ()).strip ())
        except (TypeError ,ValueError ):
            return None 
        if not (0 <=r <=255 and 0 <=g <=255 and 0 <=b <=255 ):
            return None 
        return r ,g ,b 

    def _paint_cv (cnv :tk .Canvas ,r :int ,g :int ,b :int )->None :
        hx =_rgb888_to_hex (r ,g ,b )
        cnv .delete ("p")
        cnv .create_rectangle (2 ,2 ,35 ,35 ,fill =hx ,outline ="#888888",tags ="p")

    def grab_capture_bundle ()->tuple [Any ,Path ]|None :# frame_bgra, shapes_path
        try :
            from brew_core.object_recognition import capture_recognition_bundle_for_ui 
            from tlopo_client.window import TlopoGameWindow ,win32_set_foreground_window
        except ImportError as e :
            messagebox .showerror ("Guided config",str (e ),parent =w )
            return None 

        det =TlopoGameWindow (log =lambda _m :None )
        if not det .find_window ()or not det .is_valid ():
            messagebox .showerror (
            "Guided config",
            "TLOPO window not found. Run Get Window and Get Locations first.",
            parent =w ,
            )
            return None 
        brew_hwnd =0 
        if sys .platform =="win32":
            try :
                brew_hwnd =int (self .root .winfo_id ())
            except (tk .TclError ,TypeError ,ValueError ):
                brew_hwnd =0 
        if sys .platform =="win32"and brew_hwnd >0 :
            det .bring_to_foreground_for_capture ()
            time .sleep (0.07 )
        rect =det .get_client_rect_mss_aligned ()
        if not rect :
            messagebox .showerror (
            "Guided config","Could not read the game client rectangle.",parent =w 
            )
            return None 
        bundle =capture_recognition_bundle_for_ui (rect ,log =self ._game_error_log )
        if sys .platform =="win32"and brew_hwnd >0 :
            try :
                win32_set_foreground_window (brew_hwnd )
            except Exception :
                pass 
        if bundle is None :
            messagebox .showerror ("Guided config","Screen capture failed.",parent =w )
            return None 
        return bundle ["frame_bgra"],bundle ["path"]

    board_fr =tk .LabelFrame (
    inner ,text ="Empty board (left slot)",font =wiz_meta ,padx =8 ,pady =8 
    )
    board_fr .pack (fill =tk .X ,pady =(0 ,10 ))

    br =tk .StringVar (value =str (int (self ._brew_board_await_r )))
    bg_ =tk .StringVar (value =str (int (self ._brew_board_await_g )))
    bb =tk .StringVar (value =str (int (self ._brew_board_await_b )))

    b_row =tk .Frame (board_fr )
    b_row .pack (anchor =tk .W )
    btn_board_cap =tk .Button (b_row ,text ="Capture",font =wiz_meta )
    btn_board_cap .pack (side =tk .LEFT ,padx =(0 ,8 ))
    tk .Label (b_row ,text ="R",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (b_row ,textvariable =br ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    tk .Label (b_row ,text ="G",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (b_row ,textvariable =bg_ ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    tk .Label (b_row ,text ="B",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (b_row ,textvariable =bb ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    bcv =tk .Canvas (
    b_row ,
    width =38 ,
    height =38 ,
    highlightthickness =1 ,
    highlightbackground ="#555555",
    bg ="#2a2a2e",
    )
    bcv .pack (side =tk .LEFT ,padx =(12 ,0 ))
    _paint_cv (
    bcv ,
    int (self ._brew_board_await_r ),
    int (self ._brew_board_await_g ),
    int (self ._brew_board_await_b ),
    )

    def _board_preview (*_a :Any )->None :
        t =_parse_rgb_vars (br ,bg_ ,bb )
        if t is None :
            return 
        _paint_cv (bcv ,t [0 ],t [1 ],t [2 ])

    br .trace_add ("write",lambda *_ :_board_preview ())
    bg_ .trace_add ("write",lambda *_ :_board_preview ())
    bb .trace_add ("write",lambda *_ :_board_preview ())

    def do_board_capture ()->None :
        got =grab_capture_bundle ()
        if got is None :
            return 
        frame_bgra ,path =got 
        try :
            from brew_core.next_pieces import (
            resolve_first_polygon_label ,
            sample_polygon_median_bgra ,
            )
        except ImportError as e :
            messagebox .showerror ("Guided config",str (e ),parent =w )
            return 
        poly =resolve_first_polygon_label (
        path ,("current_piece_left","validation_left")
        )
        if not poly :
            messagebox .showerror (
            "Guided config",
            "No `current_piece_left` or `validation_left` polygon in object_shapes.json.",
            parent =w ,
            )
            return 
        bg =sample_polygon_median_bgra (frame_bgra ,path ,poly )
        if not bg .get ("ok"):
            messagebox .showerror (
            "Guided config",
            str (bg .get ("error","Board color sample failed.")),
            parent =w ,
            )
            return 
        br .set (str (int (bg ["r"])))
        bg_ .set (str (int (bg ["g"])))
        bb .set (str (int (bg ["b"])))
        _board_preview ()

    btn_board_cap .config (command =do_board_capture )

    again_fr =tk .LabelFrame (
    inner ,text ="Brew Again button",font =wiz_meta ,padx =8 ,pady =8 
    )
    again_fr .pack (fill =tk .X ,pady =(0 ,10 ))
    abr =tk .StringVar (value =str (int (self ._brew_again_r )))
    abg =tk .StringVar (value =str (int (self ._brew_again_g )))
    abb =tk .StringVar (value =str (int (self ._brew_again_b )))
    a_row =tk .Frame (again_fr )
    a_row .pack (anchor =tk .W )
    btn_again_cap =tk .Button (a_row ,text ="Capture",font =wiz_meta )
    btn_again_cap .pack (side =tk .LEFT ,padx =(0 ,8 ))
    tk .Label (a_row ,text ="R",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (a_row ,textvariable =abr ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    tk .Label (a_row ,text ="G",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (a_row ,textvariable =abg ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    tk .Label (a_row ,text ="B",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (a_row ,textvariable =abb ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    acv =tk .Canvas (
    a_row ,
    width =38 ,
    height =38 ,
    highlightthickness =1 ,
    highlightbackground ="#555555",
    bg ="#2a2a2e",
    )
    acv .pack (side =tk .LEFT ,padx =(12 ,0 ))
    _paint_cv (acv ,int (self ._brew_again_r ),int (self ._brew_again_g ),int (self ._brew_again_b ))

    def _again_preview (*_a :Any )->None :
        t =_parse_rgb_vars (abr ,abg ,abb )
        if t is None :
            return 
        _paint_cv (acv ,t [0 ],t [1 ],t [2 ])

    abr .trace_add ("write",lambda *_ :_again_preview ())
    abg .trace_add ("write",lambda *_ :_again_preview ())
    abb .trace_add ("write",lambda *_ :_again_preview ())

    def do_again_capture ()->None :
        try :
            from brew_core.object_recognition import run_get_objects_pipeline 
            from tlopo_client.window import TlopoGameWindow ,win32_set_foreground_window 
        except ImportError as e :
            messagebox .showerror ("Guided config",str (e ),parent =w )
            return 
        got =grab_capture_bundle ()
        if got is None :
            return 
        frame_bgra ,path =got 
        det =TlopoGameWindow (log =lambda _m :None )
        if not det .find_window ()or not det .is_valid ():
            messagebox .showerror ("Guided config","TLOPO window not found.",parent =w )
            return 
        brew_hwnd =0 
        if sys .platform =="win32":
            try :
                brew_hwnd =int (self .root .winfo_id ())
            except (tk .TclError ,TypeError ,ValueError ):
                brew_hwnd =0 
        try :
            if sys .platform =="win32"and brew_hwnd >0 :
                det .bring_to_foreground_for_capture ()
                time .sleep (0.05 )
            rect =det .get_client_rect_mss_aligned ()
            if not rect :
                messagebox .showerror ("Guided config","No client rectangle.",parent =w )
                return 
            results ,cap_ok ,_piece =run_get_objects_pipeline (
            rect ,
            shapes_json =path ,
            log =self ._game_error_log ,
            verbose_logs =False ,
            )
        except Exception as e :
            messagebox .showerror ("Guided config",f"Brew Again sample failed: {e}",parent =w )
            return 
        finally :
            if sys .platform =="win32"and brew_hwnd >0 :
                try :
                    win32_set_foreground_window (brew_hwnd )
                except Exception :
                    pass 
        if not cap_ok or not isinstance (results ,list ):
            messagebox .showerror ("Guided config","Brew Again capture failed.",parent =w )
            return 
        ra =next ((r for r in results if str (r .get ("label",""))=="brew_again"),None )
        if not isinstance (ra ,dict ):
            messagebox .showerror (
            "Guided config",
            "No `brew_again` location found in object_shapes.json.",
            parent =w ,
            )
            return 
        rgb =self ._sample_result_box_median_rgb (frame_bgra ,ra )
        if rgb is None :
            messagebox .showerror (
            "Guided config",
            "Could not sample Brew Again RGB from the captured box.",
            parent =w ,
            )
            return 
        abr .set (str (int (rgb [0 ])))
        abg .set (str (int (rgb [1 ])))
        abb .set (str (int (rgb [2 ])))
        _again_preview ()

    btn_again_cap .config (command =do_again_capture )

    again_ok_fr =tk .LabelFrame (
    inner ,text ="Brew Again OK button",font =wiz_meta ,padx =8 ,pady =8 
    )
    again_ok_fr .pack (fill =tk .X ,pady =(0 ,10 ))
    aokr =tk .StringVar (value =str (int (self ._brew_again_ok_r )))
    aokg =tk .StringVar (value =str (int (self ._brew_again_ok_g )))
    aokb =tk .StringVar (value =str (int (self ._brew_again_ok_b )))
    aok_row =tk .Frame (again_ok_fr )
    aok_row .pack (anchor =tk .W )
    btn_again_ok_cap =tk .Button (aok_row ,text ="Capture",font =wiz_meta )
    btn_again_ok_cap .pack (side =tk .LEFT ,padx =(0 ,8 ))
    tk .Label (aok_row ,text ="R",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (aok_row ,textvariable =aokr ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    tk .Label (aok_row ,text ="G",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (aok_row ,textvariable =aokg ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    tk .Label (aok_row ,text ="B",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (aok_row ,textvariable =aokb ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    aokcv =tk .Canvas (
    aok_row ,
    width =38 ,
    height =38 ,
    highlightthickness =1 ,
    highlightbackground ="#555555",
    bg ="#2a2a2e",
    )
    aokcv .pack (side =tk .LEFT ,padx =(12 ,0 ))
    _paint_cv (aokcv ,int (self ._brew_again_ok_r ),int (self ._brew_again_ok_g ),int (self ._brew_again_ok_b ))

    def _again_ok_preview (*_a :Any )->None :
        t =_parse_rgb_vars (aokr ,aokg ,aokb )
        if t is None :
            return 
        _paint_cv (aokcv ,t [0 ],t [1 ],t [2 ])

    aokr .trace_add ("write",lambda *_ :_again_ok_preview ())
    aokg .trace_add ("write",lambda *_ :_again_ok_preview ())
    aokb .trace_add ("write",lambda *_ :_again_ok_preview ())

    def do_again_ok_capture ()->None :
        try :
            from brew_core.object_recognition import run_get_objects_pipeline 
            from tlopo_client.window import TlopoGameWindow ,win32_set_foreground_window 
        except ImportError as e :
            messagebox .showerror ("Guided config",str (e ),parent =w )
            return 
        got =grab_capture_bundle ()
        if got is None :
            return 
        frame_bgra ,path =got 
        det =TlopoGameWindow (log =lambda _m :None )
        if not det .find_window ()or not det .is_valid ():
            messagebox .showerror ("Guided config","TLOPO window not found.",parent =w )
            return 
        brew_hwnd =0 
        if sys .platform =="win32":
            try :
                brew_hwnd =int (self .root .winfo_id ())
            except (tk .TclError ,TypeError ,ValueError ):
                brew_hwnd =0 
        try :
            if sys .platform =="win32"and brew_hwnd >0 :
                det .bring_to_foreground_for_capture ()
                time .sleep (0.05 )
            rect =det .get_client_rect_mss_aligned ()
            if not rect :
                messagebox .showerror ("Guided config","No client rectangle.",parent =w )
                return 
            results ,cap_ok ,_piece =run_get_objects_pipeline (
            rect ,
            shapes_json =path ,
            log =self ._game_error_log ,
            verbose_logs =False ,
            )
        except Exception as e :
            messagebox .showerror ("Guided config",f"Brew Again OK sample failed: {e}",parent =w )
            return 
        finally :
            if sys .platform =="win32"and brew_hwnd >0 :
                try :
                    win32_set_foreground_window (brew_hwnd )
                except Exception :
                    pass 
        if not cap_ok or not isinstance (results ,list ):
            messagebox .showerror ("Guided config","Brew Again OK capture failed.",parent =w )
            return 
        aok =next ((r for r in results if str (r .get ("label",""))=="brew_again_ok"),None )
        if not isinstance (aok ,dict ):
            messagebox .showerror (
            "Guided config",
            "No `brew_again_ok` location found in object_shapes.json.",
            parent =w ,
            )
            return 
        rgb =self ._sample_result_box_median_rgb (frame_bgra ,aok )
        if rgb is None :
            messagebox .showerror (
            "Guided config",
            "Could not sample Brew Again OK RGB from the captured box.",
            parent =w ,
            )
            return 
        aokr .set (str (int (rgb [0 ])))
        aokg .set (str (int (rgb [1 ])))
        aokb .set (str (int (rgb [2 ])))
        _again_ok_preview ()

    btn_again_ok_cap .config (command =do_again_ok_capture )

    fail_fr =tk .LabelFrame (
    inner ,text ="Potion Failed Continue button",font =wiz_meta ,padx =8 ,pady =8 
    )
    fail_fr .pack (fill =tk .X ,pady =(0 ,10 ))
    pfcr =tk .StringVar (value =str (int (self ._potion_failed_continue_r )))
    pfcg =tk .StringVar (value =str (int (self ._potion_failed_continue_g )))
    pfcb =tk .StringVar (value =str (int (self ._potion_failed_continue_b )))
    pfc_row =tk .Frame (fail_fr )
    pfc_row .pack (anchor =tk .W )
    btn_fail_cap =tk .Button (pfc_row ,text ="Capture",font =wiz_meta )
    btn_fail_cap .pack (side =tk .LEFT ,padx =(0 ,8 ))
    tk .Label (pfc_row ,text ="R",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (pfc_row ,textvariable =pfcr ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    tk .Label (pfc_row ,text ="G",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (pfc_row ,textvariable =pfcg ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    tk .Label (pfc_row ,text ="B",font =wiz_meta ).pack (side =tk .LEFT )
    tk .Entry (pfc_row ,textvariable =pfcb ,width =5 ,font =wiz_meta ).pack (side =tk .LEFT ,padx =2 )
    pfccv =tk .Canvas (
    pfc_row ,
    width =38 ,
    height =38 ,
    highlightthickness =1 ,
    highlightbackground ="#555555",
    bg ="#2a2a2e",
    )
    pfccv .pack (side =tk .LEFT ,padx =(12 ,0 ))
    _paint_cv (pfccv ,int (self ._potion_failed_continue_r ),int (self ._potion_failed_continue_g ),int (self ._potion_failed_continue_b ))

    def _fail_preview (*_a :Any )->None :
        t =_parse_rgb_vars (pfcr ,pfcg ,pfcb )
        if t is None :
            return 
        _paint_cv (pfccv ,t [0 ],t [1 ],t [2 ])

    pfcr .trace_add ("write",lambda *_ :_fail_preview ())
    pfcg .trace_add ("write",lambda *_ :_fail_preview ())
    pfcb .trace_add ("write",lambda *_ :_fail_preview ())

    def do_fail_capture ()->None :
        try :
            from brew_core.object_recognition import run_get_objects_pipeline 
            from tlopo_client.window import TlopoGameWindow ,win32_set_foreground_window 
        except ImportError as e :
            messagebox .showerror ("Guided config",str (e ),parent =w )
            return 
        got =grab_capture_bundle ()
        if got is None :
            return 
        frame_bgra ,path =got 
        det =TlopoGameWindow (log =lambda _m :None )
        if not det .find_window ()or not det .is_valid ():
            messagebox .showerror ("Guided config","TLOPO window not found.",parent =w )
            return 
        brew_hwnd =0 
        if sys .platform =="win32":
            try :
                brew_hwnd =int (self .root .winfo_id ())
            except (tk .TclError ,TypeError ,ValueError ):
                brew_hwnd =0 
        try :
            if sys .platform =="win32"and brew_hwnd >0 :
                det .bring_to_foreground_for_capture ()
                time .sleep (0.05 )
            rect =det .get_client_rect_mss_aligned ()
            if not rect :
                messagebox .showerror ("Guided config","No client rectangle.",parent =w )
                return 
            results ,cap_ok ,_piece =run_get_objects_pipeline (
            rect ,
            shapes_json =path ,
            log =self ._game_error_log ,
            verbose_logs =False ,
            )
        except Exception as e :
            messagebox .showerror ("Guided config",f"Potion Failed Continue sample failed: {e}",parent =w )
            return 
        finally :
            if sys .platform =="win32"and brew_hwnd >0 :
                try :
                    win32_set_foreground_window (brew_hwnd )
                except Exception :
                    pass 
        if not cap_ok or not isinstance (results ,list ):
            messagebox .showerror ("Guided config","Potion Failed Continue capture failed.",parent =w )
            return 
        pfc =next ((r for r in results if str (r .get ("label",""))=="potion_failed_continue"),None )
        if not isinstance (pfc ,dict ):
            messagebox .showerror (
            "Guided config",
            "No `potion_failed_continue` location found in object_shapes.json.",
            parent =w ,
            )
            return 
        rgb =self ._sample_result_box_median_rgb (frame_bgra ,pfc )
        if rgb is None :
            messagebox .showerror (
            "Guided config",
            "Could not sample Potion Failed Continue RGB from the captured box.",
            parent =w ,
            )
            return 
        pfcr .set (str (int (rgb [0 ])))
        pfcg .set (str (int (rgb [1 ])))
        pfcb .set (str (int (rgb [2 ])))
        _fail_preview ()

    btn_fail_cap .config (command =do_fail_capture )

    cols =tk .Frame (inner ,bg ="#2a2a2e")
    cols .pack (fill =tk .BOTH ,expand =True )

    row_registry :dict [tuple [str ,str ],dict [str ,Any ]]={}
    row_status_labels :dict [tuple [str ,str ],tk .Label ]={}

    def add_column (
    parent :tk .Frame ,
    title :str ,
    sections :tuple [tuple [str ,str ,tuple [str ,...]],...],
    )->None :
        lf =tk .LabelFrame (parent ,text =title ,font =wiz_meta ,padx =6 ,pady =6 )
        lf .pack (side =tk .LEFT ,fill =tk .BOTH ,expand =True ,padx =(0 ,6 ))
        for section_label ,storage_slot ,poly_cands in sections :
            tk .Label (lf ,text =section_label ,font =wiz_meta ).pack (anchor =tk .W ,pady =(4 ,2 ))
            for c in gv._GUIDED_GRID_COLORS :
                ch =color_human .get (c ,c )
                row_key =(storage_slot ,c )
                fr =tk .Frame (lf )
                fr .pack (fill =tk .X ,pady =1 )
                tk .Label (fr ,text =f"  {ch} ({c})",font =wiz_meta ,width =18 ,anchor =tk .W ).pack (
                side =tk .LEFT 
                )
                btn_cap =tk .Button (fr ,text ="Capture",font =wiz_meta )
                btn_cap .pack (side =tk .LEFT ,padx =(0 ,4 ))
                vr =tk .StringVar (value ="0")
                vg2 =tk .StringVar (value ="0")
                vb2 =tk .StringVar (value ="0")
                slot_d =self ._brew_ring_median_grid .get (storage_slot ,{})
                pr0 =slot_d .get (c )
                if isinstance (pr0 ,tuple )and len (pr0 )==3 :
                    vr .set (str (int (pr0 [0 ])))
                    vg2 .set (str (int (pr0 [1 ])))
                    vb2 .set (str (int (pr0 [2 ])))
                elif storage_slot in ("current_piece_left","current_piece_right"):
                    p_disp =self ._brew_piece_display_rgb .get (c )
                    if isinstance (p_disp ,tuple )and len (p_disp )==3 :
                        vr .set (str (int (p_disp [0 ])))
                        vg2 .set (str (int (p_disp [1 ])))
                        vb2 .set (str (int (p_disp [2 ])))
                tk .Label (fr ,text ="R",font =wiz_meta ).pack (side =tk .LEFT )
                er =tk .Entry (fr ,textvariable =vr ,width =4 ,font =wiz_meta )
                er .pack (side =tk .LEFT ,padx =1 )
                tk .Label (fr ,text ="G",font =wiz_meta ).pack (side =tk .LEFT )
                eg =tk .Entry (fr ,textvariable =vg2 ,width =4 ,font =wiz_meta )
                eg .pack (side =tk .LEFT ,padx =1 )
                tk .Label (fr ,text ="B",font =wiz_meta ).pack (side =tk .LEFT )
                eb =tk .Entry (fr ,textvariable =vb2 ,width =4 ,font =wiz_meta )
                eb .pack (side =tk .LEFT ,padx =1 )
                st_lbl =tk .Label (
                fr ,
                text ="",
                font =wiz_meta ,
                width =9 ,
                anchor =tk .W ,
                fg ="#9a9a9a",
                bg ="#2a2a2e",
                )
                st_lbl .pack (side =tk .LEFT ,padx =(6 ,0 ))
                row_status_labels [row_key ]=st_lbl 
                row_registry [row_key ]={
                "sk":storage_slot ,
                "ct":c ,
                "vr":vr ,
                "vg":vg2 ,
                "vb":vb2 ,
                }
                pcv =tk .Canvas (
                fr ,
                width =38 ,
                height =38 ,
                highlightthickness =1 ,
                highlightbackground ="#555555",
                bg ="#2a2a2e",
                )
                pcv .pack (side =tk .LEFT ,padx =(8 ,0 ))

                def _piece_preview (*_x :Any ,_cv :tk .Canvas =pcv ,_vr :tk .StringVar =vr ,_vg :tk .StringVar =vg2 ,_vb :tk .StringVar =vb2 )->None :
                    t2 =_parse_rgb_vars (_vr ,_vg ,_vb )
                    if t2 is None :
                        return 
                    _paint_cv (_cv ,t2 [0 ],t2 [1 ],t2 [2 ])

                vr .trace_add ("write",lambda *_a ,f =_piece_preview :f ())
                vg2 .trace_add ("write",lambda *_a ,f =_piece_preview :f ())
                vb2 .trace_add ("write",lambda *_a ,f =_piece_preview :f ())
                ip =_parse_rgb_vars (vr ,vg2 ,vb2 )
                if ip :
                    _paint_cv (pcv ,ip [0 ],ip [1 ],ip [2 ])
                else :
                    _paint_cv (pcv ,0 ,0 ,0 )

                def do_cap (
                _sk :str =storage_slot ,
                _pc :tuple [str ,...]=poly_cands ,
                _ct :str =c ,
                _vr :tk .StringVar =vr ,
                _vg :tk .StringVar =vg2 ,
                _vb :tk .StringVar =vb2 ,
                _rk :tuple [str ,str ]=row_key ,
                _sl :tk .Label =st_lbl ,
                )->None :
                    try :
                        from brew_core.next_pieces import (
                        resolve_first_polygon_label ,
                        sample_piece_ring_at_label ,
                        )
                    except ImportError as e :
                        messagebox .showerror ("Guided config",str (e ),parent =w )
                        return 
                    got =grab_capture_bundle ()
                    if got is None :
                        return 
                    frame_bgra ,path =got 
                    poly =resolve_first_polygon_label (path ,_pc )
                    if not poly :
                        messagebox .showerror (
                        "Guided config",
                        f"No polygon for labels {list(_pc)} in object_shapes.json.",
                        parent =w ,
                        )
                        return 
                    stats =sample_piece_ring_at_label (frame_bgra ,path ,poly )
                    if not stats .get ("ok"):
                        messagebox .showerror (
                        "Guided config",
                        str (stats .get ("error","Ring sample failed.")),
                        parent =w ,
                        )
                        return 
                    row_state [_rk ]={"captured":True ,"stats":stats }
                    rm =int (stats ["r_med"])
                    gm =int (stats ["g_med"])
                    bm =int (stats ["b_med"])
                    _vr .set (str (rm ))
                    _vg .set (str (gm ))
                    _vb .set (str (bm ))
                    try :
                        _sl .config (text ="Pending",fg ="#e8a84a")
                    except tk .TclError :
                        pass 

                btn_cap .config (command =do_cap )

    add_column (cols ,"Next pair (queue)",gv._GUIDED_GRID_NEXT_ROWS )
    add_column (cols ,"Current pair (in play)",gv._GUIDED_GRID_CURRENT_ROWS )

    def do_save_all ()->None :
        tb =_parse_rgb_vars (br ,bg_ ,bb )
        if tb is None :
            messagebox .showerror ("Guided config","Empty board: enter valid R,G,B (0–255).",parent =w )
            return 
        ta =_parse_rgb_vars (abr ,abg ,abb )
        if ta is None :
            messagebox .showerror ("Guided config","Brew Again: enter valid R,G,B (0–255).",parent =w )
            return 
        ta_ok =_parse_rgb_vars (aokr ,aokg ,aokb )
        if ta_ok is None :
            messagebox .showerror ("Guided config","Brew Again OK: enter valid R,G,B (0–255).",parent =w )
            return 
        tpfc =_parse_rgb_vars (pfcr ,pfcg ,pfcb )
        if tpfc is None :
            messagebox .showerror ("Guided config","Potion Failed Continue: enter valid R,G,B (0–255).",parent =w )
            return 
        pending :list [tuple [tuple [str ,str ],dict [str ,Any ]]]=[]
        for rk ,meta in row_registry .items ():
            st =row_state .get (rk )
            if not st or not st .get ("captured"):
                continue 
            t2 =_parse_rgb_vars (meta ["vr"],meta ["vg"],meta ["vb"])
            if t2 is None :
                messagebox .showerror (
                "Guided config",
                f"Invalid R,G,B for {meta['sk']} / {meta['ct']}.",
                parent =w ,
                )
                return 
            ct =str (meta ["ct"])
            if ct not in gv._CONFIG_PIECE_DISPLAY_ORDER :
                messagebox .showerror ("Guided config",f"Unknown color token `{ct}`.",parent =w )
                return 
            pending .append ((rk ,meta ))
        self ._brew_board_await_r ,self ._brew_board_await_g ,self ._brew_board_await_b =tb 
        self ._brew_again_r ,self ._brew_again_g ,self ._brew_again_b =ta 
        self ._brew_again_ok_r ,self ._brew_again_ok_g ,self ._brew_again_ok_b =ta_ok 
        self ._potion_failed_continue_r ,self ._potion_failed_continue_g ,self ._potion_failed_continue_b =tpfc 
        self ._sync_board_bgr_vars_from_state ()
        if pending :
            for rk ,meta in pending :
                ct =str (meta ["ct"])
                sk =str (meta ["sk"])
                tup =_parse_rgb_vars (meta ["vr"],meta ["vg"],meta ["vb"])
                assert tup is not None 
                r2 ,g2 ,b2 =tup 
                slot_grid =self ._brew_ring_median_grid .setdefault (sk ,{})
                slot_grid [ct ]=(r2 ,g2 ,b2 )
                if sk in ("current_piece_left","current_piece_right"):
                    self ._brew_piece_display_rgb [ct ]=(r2 ,g2 ,b2 )
        for rk ,_meta in pending :
            row_state .pop (rk ,None )
            sl =row_status_labels .get (rk )
            if sl is not None :
                try :
                    sl .config (text ="Saved",fg ="#7cba6e")
                except tk .TclError :
                    pass 
        self ._sync_piece_cfg_rgb_vars_from_state ()
        self ._save_brew_gui_settings ()
        self ._refresh_game_action_button_labels ()
        self ._brew_automation_hotkey_sync ()
        if self ._game_config_visible :
            self ._draw_game_config_layer ()

    btn_fr =tk .Frame (outer )
    btn_fr .pack (fill =tk .X ,pady =(8 ,0 ))
    btn_save_all =tk .Button (
    btn_fr ,
    text ="Save all",
    font =wiz_meta ,
    command =do_save_all ,
    )
    btn_save_all .pack (side =tk .LEFT )
    btn_close =tk .Button (btn_fr ,text ="Close",font =wiz_meta )

    def on_close ()->None :
        self ._guided_wizard_top =None 
        try :
            w .destroy ()
        except tk .TclError :
            pass 

    btn_close .config (command =on_close )
    btn_close .pack (side =tk .RIGHT )
    _bind_wheel_recursive (w )
    w .protocol ("WM_DELETE_WINDOW",on_close )

