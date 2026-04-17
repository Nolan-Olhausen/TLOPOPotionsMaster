"""
Development helper: run the Tk GUI and restart it whenever app.py is saved.

  pip install -r requirements-dev.txt
  python dev_watch.py

No browser involved — Tk apps preview by running Python. PyInstaller builds are only for shipping.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_PY = ROOT / "app.py"

_proc: subprocess.Popen[str] | None = None
_lock = threading.Lock()
_pending: float = 0.0
_DEBOUNCE_S = 0.35


def _kill_proc() -> None:
    global _proc
    if _proc is None or _proc.poll() is not None:
        _proc = None
        return
    _proc.terminate()
    try:
        _proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        _proc.kill()
    _proc = None


def _start_proc() -> None:
    global _proc
    _kill_proc()
    _proc = subprocess.Popen(
        [sys.executable, str(APP_PY)],
        cwd=str(ROOT),
    )


def _schedule_restart() -> None:
    global _pending
    now = time.monotonic()
    with _lock:
        _pending = now + _DEBOUNCE_S


def _restart_loop() -> None:
    global _pending
    while True:
        time.sleep(0.08)
        with _lock:
            due = _pending
        if due and time.monotonic() >= due:
            with _lock:
                _pending = 0.0
            print("\n--- Reloading app.py ---\n", flush=True)
            _start_proc()


def main() -> None:
    global _proc
    if not APP_PY.is_file():
        print(f"Missing {APP_PY}", file=sys.stderr)
        sys.exit(1)

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        print("Install watchdog for auto-reload:  pip install -r requirements-dev.txt")
        print("Starting once without watch...\n", flush=True)
        subprocess.run([sys.executable, str(APP_PY)], cwd=str(ROOT))
        return

    class _Handler(FileSystemEventHandler):
        def on_modified(self, event):  # type: ignore[override]
            if event.is_directory:
                return
            p = Path(str(event.src_path))
            if p.resolve() == APP_PY.resolve():
                _schedule_restart()

    t = threading.Thread(target=_restart_loop, daemon=True)
    t.start()

    obs = Observer()
    obs.schedule(_Handler(), str(ROOT), recursive=False)
    obs.start()
    print("Watching app.py — save the file to reload the window. Ctrl+C to stop.\n", flush=True)
    _start_proc()
    try:
        while True:
            time.sleep(0.5)
            if _proc is not None and _proc.poll() is not None:
                code = _proc.returncode
                if code not in (0, None):
                    print(f"\n(app exited with {code}; fix errors or save app.py to retry)\n", flush=True)
                _proc = None
    except KeyboardInterrupt:
        pass
    finally:
        obs.stop()
        obs.join(timeout=2)
        _kill_proc()


if __name__ == "__main__":
    main()
