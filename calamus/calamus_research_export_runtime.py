"""Thin GTK coordinator for W85 Research apparatus export."""
from __future__ import annotations

from typing import Callable

from calamus_research_export_controller import ResearchExportController


def _default_chooser(parent, document_path):
    from calamus_research_export_dialogs import run_research_export_dialog

    return run_research_export_dialog(parent, document_path)


class ResearchExportRuntime:
    def __init__(
        self,
        parent,
        controller: ResearchExportController,
        *,
        document_path_provider: Callable[[], str | None],
        show_error: Callable[[str], None],
        show_info: Callable[[str], None],
        chooser=_default_chooser,
    ) -> None:
        if not isinstance(controller, ResearchExportController):
            raise TypeError("controller must be ResearchExportController")
        if not all(callable(value) for value in (
            document_path_provider, show_error, show_info, chooser
        )):
            raise TypeError("Research export runtime dependencies must be callable")
        self._parent = parent
        self._controller = controller
        self._document_path_provider = document_path_provider
        self._show_error = show_error
        self._show_info = show_info
        self._chooser = chooser

    def export(self) -> bool:
        document_path = self._document_path_provider()
        if not isinstance(document_path, str) or not document_path.strip():
            self._show_error("Save the current document before exporting Research apparatus.")
            return False
        request = self._chooser(self._parent, document_path)
        if request is None:
            return False
        kind, output_path = request
        result = self._controller.export(kind, output_path)
        if not result.exported:
            self._show_error(result.message or "Research apparatus export failed.")
            return False
        detail = result.message
        if result.artifact and result.artifact.unresolved_keys:
            detail += " Unresolved keys: " + ", ".join(result.artifact.unresolved_keys) + "."
        self._show_info(f"Research apparatus exported to:\n{result.path}\n\n{detail}")
        return True
