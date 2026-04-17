"""Module-level globals extracted from app.py.

Grouped by UI area and runtime usage to keep app.py focused on behavior.
"""

# Base palette and piece rendering.
BLACK = "#000000"
PARCHMENT_EDGE = "#8a7a62"
INK = "#554833"
MUTED = "#4a3d32"
FALLBACK_PANEL = "#d8c8a8"
PIECE_SIZE = 62
HEX_FILL = "#e8dcc8"

COLOR_OUTLINE: dict[str, str] = {
    "red": "#8b1c3a",
    "blue": "#1a5580",
    "green": "#1f6b38",
    "orange": "#a85a12",
    "purple": "#4a2c6e",
    "black": "#3a3a3a",
}

# Catalog "color" -> piece filename color prefix (see Brewing/pieces/*.png)
COLOR_TO_PREFIX: dict[str, str] = {
    "red": "Red",
    "blue": "Blue",
    "green": "Green",
    "orange": "Orange",
    "purple": "Purple",
    "black": "Grey",
}

# Catalog/list and shared recipe layout.
RECIPE_BBOX = (0.05, 0.18, 0.4, 0.8)
LIST_BBOX = (0.57, 0.085, 0.87, 0.84)
LIST_INSET_X = 25
LIST_SCROLLBAR_W = 12
LIST_TITLE_TEXT = "Potion Recipe List"
LIST_TITLE_TOP_PAD = 0
LIST_TITLE_GAP_BELOW = 8
LIST_BODY_BOTTOM_PAD = 6
LIST_TEMPLATE_NAMES = ("BrewingListGUI.jpg", "BrewingListGUI.png")
# Catalog-only control: bottom-left **Credits** (normalized on letterboxed list template).
CATALOG_CREDITS_BBOX = (0.005, 0.945, 0.13, 0.995)
GAME_TEMPLATE_NAMES = ("BrewingGameGUI.png", "BrewingGameGUI.jpg")

# Simple / stripped UI (no template image, no recipe column, no hex board art).
BREW_SIMPLE_UI_LIST_BBOX = (0.03, 0.06, 0.97, 0.92)
BREW_SIMPLE_UI_CANVAS_BG = "#3a3a3e"
BREW_SIMPLE_UI_PANEL_BG = "#4a4a52"
BREW_SIMPLE_UI_TEXT = "#f2f2f5"
BREW_SIMPLE_UI_MUTED = "#b8b8c0"

# Game screen controls and board anchors.
GAME_ART_BBOX = (0.514, 0.053, 0.942, 0.887)
GAME_BACK_BBOX = (0.231, 0.81, 0.343, 0.8)
GAME_LOGS_TOGGLE_BBOX = (0.33, 0.875, 0.45, 0.925)
GAME_OVERLAY_TOGGLE_BBOX = (0.33, 0.935, 0.45, 0.985)
GAME_GET_WINDOW_BBOX = (0.005, 0.005, 0.13, 0.055)
GAME_GET_OBJECTS_BBOX = (0.14, 0.005, 0.265, 0.055)
GAME_CAPTION_WINDOW_IDLE = "1. Get Window"
GAME_CAPTION_WINDOW_OK = "Window Found"
GAME_CAPTION_WINDOW_ERR = "Error Check Logs"
GAME_CAPTION_OBJECTS_IDLE = "2. Get Locations"
GAME_CAPTION_OBJECTS_OK = "Locations Found"
GAME_CAPTION_OBJECTS_ERR = "Error Check Logs"
GAME_GUIDED_CONFIG_BBOX = (0.005, 0.065, 0.13, 0.115)
GAME_CAPTION_GUIDED_IDLE = "3. Config Colors"
GAME_CAPTION_GUIDED_OPTIONAL = "Re-config"
GAME_STRATEGY_BBOX = (0.005, 0.875, 0.22, 0.985)
GAME_AUTOMATION_START_BBOX = (0.225, 0.875, 0.325, 0.985)
GAME_STRATEGY_TITLE = "Select Strategy"
GAME_CAPTION_AUTOMATION_START = "Start"
GAME_CAPTION_AUTOMATION_ARMED = "Running\nPress LEFT CTRL to Start/Pause"
GAME_CONFIG_TOGGLE_BBOX = (0.14, 0.065, 0.265, 0.115)
GAME_STRATEGY_CHOICE_FONT_SIZE = 10

# Disabled button styling.
GAME_UI_BUTTON_DISABLED_FILL = "#1a1814"
GAME_UI_BUTTON_DISABLED_OUTLINE = "#3d342c"
GAME_UI_BUTTON_DISABLED_TEXT = "#6d655c"

# Active game/log panel styling.
GAME_CHROME_WHITE = "#ffffff"
GAME_LOG_PANEL_FILL = "#2e2e32"
GAME_LOG_PANEL_OUTLINE = "#555555"
GAME_LOG_TEXT = "#f5f5f5"
GAME_LOG_TEXT_WIDGET_BG = "#252528"
GAME_LOG_SCROLLBAR_BG = "#3a3a3e"
GAME_LOG_SCROLLBAR_TROUGH = "#1e1e20"
GAME_LOG_MAX_LINES = 400
HEX_GRID_OUTLINE = GAME_CHROME_WHITE
# Board-memory pieces: separate tuning for Simple (incircle disk) vs Exact (square PNG).
# Disk is capped ~1.0 so circles stay inside the cell; thumb can exceed 1.0 for width fill.
BREW_HEX_MEMORY_SIMPLE_DISK_FILL_MUL = 0.96
BREW_HEX_MEMORY_EXACT_THUMB_FILL_MUL = 1.09
GAME_UI_BUTTON_FILL = "#2a2118"
GAME_UI_BUTTON_OUTLINE = "#6a5844"
GAME_UI_BUTTON_TEXT = GAME_CHROME_WHITE

# Game automation config panel sizing.
GAME_CONFIG_PANEL_PAD_PX = 10
GAME_CONFIG_PANEL_OFFSET_X = -260
GAME_CONFIG_PANEL_OFFSET_Y = -50
GAME_CONFIG_PANEL_W_MIN = 745
GAME_CONFIG_PANEL_W_MAX = 760
GAME_CONFIG_PANEL_W_FRAC_OF_BOARD = 0.78
GAME_CONFIG_PANEL_H_FRAC_OF_BOARD = 1.20
GAME_CONFIG_PANEL_H_MAX_PX = 950
GAME_CONFIG_PANEL_SCROLL_MIN_H = 520
GAME_CONFIG_PANEL_INNER_PAD_PX = 28
GAME_CONFIG_PANEL_SCROLL_TOP_RESERVE = 56
# Standalone config / log popups (fixed size; not tied to main-window letterbox scale).
GAME_CONFIG_POPUP_GEOMETRY = "780x880"
GAME_CONFIG_POPUP_CANVAS_W = 732
GAME_CONFIG_POPUP_CANVAS_H = 720
GAME_LOG_POPUP_GEOMETRY = "640x520"

# Automation defaults.
BREW_AUTOMATION_DELAY_DEFAULT_S = 0.0
# Global automation timing defaults (all strategies).
BREW_AUTOMATION_FOREGROUND_SETTLE_DEFAULT_S = 0.1
BREW_AUTOMATION_ACTION_DELAY_DEFAULT_S = 0.1
BREW_AUTOMATION_PRE_CLICK_SETTLE_DEFAULT_S = 0.1
BREW_AUTOMATION_POST_CLICK_SETTLE_DEFAULT_S = 0.1
BREW_AUTOMATION_POST_DROP_SLEEP_DEFAULT_S = 0.0
BREW_AUTOMATION_HAND_POLL_INTERVAL_DEFAULT_MS = 150
BREW_AUTOMATION_BOARD_WAIT_POLL_INTERVAL_DEFAULT_MS = 150
BREW_LIVE_GAME_VISUAL_DEFAULT = "Simple"
BREW_LIVE_GAME_VISUAL_CHOICES: tuple[str, ...] = ("None", "Simple", "Exact")
BREW_AGAIN_PER_CHANNEL_MAX_DELTA = 8

# Guided color wizard.
GAME_GUIDED_WIZARD_GEOMETRY = "1080x820"
GAME_GUIDED_WIZARD_WRAPLENGTH = 1000
_GUIDED_GRID_COLORS: tuple[str, ...] = ("R", "G", "B", "Grey", "O", "P")
_GUIDED_GRID_NEXT_ROWS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Next — left piece is", "next_piece_left", ("next_piece_left",)),
    ("Next — right piece is", "next_piece_right", ("next_piece_right",)),
)
_GUIDED_GRID_CURRENT_ROWS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Current — left piece is", "current_piece_left", ("current_piece_left", "validation_left")),
    ("Current — right piece is", "current_piece_right", ("current_piece_right", "validation_right")),
)
_CONFIG_PIECE_DISPLAY_ORDER: tuple[str, ...] = ("R", "G", "B", "O", "P", "Grey")
_GAME_CONFIG_RING_GRID_SLOTS: tuple[str, ...] = (
    "next_piece_left",
    "next_piece_right",
    "current_piece_left",
    "current_piece_right",
)

# Text labels for object/ROI reports.
_TLOPO_OBJECT_LABEL_OVERRIDES: dict[str, str] = {
    "star_1_middle": "Star Top",
    "star_2_middle": "Star Middle 1",
    "star_3_middle": "Star Middle 2",
    "star_4_middle": "Star Bottom",
    "validation_left": "Current Piece Left",
    "validation_right": "Current Piece Right",
}
_TLOPO_NEXT_PIECE_TITLES: dict[str, str] = {
    "next_piece_left": "Next piece (left)",
    "next_piece_right": "Next piece (right)",
}
_TLOPO_CURRENT_PIECE_TITLES: dict[str, str] = {
    "current_piece_left": "Current piece (left)",
    "current_piece_right": "Current piece (right)",
}
_TLOPO_PIECE_COLOR_WORDS: dict[str, str] = {
    "R": "Red",
    "O": "Orange",
    "G": "Green",
    "B": "Blue",
    "P": "Purple",
    "Grey": "Grey",
    "Unknown": "Unknown",
}

# Persistent app settings.
BREW_GUI_SETTINGS_FILENAME = "brew_gui_settings.json"

# Port Royal board rule.
PORT_ROYAL_BOARD_COLUMN_HEX: tuple[str, ...] = (
    "#8b1c3a",
    "#8b1c3a",
    "#8b1c3a",
    "#1a5580",
    "#1a5580",
    "#1f6b38",
    "#1f6b38",
    "#8b1c3a",
)
ISLAND_CUBA_BOARD_COLUMN_HEX: tuple[str, ...] = (
    "#4a2c6e",  # P
    "#8b1c3a",  # R
    "#1a5580",  # B
    "#4a2c6e",  # P
    "#1f6b38",  # G
    "#1a5580",  # B
    "#8b1c3a",  # R
    "#1f6b38",  # G
)
ISLAND_TORTUGA_BOARD_COLUMN_HEX: tuple[str, ...] = (
    "#3a3a3a",  # Grey
    "#8b1c3a",  # R
    "#1a5580",  # B
    "#3a3a3a",  # Grey
    "#1f6b38",  # G
    "#1a5580",  # B
    "#8b1c3a",  # R
    "#1f6b38",  # G
)
ISLAND_PADRES_BOARD_COLUMN_HEX: tuple[str, ...] = (
    "#a85a12",  # O
    "#8b1c3a",  # R
    "#1a5580",  # B
    "#a85a12",  # O
    "#1f6b38",  # G
    "#1a5580",  # B
    "#8b1c3a",  # R
    "#1f6b38",  # G
)
PORT_ROYAL_OUTLINE_WIDTH_EXTRA = 2
