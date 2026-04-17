"""
Tk point sizes and recipe row rhythm — **edit this file** to tune the GUI.

Built in ``PotionPickerApp.__init__``:

- **LIST_*** — catalog heading ``LIST_HEADING_PT``; potion rows ``LIST_ROW_PT``; row tightness
  ``LIST_ROW_GAP_EXTRA`` (added to the list font’s linespace).
- **RECIPE_*** — potion name ``RECIPE_POTION_TITLE_PT``; level/island line ``RECIPE_META_LINE_PT``;
  ingredient names ``RECIPE_INGREDIENT_LINE_PT`` (Cormorant / bundled serif).
- **PANEL_AND_OVERLAY_BODY_PT** — config panel, scene labels, game log, strategy, wizard fields
  (Segoe UI / UI sans stack).
- **RECIPE_INGREDIENT_ROW_*** — vertical packing of ingredient rows next to piece art.

Bundled font files: ``MyScripts/fonts/Cormorant-*.ttf`` (see OFL.txt there).
"""

# --- Catalog list: "Potion Recipe List" heading + potion names ---
LIST_HEADING_PT = 16
LIST_ROW_PT = 14
# Row height: list font linespace + this (smaller = tighter rows)
LIST_ROW_GAP_EXTRA = -3

# --- Recipe column: potion name, level/island line, each ingredient name ---
RECIPE_POTION_TITLE_PT = 17
RECIPE_META_LINE_PT = 11
RECIPE_INGREDIENT_LINE_PT = 14
# Vertical gaps in the recipe column (px at ``_layout_font_scale`` 1.0; scaled in ``draw_layers``).
RECIPE_TITLE_META_GAP_PX = 4
RECIPE_META_TO_INGREDIENTS_GAP_PX = 12

# --- Config panel, scene layout labels, game log, strategy row, wizard fields ---
PANEL_AND_OVERLAY_BODY_PT = 10

# --- Recipe ingredient rows (piece thumbnail + name); iy step × row_h per row ---
RECIPE_INGREDIENT_ROW_BELOW_PIECE = 5
RECIPE_INGREDIENT_ROW_STEP = 0.97
