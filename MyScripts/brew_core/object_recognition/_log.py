from __future__ import annotations

from typing import Callable, Optional

LogFn = Callable[[str, str], None]


def _default_log(_level: str, msg: str) -> None:
    print(msg, flush=True)


def _sink_log_for_verbose(log: Optional[LogFn], verbose_logs: bool) -> LogFn:
    def lg(level: str, msg: str) -> None:
        if not verbose_logs and level != "ERROR":
            return
        (log or _default_log)(level, msg)

    return lg
