"""Bounded, caret-aware snapshot history for Calamus.

Calamus intentionally keeps a lightweight snapshot model rather than replacing
its editor in W95.  Each snapshot owns the document text plus the two semantic
GtkTextBuffer marks that define the caret/selection.  The GTK adapter lives in
``calamus_history_runtime``; this module is completely GTK-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HistoryState:
    """One immutable document-history state.

    ``insert_offset`` and ``selection_bound_offset`` preserve selection
    direction.  Equal offsets represent a plain caret.
    """

    text: str
    insert_offset: int = 0
    selection_bound_offset: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("history text must be a string")
        limit = len(self.text)
        object.__setattr__(self, "insert_offset", max(0, min(int(self.insert_offset), limit)))
        object.__setattr__(
            self,
            "selection_bound_offset",
            max(0, min(int(self.selection_bound_offset), limit)),
        )

    @property
    def has_selection(self) -> bool:
        return self.insert_offset != self.selection_bound_offset


def history_state(value: HistoryState | str) -> HistoryState:
    """Coerce legacy string callers without weakening the typed contract."""
    if isinstance(value, HistoryState):
        return value
    if isinstance(value, str):
        return HistoryState(value)
    raise TypeError("history state must be HistoryState or str")


@dataclass
class TextHistory:
    max_steps: int = 100
    max_snapshot_chars: int = 750_000
    max_total_chars: int = 2_500_000
    undo_stack: list[HistoryState] = field(default_factory=list)
    redo_stack: list[HistoryState] = field(default_factory=list)
    disabled_reason: str | None = None

    def _too_large(self, state: HistoryState) -> bool:
        return len(state.text) > self.max_snapshot_chars

    def _trim_total(self) -> None:
        while len(self.undo_stack) > self.max_steps + 1:
            self.undo_stack.pop(0)
        while (
            sum(len(item.text) for item in self.undo_stack) > self.max_total_chars
            and len(self.undo_stack) > 1
        ):
            self.undo_stack.pop(0)

    def reset(self, value: HistoryState | str) -> None:
        state = history_state(value)
        self.redo_stack.clear()
        self.undo_stack = [state]
        self.disabled_reason = (
            "Undo history limited for large documents" if self._too_large(state) else None
        )

    def replace_current_view_state(self, value: HistoryState | str) -> bool:
        """Refresh caret/selection for the current text without adding an Undo.

        Mature editors record the caret before/after an edit but do not create
        Undo entries for navigation alone.  Replacement is therefore allowed
        only when the document text is byte-for-byte identical.
        """
        state = history_state(value)
        if not self.undo_stack or self.undo_stack[-1].text != state.text:
            return False
        self.undo_stack[-1] = state
        return True

    def commit(self, value: HistoryState | str) -> bool:
        state = history_state(value)
        if self._too_large(state):
            self.undo_stack = [state]
            self.redo_stack.clear()
            self.disabled_reason = "Undo history limited for large documents"
            return False
        if self.disabled_reason:
            self.disabled_reason = None
        if not self.undo_stack:
            self.undo_stack = [state]
            return False
        # Caret-only movement is not a document edit and therefore never adds
        # an Undo level.  Call replace_current_view_state() explicitly at edit
        # boundaries when the stored mark state must be refreshed.
        if state.text == self.undo_stack[-1].text:
            return False
        self.undo_stack.append(state)
        self._trim_total()
        self.redo_stack.clear()
        return True

    def undo(self, current_value: HistoryState | str) -> HistoryState | None:
        current_state = history_state(current_value)
        if self.disabled_reason or len(self.undo_stack) <= 1:
            return None
        current = self.undo_stack.pop()
        self.redo_stack.append(
            current_state if current.text != current_state.text else current
        )
        return self.undo_stack[-1]

    def redo(self) -> HistoryState | None:
        if self.disabled_reason or not self.redo_stack:
            return None
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        self._trim_total()
        return state

    @property
    def current(self) -> HistoryState | None:
        return self.undo_stack[-1] if self.undo_stack else None

    @property
    def can_undo(self) -> bool:
        return not self.disabled_reason and len(self.undo_stack) > 1

    @property
    def can_redo(self) -> bool:
        return not self.disabled_reason and bool(self.redo_stack)
