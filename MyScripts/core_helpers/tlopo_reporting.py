from __future__ import annotations

from typing import Any

import variables.global_variables as gv


def _tlopo_drop_slots_by_screen_order(results: list[dict[str, Any]]) -> dict[str, int]:
    drops: list[tuple[float, float, str]] = []
    for r in results:
        lab = str(r.get("label", ""))
        if not lab.lower().startswith("drop_"):
            continue
        cx = r.get("cx")
        cy = r.get("cy")
        fx = float(cx) if isinstance(cx, (int, float)) else 0.0
        fy = float(cy) if isinstance(cy, (int, float)) else 0.0
        drops.append((fx, fy, lab))
    drops.sort(key=lambda t: (t[0], t[1]))
    return {lab: i + 1 for i, (_, __, lab) in enumerate(drops)}


def _tlopo_human_object_name(raw: str, drop_slots: dict[str, int] | None = None) -> str:
    if raw in gv._TLOPO_OBJECT_LABEL_OVERRIDES:
        return gv._TLOPO_OBJECT_LABEL_OVERRIDES[raw]
    if drop_slots is not None and raw in drop_slots:
        return f"Drop Location {drop_slots[raw]}"
    return " ".join(w.capitalize() for w in raw.split("_"))


def _tlopo_piece_color_word(token: str) -> str:
    return gv._TLOPO_PIECE_COLOR_WORDS.get(token, token)


def _tlopo_object_location_line(
    entry: dict[str, Any], *, drop_slots: dict[str, int] | None = None
) -> str:
    lab = str(entry.get("label", ""))
    name = _tlopo_human_object_name(lab, drop_slots)
    cx = entry.get("cx")
    cy = entry.get("cy")
    if cx is not None and cy is not None:
        return f"{name}: ({int(cx)}, {int(cy)})"
    return name


def _tlopo_format_get_locations_report(
    results: list[dict[str, Any]],
    piece_info: dict[str, Any] | None,
    *,
    include_piece_color_block: bool = True,
) -> str:
    lines: list[str] = []
    drop_slots = _tlopo_drop_slots_by_screen_order(results)
    n = len(results)
    lines.append(f"Locations found: {n}")
    lines.append(
        "Locations (coordinates are within the game client window, origin top-left):"
    )
    for r in results:
        lines.append(f"  {_tlopo_object_location_line(r, drop_slots=drop_slots)}")
    names = [_tlopo_human_object_name(str(r.get("label", "")), drop_slots) for r in results]
    lines.append(f"Location list: {', '.join(names) if names else '(none)'}")

    if not include_piece_color_block or not isinstance(piece_info, dict):
        lines.append("")
        return "\n".join(lines)

    lines.append("")
    lines.append("Pieces (color pass)")
    npi = piece_info.get("next_pieces") or {}
    cur_l = piece_info.get("current_piece_left")
    cur_r = piece_info.get("current_piece_right")
    cur_combined = piece_info.get("current_piece_area_combined")
    if isinstance(cur_l, dict) or isinstance(cur_r, dict):
        for key, title in (
            ("current_piece_left", gv._TLOPO_CURRENT_PIECE_TITLES["current_piece_left"]),
            ("current_piece_right", gv._TLOPO_CURRENT_PIECE_TITLES["current_piece_right"]),
        ):
            slot = piece_info.get(key)
            if isinstance(slot, dict) and "label" in slot:
                lines.append(f"{title}: {_tlopo_piece_color_word(str(slot['label']))}")
            else:
                lines.append(f"{title}: (not available)")
    elif isinstance(cur_combined, dict) and "label" in cur_combined:
        lines.append(
            f"Current piece area (single wide polygon — one mixed color read): "
            f"{_tlopo_piece_color_word(str(cur_combined['label']))}"
        )
        lines.append(
            "  (Current piece left/right ROIs were missing or unusable; split of "
            "current_piece_area also failed.)"
        )
    else:
        lines.append("Current pieces: (not available)")
    for key in ("next_piece_left", "next_piece_right"):
        title = gv._TLOPO_NEXT_PIECE_TITLES.get(key, key)
        slot = npi.get(key)
        if isinstance(slot, dict) and "label" in slot:
            lines.append(f"{title}: {_tlopo_piece_color_word(str(slot['label']))}")
        else:
            lines.append(f"{title}: (not available)")
    lines.append("")
    return "\n".join(lines)
