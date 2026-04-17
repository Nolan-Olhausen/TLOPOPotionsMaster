from __future__ import annotations

import sys
import time
import tkinter as tk
from tkinter import messagebox
from typing import Any

import variables.global_variables as gv
from core_helpers import _tlopo_format_get_locations_report

def _sample_result_box_median_rgb (
frame_bgra :Any ,result :dict [str ,Any ],*,inset_frac :float =0.18 
)->tuple [int ,int ,int ]|None :
    if frame_bgra is None or not isinstance (result ,dict ):
        return None 
    x0 =result .get ("x0")
    y0 =result .get ("y0")
    x1 =result .get ("x1")
    y1 =result .get ("y1")
    if not all (isinstance (v ,(int ,float ))for v in (x0 ,y0 ,x1 ,y1 )):
        return None 
    try :
        import numpy as np 
    except ImportError :
        return None 
    h =int (frame_bgra .shape [0 ])
    w =int (frame_bgra .shape [1 ])
    l =max (0 ,min (w -1 ,int (round (min (float (x0 ),float (x1 ))))))
    r =max (0 ,min (w ,int (round (max (float (x0 ),float (x1 ))))))
    t =max (0 ,min (h -1 ,int (round (min (float (y0 ),float (y1 ))))))
    b =max (0 ,min (h ,int (round (max (float (y0 ),float (y1 ))))))
    if r -l <4 or b -t <4 :
        return None 
    ix =int ((r -l )*max (0.0 ,min (0.45 ,inset_frac )))
    iy =int ((b -t )*max (0.0 ,min (0.45 ,inset_frac )))
    l2 ,r2 =l +ix ,r -ix 
    t2 ,b2 =t +iy ,b -iy 
    if r2 -l2 <2 or b2 -t2 <2 :
        l2 ,r2 ,t2 ,b2 =l ,r ,t ,b 
    roi =frame_bgra [t2 :b2 ,l2 :r2 ]
    if roi .size ==0 :
        return None 
    b_med =int (np .median (roi [:,:,0 ]))
    g_med =int (np .median (roi [:,:,1 ]))
    r_med =int (np .median (roi [:,:,2 ]))
    return (r_med ,g_med ,b_med )


def _tlopo_client_rect_for_overlay (self ):
    try :
        from tlopo_client.window import TlopoGameWindow 
    except ImportError :
        return None 
    det =TlopoGameWindow (log =lambda _m :None )
    if not det .find_window ()or not det .is_valid ():
        return None 
    return det .get_client_rect_mss_aligned ()


def _on_shape_overlay_clicked (self )->None :
    if not self ._game_prereq_window_ok or not self ._game_prereq_objects_ok :
        messagebox .showwarning (
        "Shape overlay",
        "Run Get window and Get locations first (both must succeed), then try again.",
        parent =self .root ,
        )
        return 
    try :
        from brew_core.tlopo_overlay import BrewTlopoShapeOverlay 
    except ImportError as e :
        messagebox .showerror (
        "Shape overlay",
        f"Could not load overlay module:\n{e}",
        parent =self .root ,
        )
        return 
    if self ._game_tlopo_overlay is None :
        self ._game_tlopo_overlay =BrewTlopoShapeOverlay (
        self .root ,
        self ._tlopo_client_rect_for_overlay ,
        font_family =self ._font_ui_family ,
        )
    was_on =self ._game_tlopo_overlay .active 
    now_on =self ._game_tlopo_overlay .toggle ()
    self ._refresh_overlay_toggle_label ()
    if not was_on and not now_on :
        messagebox .showwarning (
        "Shape overlay",
        "Could not read the TLOPO client area. Make sure the game window is still open, then try again.",
        parent =self .root ,
        )


def _refresh_overlay_toggle_label(self) -> None:
    ids = self.bg_canvas.find_withtag("overlay_toggle_label")
    if ids:
        on = self._game_tlopo_overlay is not None and self._game_tlopo_overlay.active
        self.bg_canvas.itemconfigure(ids[0], text="Hide overlay" if on else "Object overlay")


def _stop_tlopo_shape_overlay(self) -> None:
    if self._game_tlopo_overlay is not None:
        self._game_tlopo_overlay.stop()
        self._game_tlopo_overlay = None
    self._refresh_overlay_toggle_label()


def _game_error_log (self ,level :str ,message :str )->None :
    """Plain errors into the game log (used by Get window / Get locations when ``verbose_logs`` is off)."""
    if level =="ERROR":
        self ._append_game_log (f"Error: {message}")


def _on_get_window_clicked (self )->None :
    """Find and validate the TLOPO client window (no ROI capture)."""
    self ._game_prereq_window_ok =False 
    self ._game_prereq_objects_ok =False 
    self ._game_get_window_caption =gv.GAME_CAPTION_WINDOW_IDLE 
    self ._game_get_objects_caption =gv.GAME_CAPTION_OBJECTS_IDLE 
    self ._refresh_game_action_button_labels ()

    try :
        from tlopo_client.window import (
        TlopoGameWindow ,
        format_window_info_text ,
        )
    except ImportError as e :
        self ._game_get_window_caption =gv.GAME_CAPTION_WINDOW_ERR 
        self ._refresh_game_action_button_labels ()
        self ._append_game_log (f"[Get Window] could not load helper: {e}")
        messagebox .showerror (
        "Get window",
        f"Could not load window helper:\n{e}",
        parent =self .root ,
        )
    else :
        det =TlopoGameWindow (log =lambda _m :None )
        if det .find_window ()and det .is_valid ():
            info =det .get_window_info ()
            body =format_window_info_text (info )if info else det .get_window_title ()or "(no details)"
            self ._append_game_log ("[Get Window] success")
            self ._append_game_log (body )
            self ._game_prereq_window_ok =True 
            self ._game_get_window_caption =gv.GAME_CAPTION_WINDOW_OK 
        else :
            self ._append_game_log (
            "[Get Window] No TLOPO window found. Look for the real client titled like "
            '"The Legend of Pirates Online [BETA]" (not this app). Leave it visible, then try again.'
            )
            self ._append_game_log ("Install: pip install -r requirements-tlopo-window.txt")
            self ._game_prereq_window_ok =False 
            self ._game_get_window_caption =gv.GAME_CAPTION_WINDOW_ERR 

        self ._append_game_log ("")
        self ._refresh_game_action_button_labels ()
    finally :
        self ._brew_automation_hotkey_sync ()


def _on_get_objects_clicked (self )->None :
    """Capture the client ROI and list labeled shape centers (locations only — no piece color pass)."""
    if not self ._game_prereq_window_ok :
        messagebox .showwarning (
        "Get locations",
        "Run Get Window successfully first, then capture locations.",
        parent =self .root ,
        )
        return 
    self ._game_prereq_objects_ok =False 
    self ._game_get_objects_caption =gv.GAME_CAPTION_OBJECTS_IDLE 
    self ._refresh_game_action_button_labels ()

    try :
        try :
            from brew_core.object_recognition import run_object_recognition_roi_only 
            from tlopo_client.window import TlopoGameWindow ,win32_set_foreground_window 
        except ImportError as e :
            self ._game_get_objects_caption =gv.GAME_CAPTION_OBJECTS_ERR 
            self ._refresh_game_action_button_labels ()
            self ._append_game_log (f"[Get Locations] import failed: {e}")
            self ._append_game_log ("Install: pip install -r requirements-tlopo-window.txt")
            messagebox .showerror (
            "Get locations",
            f"Could not load recognition module:\n{e}\n\n"
            "Install: pip install -r requirements-tlopo-window.txt",
            parent =self .root ,
            )
            return 

        det_objs =TlopoGameWindow (log =lambda _m :None )
        if not det_objs .find_window ()or not det_objs .is_valid ():
            self ._append_game_log (
            "[Get Locations] No TLOPO game window found. Leave the client titled like "
            '"The Legend of Pirates Online [BETA]" visible (not minimized), then try again.'
            )
            self ._game_prereq_window_ok =False 
            self ._game_get_window_caption =gv.GAME_CAPTION_WINDOW_ERR 
            self ._game_get_objects_caption =gv.GAME_CAPTION_OBJECTS_ERR 
            self ._refresh_game_action_button_labels ()
            return 

        self ._game_prereq_window_ok =True 
        self ._game_get_window_caption =gv.GAME_CAPTION_WINDOW_OK 
        self ._refresh_game_action_button_labels ()

        brew_hwnd =0 
        if sys .platform =="win32":
            try :
                brew_hwnd =int (self .root .winfo_id ())
            except (tk .TclError ,TypeError ,ValueError ):
                brew_hwnd =0 

        if sys .platform =="win32"and brew_hwnd >0 :
            if det_objs .bring_to_foreground_for_capture ():
                self ._append_game_log (
                "[Get Locations] TLOPO brought to foreground for capture (then Brewing is restored)."
                )
                time .sleep (0.06 )
            else :
                self ._append_game_log (
                "[Get Locations] Could not foreground TLOPO; capture may not match the live client."
                )

        try :
            rect =det_objs .get_client_rect_mss_aligned ()
            if not rect :
                self ._append_game_log ("[Get Locations] Could not read the game client rectangle.")
                self ._game_prereq_objects_ok =False 
                self ._game_get_objects_caption =gv.GAME_CAPTION_OBJECTS_ERR 
                self ._refresh_game_action_button_labels ()
                return 

            results ,roi_ok =run_object_recognition_roi_only (
            rect ,
            log =self ._game_error_log ,
            verbose_logs =False ,
            )
            if not roi_ok or not results :
                self ._append_game_log (
                "[Get Locations] ROI capture or metrics failed (no shape results)."
                )
                self ._game_prereq_objects_ok =False 
                self ._game_get_objects_caption =gv.GAME_CAPTION_OBJECTS_ERR 
                self ._refresh_game_action_button_labels ()
                return 

            self ._game_prereq_objects_ok =True 
            self ._game_get_objects_caption =gv.GAME_CAPTION_OBJECTS_OK 
            self ._append_game_log (
            _tlopo_format_get_locations_report (
            results ,
            None ,
            include_piece_color_block =False ,
            )
            )
            self ._append_game_log ("")
        except Exception as e :
            self ._append_game_log (f"Error: Get Locations failed: {e}")
            self ._game_prereq_objects_ok =False 
            self ._game_get_objects_caption =gv.GAME_CAPTION_OBJECTS_ERR 
        finally :
            if sys .platform =="win32"and brew_hwnd >0 :
                try :
                    win32_set_foreground_window (brew_hwnd )
                except Exception :
                    pass 

        self ._refresh_game_action_button_labels ()
    finally :
        self ._brew_automation_hotkey_sync ()


