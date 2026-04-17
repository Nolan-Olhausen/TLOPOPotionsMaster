from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._log import LogFn, _default_log
from ._optional_deps import np
from .imaging import _clip, _polygon_mask, _presence_metrics
from .shapes import BoxShape, PolyShape, Shape


def _accumulate_shape_roi_metrics(
    bundle: Dict[str, Any],
    lg: LogFn,
    log: Optional[LogFn],
    verbose_logs: bool,
) -> List[Dict[str, Any]]:
    gray = bundle["gray"]
    shapes: List[Shape] = bundle["shapes"]
    H, W = int(bundle["H"]), int(bundle["W"])
    results: List[Dict[str, Any]] = []
    for s in shapes:
        if isinstance(s, BoxShape):
            x0 = _clip(s.x0, 0, W - 1)
            y0 = _clip(s.y0, 0, H - 1)
            x1 = _clip(s.x1, 1, W)
            y1 = _clip(s.y1, 1, H)
            if x1 <= x0 or y1 <= y0:
                metrics = _presence_metrics(np.empty((0, 0), dtype=np.float32))
            else:
                roi = gray[y0:y1, x0:x1]
                metrics = _presence_metrics(roi)
            cx = int(round((x0 + x1) * 0.5))
            cy = int(round((y0 + y1) * 0.5))
            results.append(
                {
                    "label": s.label,
                    "type": "box",
                    "category": s.category,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "cx": cx,
                    "cy": cy,
                    **metrics,
                }
            )
            lg(
                "INFO",
                f"\U0001f50d \u2022 {s.label}: mean={metrics['mean_gray']}, contrast={metrics['contrast']}, n={metrics['n_pixels']}",
            )
        elif isinstance(s, PolyShape) and s.closed and len(s.pts) >= 3:
            pts = [(_clip(x, 0, W - 1), _clip(y, 0, H - 1)) for (x, y) in s.pts]
            mask = _polygon_mask(H, W, pts)
            metrics = _presence_metrics(gray, mask)
            cx = int(round(sum(x for x, _ in pts) / len(pts)))
            cy = int(round(sum(y for _, y in pts) / len(pts)))
            results.append(
                {
                    "label": s.label,
                    "type": "polygon",
                    "category": s.category,
                    "n_vertices": len(pts),
                    "cx": cx,
                    "cy": cy,
                    **metrics,
                }
            )
            lg(
                "INFO",
                f"\U0001f50d \u2022 {s.label}: mean={metrics['mean_gray']}, contrast={metrics['contrast']}, n={metrics['n_pixels']}",
            )
        else:
            lab = getattr(s, "label", "poly")
            if verbose_logs:
                (log or _default_log)(
                    "WARNING", f"\U0001f50d \u2022 {lab}: polygon not closed or too few points."
                )

    lg("SUCCESS", f"\U0001f50d Recognition complete for {len(results)} shapes.")
    labels = [str(r["label"]) for r in results]
    lg("SUCCESS", f"\U0001f3af Object recognition completed - analyzed {len(results)} shapes")
    if labels:
        lg("INFO", f"\U0001f4ca Detected elements: {', '.join(labels)}")
    return results
