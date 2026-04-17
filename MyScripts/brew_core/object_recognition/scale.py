from __future__ import annotations

from typing import Any, Dict, List, Tuple

from tlopo_client.geometry import calc_aspect_ratio_transform, expand_polygon_radially

from .shapes import BoxShape, PolyShape, Shape


def _scaled_shapes_for_size(
    raw: List[Shape],
    baseline_w: int,
    baseline_h: int,
    cur_w: int,
    cur_h: int,
    *,
    baseline_fit: str = "auto",
    next_piece_polygon_expand: float = 1.0,
) -> Tuple[List[Shape], Dict[str, Any]]:
    tr = calc_aspect_ratio_transform(
        baseline_w, baseline_h, cur_w, cur_h, baseline_fit=baseline_fit
    )
    sx, sy = tr["scale_x"], tr["scale_y"]
    ox, oy = tr["offset_x"], tr["offset_y"]
    scaled: List[Shape] = []
    for s in raw:
        if isinstance(s, BoxShape):
            scaled.append(
                BoxShape(
                    label=s.label,
                    category=s.category,
                    color=s.color,
                    x0=s.x0 * sx + ox,
                    y0=s.y0 * sy + oy,
                    x1=s.x1 * sx + ox,
                    y1=s.y1 * sy + oy,
                )
            )
        else:
            pts = [(x * sx + ox, y * sy + oy) for (x, y) in s.pts]
            if (
                next_piece_polygon_expand > 1.0005
                and s.label in ("next_piece_left", "next_piece_right")
            ):
                pts = expand_polygon_radially(pts, next_piece_polygon_expand)
            scaled.append(
                PolyShape(
                    label=s.label,
                    category=s.category,
                    color=s.color,
                    closed=s.closed,
                    pts=pts,
                )
            )
    return scaled, dict(tr)
