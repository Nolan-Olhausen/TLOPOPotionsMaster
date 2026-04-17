"""Paths anchored at the MyScripts directory (sibling of this package)."""

from __future__ import annotations

from pathlib import Path

# Directory containing ``app.py``, JSON configs, and this package.
MYSCRIPTS_DIR = Path(__file__).resolve().parent.parent

# Workspace root (e.g. TLOPOScripts): ``oldBot/``, ``PotionBotExeGUI/``, ``Brewing/``.
REPO_ROOT = MYSCRIPTS_DIR.parent.parent
