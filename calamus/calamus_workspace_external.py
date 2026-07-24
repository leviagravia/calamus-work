"""Shell-free external open and reveal adapters."""
from __future__ import annotations

import os
import subprocess


def _launch(candidates: tuple[tuple[str, ...], ...]) -> bool:
    for argv in candidates:
        try:
            subprocess.Popen(argv, start_new_session=True)
            return True
        except (OSError, ValueError):
            continue
    return False


def open_external_path(path: str) -> bool:
    if not isinstance(path, str) or not os.path.exists(path):
        return False
    return _launch((("xdg-open", path), ("gio", "open", path)))


def reveal_in_file_manager(path: str) -> bool:
    if not isinstance(path, str) or not os.path.exists(path):
        return False
    target = path if os.path.isdir(path) else os.path.dirname(path)
    return _launch((("xdg-open", target), ("gio", "open", target)))
