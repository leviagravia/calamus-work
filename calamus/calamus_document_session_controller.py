"""GTK-free orchestration ports for W102 document-session transitions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from calamus_document_session import (
    DocumentSession,
    DocumentSessionPhase,
    DocumentSessionTransition,
)
from calamus_file_lifecycle import NewPlan, OpenPlan, SavePlan, prepare_open_plan


@dataclass(frozen=True)
class DocumentSessionPorts:
    read_buffer_text: Callable[[], str]
    replace_buffer_text: Callable[[str], None]
    reset_undo_history: Callable[[], None]
    read_text_file: Callable[[str], str]
    write_text_file: Callable[[str, str], None]
    is_large_text_file: Callable[[str], bool]


class DocumentSessionController:
    __slots__ = ("session", "ports")

    def __init__(self, session: DocumentSession, ports: DocumentSessionPorts) -> None:
        if not isinstance(session, DocumentSession):
            raise TypeError("session must be a DocumentSession")
        if not isinstance(ports, DocumentSessionPorts):
            raise TypeError("ports must be DocumentSessionPorts")
        self.session = session
        self.ports = ports

    def capture_buffer_text(self) -> str:
        text = self.ports.read_buffer_text()
        self.session.synchronize_text(text)
        return text

    def observe_buffer_change(self) -> bool:
        return self.session.observe_buffer_change(self.ports.read_buffer_text())

    def replace_current_text(self, text: str, *, modified: bool = False) -> DocumentSessionTransition:
        with self.session.replacement():
            self.ports.replace_buffer_text(text)
        transition = self.session.replace_current_text(text, modified=modified)
        self.ports.reset_undo_history()
        return transition

    def execute_new(self, plan: NewPlan) -> DocumentSessionTransition:
        with self.session.replacement():
            self.ports.replace_buffer_text(plan.text)
        transition = self.session.commit_new(plan)
        self.ports.reset_undo_history()
        return transition

    def open_path(self, path: str) -> tuple[OpenPlan, DocumentSessionTransition]:
        plan = prepare_open_plan(
            path,
            self.ports.read_text_file(path),
            large_file=self.ports.is_large_text_file(path),
        )
        return plan, self.execute_open(plan)

    def execute_open(self, plan: OpenPlan) -> DocumentSessionTransition:
        with self.session.replacement(DocumentSessionPhase.OPENING):
            self.ports.replace_buffer_text(plan.text)
        transition = self.session.commit_open(plan)
        self.ports.reset_undo_history()
        return transition

    def execute_save(self, plan: SavePlan) -> DocumentSessionTransition:
        if not plan.target_path:
            raise ValueError("save plan has no target path")
        if plan.replaces_buffer_text:
            with self.session.replacement(DocumentSessionPhase.SAVING):
                self.ports.replace_buffer_text(plan.text_to_write)
            self.session.stage_save_text(plan)
        self.ports.write_text_file(plan.target_path, plan.text_to_write)
        return self.session.commit_save(plan)
