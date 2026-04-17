from __future__ import annotations


def format_island(slug: str) -> str:
    return slug.replace("_", " ").title()


def island_display_for_gui(island: str | None) -> str:
    if not island or not str(island).strip():
        return "Any Island"
    key = str(island).strip().lower()
    if key == "port_royal":
        return "Any Island"
    if key == "padres":
        return "Padres del Fuego"
    if key == "tortuga":
        return "Tortuga & Bilgewater"
    return format_island(str(island))


def potion_is_any_island(potion: dict) -> bool:
    isl = potion.get("island", "")
    return island_display_for_gui(str(isl) if isl else None) == "Any Island"


def brew_board_strategy_label(potion: dict) -> str:
    isl = island_display_for_gui(str(potion.get("island") or ""))
    if isl == "Any Island":
        return "[Port Royal] Board Rule"
    return f"[{isl}] Board Rule"


def potion_supports_port_royal_column_board_rule(potion: dict) -> bool:
    isl = str(potion.get("island") or "").strip().lower()
    return isl in ("", "port_royal", "cuba", "tortuga", "padres")


def brew_choice_is_board_rule(potion: dict, choice: str) -> bool:
    return (choice or "").strip() == brew_board_strategy_label(potion)


def brew_potion_strategy_label(potion: dict) -> str:
    st = potion.get("strategy")
    if isinstance(st, dict):
        name = str(st.get("strategy_name") or "").strip()
        if name:
            return name
    dn = str(potion.get("display_name") or "Potion").strip()
    return f"{dn} (strategy TBD)"


def brew_strategy_choices(potion: dict) -> tuple[str, str]:
    return brew_board_strategy_label(potion), brew_potion_strategy_label(potion)
