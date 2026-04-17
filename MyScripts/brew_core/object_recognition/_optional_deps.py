"""Optional numpy, mss, PIL; mss DPI patch on Windows."""

from __future__ import annotations

import sys

try:
    import numpy as np

    NUMPY_OK = True
except ImportError:
    np = None  # type: ignore[assignment]
    NUMPY_OK = False

try:
    import mss  # type: ignore
except ImportError:
    mss = None  # type: ignore[assignment]
else:
    if sys.platform == "win32":
        try:
            from mss import windows as _mss_win  # type: ignore[import-untyped]

            _mss_win.MSS._set_dpi_awareness = lambda _self: None  # type: ignore[method-assign]
        except Exception:
            pass

try:
    from PIL import Image, ImageDraw  # type: ignore

    PIL_AVAILABLE = True
except Exception:
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    PIL_AVAILABLE = False
