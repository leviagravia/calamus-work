"""Core document model for Calamus.

This module deliberately has no GTK dependency.  It owns document identity,
text, and dirty state so the UI can be refactored without changing editor
semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from calamus_document import read_text_file, write_text_file, is_large_text_file


@dataclass
class Document:
    text: str = ""
    file_path: Optional[str] = None
    modified: bool = False

    def set_text(self, text: str, *, modified: bool = True) -> None:
        self.text = text if isinstance(text, str) else ""
        self.modified = bool(modified)

    def get_text(self) -> str:
        return self.text

    def mark_modified(self, text: str | None = None) -> None:
        if text is not None:
            self.text = text
        self.modified = True

    def mark_saved(self, text: str | None = None, path: str | None = None) -> None:
        if text is not None:
            self.text = text
        if path is not None:
            self.file_path = path
        self.modified = False

    def clear(self) -> None:
        self.text = ""
        self.file_path = None
        self.modified = False

    def load(self, path: str) -> str:
        text = read_text_file(path)
        self.file_path = path
        self.text = text
        self.modified = False
        return text

    def save(self, path: str | None = None, text: str | None = None) -> None:
        target = path or self.file_path
        if not target:
            raise ValueError("No file path set for document save")
        if text is not None:
            self.text = text
        write_text_file(target, self.text)
        self.file_path = target
        self.modified = False

    def is_large(self, threshold: int | None = None) -> bool:
        if not self.file_path:
            return False
        return is_large_text_file(self.file_path, threshold=threshold) if threshold is not None else is_large_text_file(self.file_path)
