"""GTK-free result types for Writing Workspace mutations."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceOperationResult:
    success: bool
    path: str
    message: str = ""
    committed: bool = False
    source_path: str = ""
    companion_path: str = ""
    scratchpad_path: str = ""
    rollback_failed: bool = False
