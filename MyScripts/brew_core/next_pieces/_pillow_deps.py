from __future__ import annotations

try:
    from PIL import Image, ImageDraw, ImageFilter  # type: ignore

    PIL_OK = True
except ImportError:
    Image = ImageDraw = ImageFilter = None  # type: ignore[assignment]
    PIL_OK = False
