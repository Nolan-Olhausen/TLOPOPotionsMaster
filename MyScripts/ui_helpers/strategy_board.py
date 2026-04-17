from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Any

import brew_core.board_memory as brew_board_memory
import variables.global_variables as gv
from core_helpers import brew_strategy_choices

def _brew_strategy_wrap_two_lines (self ,text :str ,max_width_px :int ,font_tuple :tuple [Any ,...])->str :
    """Word-wrap to at most two lines (one ``\\n``); ellipsis only if still too wide on line 2."""
    if not text or max_width_px <=8 :
        return text
    try :
        font =tkfont .Font (self .root ,font =font_tuple )
    except tk .TclError :
        return text
    ell ="…"
    if font .measure (text )<=max_width_px :
        return text

    words =text .split ()
    if not words :
        return text

    if len (words )==1 :
        w =words [0 ]
        lo =0 
        for k in range (1 ,len (w )+1 ):
            if font .measure (w [:k ])<=max_width_px :
                lo =k 
            else :
                break
        if lo ==0 :
            lo =1 
        first =w [:lo ]
        second =w [lo :]
        if not second :
            return first
        if font .measure (second )<=max_width_px :
            return first +"\n"+second 
        s2 =second 
        while s2 and font .measure (s2 +ell )>max_width_px :
            s2 =s2 [:-1 ]
        return first +"\n"+(s2 +ell if s2 else ell )

    line1 :list [str ]=[]
    i =0 
    while i <len (words ):
        trial =" ".join (line1 +[words [i ]])if line1 else words [i ]
        if font .measure (trial )<=max_width_px :
            line1 .append (words [i ])
            i +=1 
        else :
            break
    if not line1 :
        line1 =[words [0 ]]
        i =1 
    rest =words [i :]
    if not rest :
        return " ".join (line1 )
    line2 =" ".join (rest )
    if font .measure (line2 )<=max_width_px :
        return " ".join (line1 )+"\n"+line2 
    s2 =line2 
    while s2 and font .measure (s2 +ell )>max_width_px :
        if " "in s2 :
            s2 =s2 .rsplit (" ",1 )[0 ]
        else :
            s2 =s2 [:-1 ]
    return " ".join (line1 )+"\n"+(s2 +ell if s2 else ell )


def _apply_brew_strategy_choice (self ,choice :str )->None :
    self ._brew_strategy_choice =choice 
    if self ._game_strategy_text_lbl is None or not self ._game_strategy_text_lbl .winfo_exists ():
        return
    row =self ._game_strategy_row 
    edge =120 
    if row is not None and row .winfo_exists ()and row .winfo_width ()>8 :
        edge =max (48 ,row .winfo_width ()-28 )
    self ._game_strategy_text_lbl .configure (
    text =self ._brew_strategy_wrap_two_lines (self ._brew_strategy_choice ,edge ,self ._font_strategy_choice ),
    justify =tk .LEFT ,
    )
    m =self ._game_strategy_menu 
    if m is not None :
        try :
            m .unpost ()
        except tk .TclError :
            pass 
    if self ._view =="game":
        self ._draw_hex_grid_layer ()
        self ._raise_overlay_tags ()


def _brew_reset_board_memory (self )->None :
    """Fresh simulator for a new game view (same idea as oldBot starting a round)."""
    self ._board_memory_photo_refs .clear ()
    self ._brew_board_ingredient_done =[]
    if not brew_board_memory .board_memory_available ():
        self ._brew_board_sim =None 
        self ._brew_board_memory =None 
        return
    self ._brew_board_sim =brew_board_memory .BoardSim ()
    self ._brew_board_memory =brew_board_memory .BoardMemory ()
    if self .potions :
        p =self .potions [max (0 ,min (self ._current_potion_index ,len (self .potions )-1 ))]
        ings =p .get ("ingredients")if isinstance (p ,dict )else None 
        if isinstance (ings ,list ):
            self ._brew_board_ingredient_done =[False ]*len (ings )


def _ingredient_for_board_line_color (self ,potion :dict ,line_color :str )->dict |None :
    """First recipe ingredient whose catalog color matches a BoardSim gem color."""
    ln =str (line_color or "").strip ().lower ()
    if not ln :
        return None
    for ing in potion .get ("ingredients")or []:
        if not isinstance (ing ,dict ):
            continue
        c =str (ing .get ("color")or "").strip ().lower ()
        if not c :
            continue
        if c ==ln :
            return ing
        if ln =="grey"and c in ("grey","gray","black"):
            return ing
    return None


def _brew_board_memory_apply_automation_drop (
self ,
*,
slot :int ,
auto_swap :bool ,
vl :str ,
vr :str ,
cl :str ,
cr :str ,
)->None :
    """After a successful automated drop, mirror it on the internal BoardSim and redraw."""
    if not brew_board_memory .board_memory_available ()or self ._brew_board_sim is None :
        return
    if not self .potions :
        return
    # Keep true multi-island colors (O/P/Grey) in board memory; do not collapse to Port Royal RGB.
    pair =brew_board_memory .drop_colors_for_place_pair (vl ,vr ,auto_swap =auto_swap )
    if pair is None :
        return
    a ,b =pair 
    col0 =int (slot )-1 
    if col0 <0 or col0 >=brew_board_memory .COLS -1 :
        return
    if not self ._brew_board_sim .can_place_pair (col0 ,a ,b ):
        self ._append_game_log (
            "[Board memory] Sim rejected a drop (board may be full or out of sync). "
            "Re-open this recipe to reset the overlay."
        )
        return
    potion =self .potions [max (0 ,min (self ._current_potion_index ,len (self .potions )-1 ))]
    ings =potion .get ("ingredients")if isinstance (potion ,dict )else None 
    if isinstance (ings ,list ):
        if len (self ._brew_board_ingredient_done )!=len (ings ):
            self ._brew_board_ingredient_done =[False ]*len (ings )
    else :
        self ._brew_board_ingredient_done =[]
    self ._brew_board_sim .place_pair_and_resolve (col0 ,a ,b )
    if self ._brew_board_ingredient_done :
        try :
            n_cons =brew_board_memory .settle_merges_and_recipe_from_catalog (
            self ._brew_board_sim ,potion ,self ._brew_board_ingredient_done 
            )
            if n_cons >0 :
                done_n =sum (1 for x in self ._brew_board_ingredient_done if x )
                self ._append_game_log (
                    f"[Board memory] recipe cleared {n_cons} gem(s) ({done_n}/{len(self._brew_board_ingredient_done)})."
                )
        except Exception :
            pass 
    if self ._brew_board_memory is not None :
        self ._brew_board_memory .record (col0 ,str (cl ),str (cr ),bool (auto_swap ),"exact")
    if self ._view =="game":
        self ._draw_hex_grid_layer ()
        self ._raise_overlay_tags ()


def _rebuild_brew_strategy_menu (self ,opts :tuple [str ,str ])->None :
    m =self ._game_strategy_menu 
    if m is None or not m .winfo_exists ():
        return
    m .delete (0 ,tk .END )
    wrap_px =max (40 ,int (getattr (self ,"_brew_strategy_menu_wrap_px",280 )))
    for opt in opts :
        label =self ._brew_strategy_wrap_two_lines (opt ,wrap_px ,self ._font_strategy_menu )
        m .add_command (label =label ,command =lambda o =opt :self ._apply_brew_strategy_choice (o ))


def _destroy_game_strategy_embed (self )->None :
    self ._game_strategy_text_lbl =None 
    self ._game_strategy_row =None 
    if self ._game_strategy_menu is not None :
        try :
            try :
                self ._game_strategy_menu .unpost ()
            except tk .TclError :
                pass 
            self ._game_strategy_menu .destroy ()
        except tk .TclError :
            pass 
        self ._game_strategy_menu =None 
    if self ._game_strategy_shell is not None :
        try :
            self ._game_strategy_shell .destroy ()
        except tk .TclError :
            pass 
        self ._game_strategy_shell =None 


def _draw_game_strategy_embed (self ,x :int ,y :int ,rw :int ,rh :int )->None :
    self ._destroy_game_strategy_embed ()
    if self ._view !="game"or not self .potions or rw <48 or rh <28 :
        return
    p =self .potions [max (0 ,min (self ._current_potion_index ,len (self .potions )-1 ))]
    board ,specific =brew_strategy_choices (p )
    opts =(board ,specific )
    if not self ._brew_strategy_choice or self ._brew_strategy_choice not in opts :
        self ._brew_strategy_choice =board 

    btn_fill =gv .BREW_SIMPLE_UI_PANEL_BG if getattr (self ,"_brew_simple_ui",False )else gv .GAME_UI_BUTTON_FILL 
    btn_outline =gv .BREW_SIMPLE_UI_MUTED if getattr (self ,"_brew_simple_ui",False )else gv .GAME_UI_BUTTON_OUTLINE 
    btn_text =gv .BREW_SIMPLE_UI_TEXT if getattr (self ,"_brew_simple_ui",False )else gv .GAME_UI_BUTTON_TEXT 
    shell =tk .Frame (
    self .bg_canvas ,
    bg =btn_fill ,
    highlightthickness =2 ,
    highlightbackground =btn_outline ,
    )
    tk .Label (
    shell ,
    text =gv.GAME_STRATEGY_TITLE ,
    bg =btn_fill ,
    fg =btn_text ,
    font =self ._font_meta ,
    ).pack (side =tk .TOP ,anchor ="w",padx =6 ,pady =(2 ,0 )if rh <40 else (4 ,0 ))

    # ttk.Combobox still paints a light native field on Windows — use plain tk + Menu instead.
    self ._brew_strategy_menu_wrap_px =max (200 ,min (480 ,rw +140 ))
    row =tk .Frame (
    shell ,
    bg =btn_fill ,
    highlightthickness =0 ,
    cursor ="hand2",
    )
    row .pack (fill =tk .BOTH ,expand =True ,padx =4 ,pady =(1 ,2 )if rh <40 else (2 ,4 ))
    edge =max (48 ,rw -52 )
    text_lbl =tk .Label (
    row ,
    text =self ._brew_strategy_wrap_two_lines (
    self ._brew_strategy_choice ,edge ,self ._font_strategy_choice 
    ),
    anchor ="nw",
    justify =tk .LEFT ,
    bg =btn_fill ,
    fg =btn_text ,
    font =self ._font_strategy_choice ,
    cursor ="hand2",
    )
    text_lbl .pack (side =tk .LEFT ,fill =tk .BOTH ,expand =True ,padx =(4 ,0 ))
    arrow_lbl =tk .Label (
    row ,
    text ="\u25be",
    anchor ="center",
    bg =btn_fill ,
    fg =btn_outline ,
    font =(self ._font_ui_family ,12 ),
    width =2 ,
    cursor ="hand2",
    )
    arrow_lbl .pack (side =tk .RIGHT ,padx =(0 ,2 ))

    menu =tk .Menu (
    self .root ,
    tearoff =0 ,
    bg =btn_fill ,
    fg =btn_text ,
    activebackground =btn_outline ,
    activeforeground =btn_text ,
    activeborderwidth =0 ,
    bd =0 ,
    relief =tk .FLAT ,
    font =self ._font_strategy_menu ,
    )
    self ._game_strategy_menu =menu 
    self ._rebuild_brew_strategy_menu (opts )

    def post_menu (_event :tk .Event |None =None )->None :
        if self ._game_strategy_menu is None or self ._game_strategy_row is None :
            return
        try :
            rx =int (self ._game_strategy_row .winfo_rootx ())
            ry =int (self ._game_strategy_row .winfo_rooty ()+self ._game_strategy_row .winfo_height ())
            self ._game_strategy_menu .post (rx ,ry )
        except tk .TclError :
            pass 

    def on_row_configure (_event :tk .Event |None =None )->None :
        if self ._game_strategy_text_lbl is None or not self ._game_strategy_text_lbl .winfo_exists ():
            return
        if self ._game_strategy_row is None or not self ._game_strategy_row .winfo_exists ():
            return
        wpx =max (48 ,self ._game_strategy_row .winfo_width ()-28 )
        self ._brew_strategy_menu_wrap_px =max (200 ,min (480 ,self ._game_strategy_row .winfo_width ()+160 ))
        self ._game_strategy_text_lbl .configure (
        text =self ._brew_strategy_wrap_two_lines (self ._brew_strategy_choice ,wpx ,self ._font_strategy_choice ),
        justify =tk .LEFT ,
        )

    row .bind ("<Button-1>",post_menu )
    text_lbl .bind ("<Button-1>",post_menu )
    arrow_lbl .bind ("<Button-1>",post_menu )
    row .bind ("<Configure>",on_row_configure )

    self .bg_canvas .create_window (
    x ,
    y ,
    window =shell ,
    anchor ="nw",
    width =rw ,
    height =rh ,
    tags =("game_ui","game_strategy_layer"),
    )
    self ._game_strategy_shell =shell 
    self ._game_strategy_row =row 
    self ._game_strategy_text_lbl =text_lbl 


def _refresh_brew_strategy_dropdown (self )->None :
    if self ._view !="game"or not self .potions :
        return
    if self ._game_strategy_text_lbl is None or not self ._game_strategy_text_lbl .winfo_exists ():
        return
    p =self .potions [max (0 ,min (self ._current_potion_index ,len (self .potions )-1 ))]
    board ,specific =brew_strategy_choices (p )
    opts =(board ,specific )
    cur =self ._brew_strategy_choice 
    if cur not in opts :
        cur =board 
        self ._brew_strategy_choice =cur 
    row =self ._game_strategy_row 
    edge =max (48 ,row .winfo_width ()-28 )if row is not None and row .winfo_exists ()else 120 
    if row is not None and row .winfo_exists ():
        self ._brew_strategy_menu_wrap_px =max (200 ,min (480 ,row .winfo_width ()+160 ))
    self ._game_strategy_text_lbl .configure (
    text =self ._brew_strategy_wrap_two_lines (self ._brew_strategy_choice ,edge ,self ._font_strategy_choice ),
    justify =tk .LEFT ,
    )
    self ._rebuild_brew_strategy_menu (opts )
    self ._draw_hex_grid_layer ()
    self ._raise_overlay_tags ()


