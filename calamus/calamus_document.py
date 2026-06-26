"""Document I/O helpers for Calamus."""
from __future__ import annotations

import os

LARGE_FILE_BYTES = 1_000_000


def file_size(path: str) -> int:
    return os.path.getsize(path)


def is_large_text_file(path: str, threshold: int = LARGE_FILE_BYTES) -> bool:
    try:
        return file_size(path) >= threshold
    except OSError:
        return False


def read_text_file(path: str) -> str:
    """Read a text document. UTF-8 is preferred; locale fallback preserves legacy files."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="locale") as f:
            return f.read()


def write_text_file(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
