"""
One-shot object recognition matching PotionBotExeGUI ``object_recognition.ObjectRecognizer``:

- Load ``object_shapes.json`` (baseline size from ``captured_image_size``; optional
  ``next_piece_polygon_expand`` scales ``next_piece_*`` hex polys toward the border).
- Capture the TLOPO **client** rectangle with ``mss`` (BGRA → grayscale).
- Map shapes with ``tlopo_client.geometry.calc_aspect_ratio_transform`` (letterbox / pillarbox / uniform).
- Per shape: ``mean`` (mean gray), ``contrast`` (stddev), ``n`` (pixel count).

Shape file resolution (first hit):

1. Path from env ``BREW_OBJECT_SHAPES`` if set and the file exists
2. ``<repo>/PotionBotExeGUI/configuration/object_shapes.json`` (canonical; includes ``baseline_fit``)
3. ``MyScripts/object_shapes.json`` only if the shared file is missing (avoids a stale local
   copy shadowing the repo config)
"""

from __future__ import annotations

from ._log import LogFn, _default_log
from .capture import capture_client_bgra, mapping_size_from_bgra_frame
from .pipeline import (
    capture_recognition_bundle_for_ui,
    run_get_objects_pipeline,
    run_object_recognition_roi_only,
)
from .scale import _scaled_shapes_for_size
from .shapes import BoxShape, PolyShape, Shape, load_shapes, resolve_object_shapes_json

__all__ = [
    "BoxShape",
    "LogFn",
    "PolyShape",
    "Shape",
    "_default_log",
    "_scaled_shapes_for_size",
    "capture_client_bgra",
    "capture_recognition_bundle_for_ui",
    "load_shapes",
    "mapping_size_from_bgra_frame",
    "resolve_object_shapes_json",
    "run_get_objects_pipeline",
    "run_object_recognition_roi_only",
]
