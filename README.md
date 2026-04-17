# TLOPO Potions Master (Brewing GUI)

Desktop companion for **The Legend of Pirates Online** potion brewing. It shows a searchable potion catalog with recipes and ingredients, a **brewing board** view with a Port Royal–style hex layout, optional **automation** (clicks and recovery in the real game window), and tools to **capture the game window**, sample board colors, and run a **guided color wizard**.

The shipped executable is **`TLOPOPotionsMaster.exe`** (built from `MyScripts/`). This document is written for anyone using the app from source or from the built `.exe`.

---

## Repository layout (what lives where)

| Location | Purpose |
|----------|---------|
| **`MyScripts/`** | Application code (`app.py`), catalog data, fonts, PyInstaller spec, and `brew_gui_settings.json` when running from source. |
| **`MyScripts/potions/catalog.json`** | Potion list and recipe metadata the GUI loads at startup. |
| **`GUI/`** | Background art for **fancy** UI: list screen (`BrewingListGUI.jpg` or `.png`) and game screen (`BrewingGameGUI.png` or `.jpg`). Without these, fancy mode falls back to a plain black canvas (see app docstring). |
| **`pieces/`** | Ingredient piece PNGs used in the recipe column (canonical naming: `{Color}{level}{Name}.png`; catalog color `black` maps to grey art). |
| **`LICENSE.txt`** | Project license. |
| **`MyScripts/fonts/`** | Bundled **Cormorant** serif (plus `OFL.txt`) for list/recipe typography when font files are available. |

Frozen builds bundle `potions/`, `GUI/`, `pieces/`, `fonts/`, and data files the spec lists; settings still persist to a JSON file next to the `.exe` (see below).

---

## Requirements

### Always (source run and typical automation)

- **Python 3.10+** (recommended; match whatever you use to build the exe).
- Install from **`MyScripts/requirements.txt`**:

  ```text
  Pillow>=10.0.0
  pynput>=1.7.6
  ```

### Optional: live TLOPO window + screenshots + recognition

For **Get Window**, **Get Locations**, shape overlay, and ROI-style color work, install **`MyScripts/requirements-tlopo-window.txt`** (Windows: **pywin32**, **mss**, **numpy**). Without these, parts of the integration stack are unavailable; the catalog and local board UI may still work.

### Building the `.exe`

- **`MyScripts/requirements-build.txt`** (includes PyInstaller). Use **`MyScripts/build.ps1`** or **`build.cmd`** from the `MyScripts` folder.

---

## Running from source

1. Open a terminal and install dependencies:

   ```powershell
   cd path\to\Brewing\MyScripts
   pip install -r requirements.txt
   ```

 Add optional window capture when needed:

   ```powershell
   pip install -r requirements-tlopo-window.txt
   ```

2. Start the app:

   ```powershell
   python app.py
   ```

If `catalog.json` is missing or invalid, the app exits with an error on the console.

**Working directory:** Run from `MyScripts` so relative paths and imports behave as expected (this matches how `get_catalog_path()` and sibling packages resolve).

---

## Running the built executable

After a successful build, **`MyScripts/dist/TLOPOPotionsMaster.exe`** is the portable app.

- **Settings file:** `brew_gui_settings.json` is stored **next to the `.exe`** (not inside `_MEIPASS`), so your preferences survive updates if you keep the same folder.
- Close the running exe before rebuilding with PyInstaller (avoid file locks / permission errors).

---

## Main screens

### Catalog (potion list)

- **List:** Scroll with the mouse wheel, scrollbar, or **Page Up / Page Down**. **Up / Down** move the selection on the list (catalog fancy mode).
- **Select a potion:** Click a row. Some islands (e.g. **Any Island**, or certain three-color islands) trigger a **confirmation** dialog before entering the game view.
- **Recipe column (fancy mode):** Title, meta line, ingredients, and piece thumbnails for the selected potion.
- **Simple UI catalog:** Same data in a compact layout: controls on the left, list on the right, **Credits** at the bottom. No themed JPG/PNG background.

### Game view (brewing board)

- **Fancy mode:** Full game template art, recipe column, hex grid over the board region, **switch recipe** link, strategy embed, **Start** automation, and top-row actions (**Get Window**, **Get Locations**, **Config Colors**, **Config Panel**, **Logs**, **Object overlay** as applicable).
- **Simple mode:** Grey full-window layout; **no** recipe column or decorative board art on canvas; **potion list stays visible** on the right so you can switch recipes in-game; **Active Potion** shows the current selection on the left.
- **Back to catalog:** **Escape**, or use **switch recipe** / back affordance depending on mode.

---

## Fancy UI vs Simple UI

| | **Fancy UI** | **Simple UI** |
|---|--------------|----------------|
| Background | Letterboxed template images from **`GUI/`** | Flat grey panels |
| Recipe column | Shown in catalog and fancy game | Hidden in simple mode |
| Hex board art | Fancy game | Hidden in simple game (list remains) |
| Templates | Requires list + game images for full experience | Works without `GUI/` images |

Toggle **Simple UI** in the **Config** panel (checkbox: *“Simple UI (no themed background, no recipe/board art)”*), then save/apply so settings persist.

---

## Config panel and persistence

Open **Config** from the in-app control. The app saves many options to **`brew_gui_settings.json`**:

- **From source:** `MyScripts/brew_gui_settings.json`
- **From exe:** same file name **next to** `TLOPOPotionsMaster.exe`

You can back up or reset this file if the UI gets into a bad state (automation timings, RGB samples, ring median grid, **simple_ui**, etc.). The config “OK” / apply path redraws the background and reapplies layout.

---

## Game integration workflow (typical)

These steps assume optional **tlopo-window** dependencies are installed and the game is running on the same PC.

1. **Get Window** — Finds and attaches to the TLOPO game window for later screenshots and automation.
2. **Get Locations** — Refreshes geometry / client rect used for captures (button enables after a successful window grab when applicable).
3. **Config Colors** (or guided wizard) — Aligns RGB sampling with **your** board and UI; ring median colors and piece colors feed recognition and overlays.
4. **Select strategy** (Port Royal board strategy, etc.) and review the embedded strategy UI.
5. **Start** — Arms automation; use the documented **Left Ctrl** hotkey to start/pause when the app indicates it is armed.

Exact labels and enablement are shown on the live buttons. Use the **Logs** panel for step traces and errors.

---

## Automation and hotkeys

- Automation drives the **real game window** using timed clicks and recovery logic (Port Royal–oriented flows in code). Tune delays and polling in **Config** if clicks race the UI.
- **pynput** is used for hotkeys and input; some environments (elevated apps, remote desktop) can interfere—run without extra permission mismatches when possible.

---

## Keyboard and mouse reference

| Action | Behavior |
|--------|----------|
| **Escape** | Leave game view and return to catalog (when applicable). |
| **Mouse wheel** | Scroll potion list (and guided wizard content where bound). |
| **List click** | Select potion; in **simple game** mode, changes active potion and refreshes strategy context. |
| **Config / Logs / Overlay toggles** | Hit targets on the chrome; simple mode uses the same logical controls in a compact strip. |

---

## Building the release executable

From **`Brewing/MyScripts`**:

```powershell
pip install -r requirements.txt -r requirements-build.txt
.\build.ps1
```

Output: **`dist/TLOPOPotionsMaster.exe`**. The spec file is **`brew_gui.spec`**; adjust datas/hidden imports there if you add new runtime assets.

---

## Troubleshooting

| Symptom | Things to check |
|---------|------------------|
| **Missing catalog** | `MyScripts/potions/catalog.json` exists and contains a top-level `"potions"` array. |
| **Blank / black fancy background** | `Brewing/GUI/` contains the expected list and game template filenames (see `variables/global_variables.py`: `LIST_TEMPLATE_NAMES`, `GAME_TEMPLATE_NAMES`). |
| **Get Window / capture does nothing** | Install `requirements-tlopo-window.txt`; on Windows, pywin32 + mss + numpy. |
| **Automation mis-clicks** | Increase settle/delay values in Config; check Logs; verify resolution/DPI and that the game window is not occluded. |
| **Settings not sticking (exe)** | Ensure `brew_gui_settings.json` is writable beside the exe (portable folder, not a protected install directory). |

---

## Developer documentation

- High-level architecture and package map: docstring at the top of **`MyScripts/app.py`**.
- Typography sizes: **`MyScripts/variables/brew_typography.py`**.
- Shared UI/game constants: **`MyScripts/variables/global_variables.py`**.

---

## License

See **`LICENSE.txt`** in this `Brewing` folder. Font licensing for bundled Cormorant is under **`MyScripts/fonts/OFL.txt`**.
