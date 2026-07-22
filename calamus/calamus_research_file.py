"""Shared file identity and atomic UTF-8 persistence for Calamus Research data."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from typing import Any


@dataclass(frozen=True)
class FileToken:
    exists: bool
    mtime_ns: int = 0
    size: int = 0
    digest: str = ""


def file_token(path: str) -> FileToken:
    if not isinstance(path, str) or not path:
        return FileToken(False)
    try:
        stat_result = os.stat(path)
        with open(path, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        return FileToken(
            True,
            stat_result.st_mtime_ns,
            stat_result.st_size,
            digest,
        )
    except OSError:
        return FileToken(False)


def atomic_write_utf8(path: str, text: Any) -> FileToken:
    """Atomically replace *path* with normalized UTF-8 text and return its token."""
    if not isinstance(path, str) or not path:
        raise ValueError("path is required")
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    directory = os.path.dirname(path)
    tmp_path = path + ".tmp"
    if directory:
        os.makedirs(directory, exist_ok=True)
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        return file_token(path)
    except OSError:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError:
            pass
        raise
