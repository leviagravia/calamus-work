"""Bounded text-history helpers for Calamus.

The GTK text buffer remains the source of truth.  This module only stores
coarse-grained snapshots so command-level undo stays predictable without
allowing large documents to multiply memory use by 100x.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TextHistory:
    max_steps: int = 100
    max_snapshot_chars: int = 750_000
    max_total_chars: int = 2_500_000
    undo_stack: list[str] = field(default_factory=list)
    redo_stack: list[str] = field(default_factory=list)
    disabled_reason: str | None = None

    def _too_large(self, text: str) -> bool:
        return len(text) > self.max_snapshot_chars

    def _trim_total(self) -> None:
        while len(self.undo_stack) > self.max_steps + 1:
            self.undo_stack.pop(0)
        while sum(len(item) for item in self.undo_stack) > self.max_total_chars and len(self.undo_stack) > 1:
            self.undo_stack.pop(0)

    def reset(self, text: str) -> None:
        self.redo_stack.clear()
        if self._too_large(text):
            self.undo_stack = [text]
            self.disabled_reason = "Undo history limited for large documents"
            return
        self.undo_stack = [text]
        self.disabled_reason = None

    def commit(self, text: str) -> bool:
        if self._too_large(text):
            self.undo_stack = [text]
            self.redo_stack.clear()
            self.disabled_reason = "Undo history limited for large documents"
            return False
        if self.disabled_reason and not self._too_large(text):
            self.disabled_reason = None
        if not self.undo_stack:
            self.undo_stack = [text]
            return False
        if text == self.undo_stack[-1]:
            return False
        self.undo_stack.append(text)
        self._trim_total()
        self.redo_stack.clear()
        return True

    def undo(self, current_text: str) -> str | None:
        if self.disabled_reason or len(self.undo_stack) <= 1:
            return None
        current = self.undo_stack.pop()
        if current != current_text:
            self.redo_stack.append(current_text)
        else:
            self.redo_stack.append(current)
        return self.undo_stack[-1]

    def redo(self) -> str | None:
        if self.disabled_reason or not self.redo_stack:
            return None
        text = self.redo_stack.pop()
        self.undo_stack.append(text)
        self._trim_total()
        return text

    @property
    def can_undo(self) -> bool:
        return not self.disabled_reason and len(self.undo_stack) > 1

    @property
    def can_redo(self) -> bool:
        return not self.disabled_reason and bool(self.redo_stack)
