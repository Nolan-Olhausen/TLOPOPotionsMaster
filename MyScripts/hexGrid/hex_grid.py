from __future__ import annotations

import math
from dataclasses import dataclass, field

import variables.global_variables as gv

@dataclass
class BrewBoardHexGrid :
    """
    Single place to tune the brew-board hex overlay (game view only).

    All layout uses this instance — adjust fields until the grid matches your art.

    Tessellation (true honeycomb — see redblobgames hex grids):
      - ``flat_top`` (default): flat-top hexes (horizontal flats). Stagger:
          * ``odd_columns`` / ``even_columns`` — columns alternate up/down (odd-q offset
            into flat-top pixel space); matches a typical carved board.
          * ``odd_rows`` / ``even_rows`` — rows alternate left/right (odd-r offset).
      - ``pointy_top``: vertex-up hexes. Stagger ``odd_columns`` / ``even_columns``.

    ``rotation_degrees``: rigid rotation of the whole grid (centers + outlines) around the
    board-rectangle center after layout — use to align the honeycomb with the artwork.

    ``column_spacing_mul`` / ``row_spacing_mul``: horizontal / vertical pitch of the lattice
    and outlines (1.0 = tight honeycomb). Increase to widen or lengthen cells.

    ``cell_polygon_phase_degrees``: None = auto (+30° for ``flat_top``, 0 for ``pointy_top``).
    """

    columns :int =8 
    rows :int =10 

    # Shrink the usable rectangle inside GAME_ART_BBOX (fraction of width/height per side, 0–0.25).
    inset_fraction_x :float =0.0 
    inset_fraction_y :float =0.0 

    tessellation :str ="flat_top"
    stagger :str ="odd_columns"

    # Extra rotation of the hex outline only (degrees). None = auto (+30 for flat_top, 0 for pointy_top).
    cell_polygon_phase_degrees :float |None =None 

    # Horizontal / vertical pitch vs circumradius R (1 = tight honeycomb). Applied to layout and outlines.
    column_spacing_mul :float =1 
    row_spacing_mul :float =1 

    # Nudge every cell center (pixels, before rotation).
    cell_offset_x_px :float =0.0 
    cell_offset_y_px :float =0.0 

    # Extra Y per row index 0..rows-1 (pixels). Shorter tuples pad with 0; longer are truncated.
    row_offset_y_px :tuple [float ,...]=field (default_factory =tuple )

    # Whole grid: rigid rotation in degrees around the board-rectangle center (after layout + scale).
    rotation_degrees :float =0.0 

    # Uniform scale after max-fit (1.0 = as large as fits; smaller shrinks entire tessellation).
    global_scale :float =1.05 

    # Safety margin on binary-search fit (slightly <1 shrinks so hexes don’t kiss the bbox edge).
    fit_shrink :float =0.98 

    # Outline hex: circumradius minus this (pixels). Use 0 for edge-to-edge stroke; >0 gaps lines slightly.
    outline_radius_inset :float =0.0 
    outline_width :int =1 

BREW_BOARD_HEX_GRID =BrewBoardHexGrid ()

def compute_hex_cell_outline_colors_for_palette (
cfg :BrewBoardHexGrid ,palette :tuple [str ,...]
)->dict [tuple [int ,int ],str ]:
    """(col,row) → outline hex per column from an 8-column palette (fill stays empty)."""
    cols =max (1 ,cfg .columns )
    rows =max (1 ,cfg .rows )
    pal =tuple (palette or ())
    if not pal :
        pal =gv .PORT_ROYAL_BOARD_COLUMN_HEX 
    out :dict [tuple [int ,int ],str ]={}
    for cc in range (cols ):
        color =pal [cc ]if cc <len (pal )else pal [-1 ]
        for rr in range (rows ):
            out [(cc ,rr )]=color 
    return out 

def compute_port_royal_hex_cell_outline_colors (cfg :BrewBoardHexGrid )->dict [tuple [int ,int ],str ]:
    """(col,row) → outline hex per column from ``PORT_ROYAL_BOARD_COLUMN_HEX`` (fill stays empty)."""
    return compute_hex_cell_outline_colors_for_palette (cfg ,gv .PORT_ROYAL_BOARD_COLUMN_HEX )

def _hex_polygon_points (cx :float ,cy :float ,r :float )->list [float ]:
    """Pointy-top hex (vertex at top); same as phase 0 in _hex_polygon_points_phase."""
    return _hex_polygon_points_phase (cx ,cy ,r ,0.0 )

def _hex_polygon_points_phase (cx :float ,cy :float ,r :float ,phase_deg :float )->list [float ]:
    """Regular hex; phase_deg rotates the whole cell (e.g. +30 for flat-top, horizontal flats)."""
    pts :list [float ]=[]
    base =-90.0 +phase_deg 
    for i in range (6 ):
        ang =math .radians (i *60 +base )
        pts .append (cx +r *math .cos (ang ))
        pts .append (cy +r *math .sin (ang ))
    return pts 

def _hex_polygon_stretched_rotated (
cx :float ,
cy :float ,
r :float ,
phase_deg :float ,
stretch_x :float ,
stretch_y :float ,
grid_rotation_deg :float ,
)->list [float ]:
    """
    Hex outline vertex offsets scaled by stretch_* then rotated by grid_rotation_deg
    (same transform as cell centers) so the overlay rotates as one rigid layer.
    """
    base =-90.0 +phase_deg 
    rad_gr =math .radians (grid_rotation_deg )
    cr ,sr =math .cos (rad_gr ),math .sin (rad_gr )
    pts :list [float ]=[]
    for i in range (6 ):
        ang =math .radians (i *60 +base )
        dx =stretch_x *r *math .cos (ang )
        dy =stretch_y *r *math .sin (ang )
        if abs (grid_rotation_deg )>1e-6 :
            rx =dx *cr -dy *sr 
            ry =dx *sr +dy *cr 
        else :
            rx ,ry =dx ,dy 
        pts .append (cx +rx )
        pts .append (cy +ry )
    return pts 

def hex_memory_piece_fit_px (
r :float ,
phase_deg :float ,
stretch_x :float ,
stretch_y :float ,
grid_rotation_deg :float ,
*,
inset :float =0.98 ,
outline_inset_px :float =0.0 ,
)->tuple [float ,float ]:
    """
    Pixel sizes for board-memory art matching ``_hex_polygon_stretched_rotated`` geometry.

    Returns ``(circle_radius_px, square_thumbnail_side_px)`` for a hex centered at the origin
    with the same ``r`` / stretch / rotation as the **drawn** outline. Uses true edge distance
    (inradius) and ``min(2 * inradius, 2 * min(bbox_half_w, bbox_half_h))`` so squares fill
    flat-top cells (side = flat-to-flat) without double-counting stretch on ``r``.

    ``outline_inset_px`` should be ~half the canvas outline width: the stroke is centered on
    the path, so the visible inner fill sits that much inside the geometric hex.

    After the geometric fit, ``variables.global_variables`` applies
    ``BREW_HEX_MEMORY_SIMPLE_DISK_FILL_MUL`` (disk radius) and
    ``BREW_HEX_MEMORY_EXACT_THUMB_FILL_MUL`` (square thumbnail side) independently.
    """
    oi =max (0.0 ,float (outline_inset_px ))
    pts =_hex_polygon_stretched_rotated (
    0.0 ,
    0.0 ,
    float (r ),
    float (phase_deg ),
    float (stretch_x ),
    float (stretch_y ),
    float (grid_rotation_deg ),
    )
    xs =pts [0 ::2 ]
    ys =pts [1 ::2 ]
    verts =list (zip (xs ,ys ))
    rin =float ("inf")
    for i in range (6 ):
        x0 ,y0 =verts [i ]
        x1 ,y1 =verts [(i +1 )%6 ]
        den =math .hypot (x1 -x0 ,y1 -y0 )
        if den <1e-12 :
            continue 
        d =abs (x0 *y1 -x1 *y0 )/den 
        rin =min (rin ,d )
    rin =max (rin -oi ,1e-6 )
    half_w =max (abs (x )for x in xs )
    half_h =max (abs (y )for y in ys )
    # Flat-to-flat–style cap from bbox; subtract stroke once on the diameter (not per-axis on
    # vertices, which over-shrank width vs the edge-based ``rin``).
    cap =max (2.0 *min (half_w ,half_h )-2.0 *oi ,1e-6 )
    base_side =min (2.0 *rin ,cap )*float (inset )
    base_disk =rin *float (inset )
    mul_s =float (getattr (gv ,"BREW_HEX_MEMORY_EXACT_THUMB_FILL_MUL",1.0 ))
    mul_d =float (getattr (gv ,"BREW_HEX_MEMORY_SIMPLE_DISK_FILL_MUL",1.0 ))
    mul_s =max (0.95 ,min (1.18 ,mul_s ))
    mul_d =max (0.85 ,min (1.02 ,mul_d ))
    side =base_side *mul_s 
    r_disk =base_disk *mul_d 
    return r_disk ,side 

def _offset_to_axial_q (col :int ,row :int ,odd_q :bool )->tuple [int ,int ]:
    """Offset (col,row) odd-q / even-q → axial (q, r)."""
    q =col 
    if odd_q :
        r =row -(col -(col &1 ))//2 
    else :
        r =row -(col +(col &1 ))//2 
    return q ,r 

def _offset_to_axial_r (col :int ,row :int ,odd_r :bool )->tuple [int ,int ]:
    """Offset (col,row) odd-r / even-r → axial (q, r)."""
    r =row 
    if odd_r :
        q =col -(row -(row &1 ))//2 
    else :
        q =col -(row +(row &1 ))//2 
    return q ,r 

def _axial_to_pixel_pointy (q :int ,r :int ,R :float )->tuple [float ,float ]:
    """Pointy-top hex centers (circumradius R). https://www.redblobgames.com/grids/hexagons/"""
    x =R *math .sqrt (3 )*(q +r /2.0 )
    y =R *1.5 *r 
    return x ,y 

def _axial_to_pixel_flat (q :int ,r :int ,R :float )->tuple [float ,float ]:
    """Flat-top hex centers (circumradius R)."""
    x =R *1.5 *q 
    y =R *math .sqrt (3 )*(r +q /2.0 )
    return x ,y 

def _offset_col_row_to_local_xy (
col :int ,
row :int ,
R :float ,
tessellation :str ,
stagger :str ,
col_mul :float ,
row_mul :float ,
)->tuple [float ,float ]:
    tess =(tessellation or "flat_top").lower ()
    if tess =="pointy_top":
        st =(stagger or "odd_columns").lower ()
        odd_q =st !="even_columns"
        q ,r =_offset_to_axial_q (col ,row ,odd_q )
        lx ,ly =_axial_to_pixel_pointy (q ,r ,R )
    else :
        st =(stagger or "odd_columns").lower ()
        if st in ("odd_columns","even_columns"):
            odd_q =st !="even_columns"
            q ,r =_offset_to_axial_q (col ,row ,odd_q )
            lx ,ly =_axial_to_pixel_flat (q ,r ,R )
        else :
            odd_r =st !="even_rows"
            q ,r =_offset_to_axial_r (col ,row ,odd_r )
            lx ,ly =_axial_to_pixel_flat (q ,r ,R )
    return lx *col_mul ,ly *row_mul 

def _hex_local_centers_for_R (
cols :int ,
rows :int ,
R :float ,
tessellation :str ,
stagger :str ,
col_mul :float ,
row_mul :float ,
)->list [tuple [float ,float ]]:
    out :list [tuple [float ,float ]]=[]
    for c in range (cols ):
        for rr in range (rows ):
            out .append (_offset_col_row_to_local_xy (c ,rr ,R ,tessellation ,stagger ,col_mul ,row_mul ))
    return out 

def _hex_pack_extents_from_centers (
local_xy :list [tuple [float ,float ]],
R :float ,
tessellation :str ,
col_mul :float ,
row_mul :float ,
)->tuple [float ,float ,float ,float ]:
    if not local_xy :
        return 0.0 ,0.0 ,0.0 ,0.0 
    tess =(tessellation or "flat_top").lower ()
    if tess =="pointy_top":
        extra_x ,extra_y =math .sqrt (3 )*R *col_mul ,2.0 *R *row_mul 
    else :
        extra_x ,extra_y =2.0 *R *col_mul ,math .sqrt (3 )*R *row_mul 
    xs =[p [0 ]for p in local_xy ]
    ys =[p [1 ]for p in local_xy ]
    min_cx ,max_cx =min (xs ),max (xs )
    min_cy ,max_cy =min (ys ),max (ys )
    pack_w =(max_cx -min_cx )+extra_x 
    pack_h =(max_cy -min_cy )+extra_y 
    return min_cx ,min_cy ,pack_w ,pack_h 

def _hex_board_cell_centers_for_cfg (
ax :float ,
ay :float ,
aw :float ,
ah :float ,
cfg :BrewBoardHexGrid ,
)->tuple [list [tuple [float ,float ]],float ,list [tuple [int ,int ]]]:
    """
    Lay out hex cell centers inside the board rectangle using BrewBoardHexGrid.

    Returns (centers in pixel space, circumradius for drawing outlines, (col, row) per center).
    ``(col, row)`` matches ``_hex_local_centers_for_R`` order: column-major, ``row`` 0..rows-1.
    """
    cols ,rows =max (1 ,cfg .columns ),max (1 ,cfg .rows )
    ix =max (0.0 ,min (0.24 ,cfg .inset_fraction_x ))
    iy =max (0.0 ,min (0.24 ,cfg .inset_fraction_y ))
    mx =aw *ix 
    my =ah *iy 
    ax ,ay ,aw ,ah =ax +mx ,ay +my ,aw -2 *mx ,ah -2 *my 
    if aw <16 or ah <16 :
        return [],4.0 ,[]

    tess =(cfg .tessellation or "flat_top").lower ()
    if tess not in ("flat_top","pointy_top"):
        tess ="flat_top"
    cm =max (0.05 ,min (2.0 ,cfg .column_spacing_mul ))
    rm =max (0.05 ,min (2.0 ,cfg .row_spacing_mul ))

    def pack_size (rad :float )->tuple [float ,float ,float ,float ]:
        loc =_hex_local_centers_for_R (cols ,rows ,rad ,tess ,cfg .stagger ,cm ,rm )
        return _hex_pack_extents_from_centers (loc ,rad ,tess ,cm ,rm )

    lo ,hi =3.0 ,min (aw ,ah )/2.0 
    best_r =lo 
    for _ in range (48 ):
        mid =(lo +hi )/2 
        _ ,_ ,pw ,ph =pack_size (mid )
        if pw <=aw and ph <=ah :
            best_r =mid 
            lo =mid 
        else :
            hi =mid 
    r =max (2.0 ,best_r *max (0.5 ,min (1.0 ,cfg .fit_shrink )))
    loc =_hex_local_centers_for_R (cols ,rows ,r ,tess ,cfg .stagger ,cm ,rm )
    min_cx ,min_cy ,pack_w ,pack_h =_hex_pack_extents_from_centers (loc ,r ,tess ,cm ,rm )
    if tess =="pointy_top":
        pad_lx =min_cx -(math .sqrt (3 )/2 )*r *cm 
        pad_ty =min_cy -r *rm 
    else :
        pad_lx =min_cx -r *cm 
        pad_ty =min_cy -(math .sqrt (3 )/2 )*r *rm 
    ox =ax +(aw -pack_w )/2 -pad_lx 
    oy =ay +(ah -pack_h )/2 -pad_ty 

    base_ro =list (cfg .row_offset_y_px )
    row_off =[base_ro [i ]if i <len (base_ro )else 0.0 for i in range (rows )]

    centers :list [tuple [float ,float ]]=[]
    cell_indices :list [tuple [int ,int ]]=[]
    for i ,(lx ,ly )in enumerate (loc ):
        rr =i %rows 
        cc =i //rows 
        cx =ox +lx +cfg .cell_offset_x_px 
        cy =oy +ly +cfg .cell_offset_y_px +row_off [rr ]
        centers .append ((cx ,cy ))
        cell_indices .append ((cc ,rr ))

    pivot_x =ax +aw /2 
    pivot_y =ay +ah /2 
    gs =max (0.05 ,min (2.0 ,cfg .global_scale ))
    scaled :list [tuple [float ,float ]]=[]
    for cx ,cy in centers :
        scaled .append (
        (
        pivot_x +(cx -pivot_x )*gs ,
        pivot_y +(cy -pivot_y )*gs ,
        )
        )
    centers =scaled 
    r_draw =r *gs 

    rot =max (-360.0 ,min (360.0 ,cfg .rotation_degrees ))
    if abs (rot )>1e-6 :
        rad =math .radians (rot )
        cr ,sr =math .cos (rad ),math .sin (rad )
        rotated :list [tuple [float ,float ]]=[]
        for cx ,cy in centers :
            x =cx -pivot_x 
            y =cy -pivot_y 
            rotated .append ((pivot_x +x *cr -y *sr ,pivot_y +x *sr +y *cr ))
        centers =rotated 

    return centers ,r_draw ,cell_indices 

