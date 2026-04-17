from __future__ import annotations

from typing import Callable

LogFn = Callable[[str, str], None]


def _default_log(_level: str, msg: str) -> None:
    print(msg, flush=True)
