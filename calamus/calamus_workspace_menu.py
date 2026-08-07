"""GTK-free Recent Workspaces menu projection for W105."""
from __future__ import annotations

from calamus_menu_model import DynamicMenuRow, recent_workspace_rows


def recent_workspaces_projection(paths) -> tuple[DynamicMenuRow, ...]:
    return recent_workspace_rows(paths)
