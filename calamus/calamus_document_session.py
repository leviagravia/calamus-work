"""GTK-free authority for the active Calamus document session.

W102 extracts document identity, text snapshot, dirty state, and guarded bulk
replacement from the application window.  Gtk.TextBuffer remains the live
editing surface; the session owns the authoritative non-GTK state and transition
invariants.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Iterator

from calamus_file_lifecycle import NewPlan, OpenPlan, SavePlan
from calamus_model import Document


class DocumentSessionPhase(str, Enum):
    IDLE = "idle"
    REPLACING = "replacing"
    OPENING = "opening"
    SAVING = "saving"


@dataclass(frozen=True)
class DocumentSessionSnapshot:
    text: str
    file_path: str | None
    modified: bool
    phase: DocumentSessionPhase
    revision: int


@dataclass(frozen=True)
class DocumentSessionTransition:
    operation: str
    before: DocumentSessionSnapshot
    after: DocumentSessionSnapshot
    identity_changed: bool
    content_changed: bool


class DocumentSession:
    """Single writable authority for one active plain-text document."""

    __slots__ = ("_document", "_phase", "_phase_depth", "_revision")

    def __init__(self, document: Document | None = None) -> None:
        self._document = document if document is not None else Document()
        self._phase = DocumentSessionPhase.IDLE
        self._phase_depth = 0
        self._revision = 0

    @property
    def document(self) -> Document:
        """Compatibility projection; mutation remains session-owned."""
        return self._document

    @property
    def text(self) -> str:
        return self._document.text

    @property
    def file_path(self) -> str | None:
        return self._document.file_path

    @property
    def modified(self) -> bool:
        return self._document.modified

    @property
    def phase(self) -> DocumentSessionPhase:
        return self._phase

    @property
    def loading(self) -> bool:
        return self._phase_depth > 0

    @property
    def revision(self) -> int:
        return self._revision

    def current_path(self) -> str | None:
        return self.file_path

    def snapshot(self) -> DocumentSessionSnapshot:
        return DocumentSessionSnapshot(
            text=self.text,
            file_path=self.file_path,
            modified=self.modified,
            phase=self.phase,
            revision=self.revision,
        )

    @contextmanager
    def replacement(self, phase: DocumentSessionPhase = DocumentSessionPhase.REPLACING) -> Iterator[None]:
        if not isinstance(phase, DocumentSessionPhase):
            raise TypeError("phase must be a DocumentSessionPhase")
        previous = self._phase
        self._phase_depth += 1
        self._phase = phase
        try:
            yield
        finally:
            self._phase_depth -= 1
            if self._phase_depth < 0:
                self._phase_depth = 0
                self._phase = DocumentSessionPhase.IDLE
                raise RuntimeError("document session replacement depth underflow")
            self._phase = previous if self._phase_depth else DocumentSessionPhase.IDLE

    def synchronize_text(self, text: str) -> None:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        self._document.text = text

    def observe_buffer_change(self, text: str) -> bool:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if self.loading:
            return False
        changed = text != self._document.text or not self._document.modified
        self._document.mark_modified(text)
        if changed:
            self._revision += 1
        return True

    def mark_modified(self, text: str | None = None) -> None:
        if text is not None and not isinstance(text, str):
            raise TypeError("text must be a string or None")
        before = (self._document.text, self._document.modified)
        self._document.mark_modified(text)
        if before != (self._document.text, self._document.modified):
            self._revision += 1

    def replace_current_text(self, text: str, *, modified: bool) -> DocumentSessionTransition:
        before = self.snapshot()
        self._document.set_text(text, modified=modified)
        self._revision += 1
        return self._transition("replace", before)

    def commit_new(self, plan: NewPlan) -> DocumentSessionTransition:
        if not isinstance(plan, NewPlan):
            raise TypeError("plan must be a NewPlan")
        before = self.snapshot()
        self._document.file_path = plan.target_path
        self._document.set_text(plan.text, modified=plan.modified)
        self._revision += 1
        return self._transition("new", before)

    def commit_open(self, plan: OpenPlan) -> DocumentSessionTransition:
        if not isinstance(plan, OpenPlan):
            raise TypeError("plan must be an OpenPlan")
        before = self.snapshot()
        self._document.file_path = plan.target_path
        self._document.set_text(plan.text, modified=False)
        self._revision += 1
        return self._transition("open", before)

    def stage_save_text(self, plan: SavePlan) -> None:
        if not isinstance(plan, SavePlan):
            raise TypeError("plan must be a SavePlan")
        # Preserve historical behavior: normalization can update the visible and
        # model text before a write that may subsequently fail, while identity
        # and dirty state remain unchanged until persistence succeeds.
        self.synchronize_text(plan.text_to_write)

    def commit_save(self, plan: SavePlan) -> DocumentSessionTransition:
        if not isinstance(plan, SavePlan):
            raise TypeError("plan must be a SavePlan")
        if not plan.target_path:
            raise ValueError("save plan has no target path")
        before = self.snapshot()
        self._document.file_path = plan.target_path
        self._document.set_text(plan.text_to_write, modified=False)
        self._revision += 1
        return self._transition("save", before)

    def rebind_path(self, path: str | None) -> DocumentSessionTransition:
        if path is not None and not isinstance(path, str):
            raise TypeError("path must be a string or None")
        before = self.snapshot()
        self._document.file_path = path
        if before.file_path != path:
            self._revision += 1
        return self._transition("rebind", before)

    def detach(self, text: str) -> DocumentSessionTransition:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        before = self.snapshot()
        self._document.file_path = None
        self._document.set_text(text, modified=True)
        self._revision += 1
        return self._transition("detach", before)

    def mark_clean(self, text: str | None = None) -> None:
        """Commit the current snapshot as clean without changing identity."""
        if text is not None and not isinstance(text, str):
            raise TypeError("text must be a string or None")
        before = (self._document.text, self._document.modified)
        if text is not None:
            self._document.text = text
        self._document.modified = False
        if before != (self._document.text, self._document.modified):
            self._revision += 1

    def requires_save_confirmation(self) -> bool:
        return self.modified

    def _transition(self, operation: str, before: DocumentSessionSnapshot) -> DocumentSessionTransition:
        after = self.snapshot()
        return DocumentSessionTransition(
            operation=operation,
            before=before,
            after=after,
            identity_changed=before.file_path != after.file_path,
            content_changed=before.text != after.text,
        )
