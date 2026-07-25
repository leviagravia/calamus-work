"""Thin GTK coordinator for W87 BibTeX/BibLaTeX import and export."""
from __future__ import annotations

from calamus_bibtex_controller import BibtexController
from calamus_bibtex_dialogs import (
    confirm_bib_import,
    run_bib_export_destination_dialog,
    run_bib_export_preview_dialog,
    run_bib_file_dialog,
    run_bib_format_dialog,
    run_bib_import_preview_dialog,
    show_bib_error,
    show_bib_export_result,
    show_bib_import_result,
)


class BibtexRuntime:
    def __init__(self, parent, controller: BibtexController) -> None:
        if not isinstance(controller, BibtexController):
            raise TypeError("controller must be BibtexController")
        self._parent = parent
        self._controller = controller

    def import_references(self) -> bool:
        source = run_bib_file_dialog(self._parent)
        if not source:
            return False
        format = run_bib_format_dialog(self._parent, title="Import BibTeX/BibLaTeX")
        if not format:
            return False
        try:
            inspection = self._controller.inspect_import(source, format)
        except (OSError, TypeError, UnicodeError, ValueError) as error:
            show_bib_error(self._parent, "Cannot inspect bibliography", str(error))
            return False
        decisions = run_bib_import_preview_dialog(self._parent, inspection.preview)
        if decisions is None:
            return False
        try:
            plan = self._controller.prepare_import(inspection, decisions)
        except (OSError, TypeError, UnicodeError, ValueError) as error:
            show_bib_error(self._parent, "Cannot prepare import", str(error))
            return False
        if not confirm_bib_import(self._parent, plan):
            return False
        result = self._controller.apply_import(plan)
        show_bib_import_result(self._parent, result)
        return result.succeeded

    def export_references(self) -> bool:
        format = run_bib_format_dialog(self._parent, title="Export References as BibTeX/BibLaTeX")
        if not format:
            return False
        try:
            plan = self._controller.prepare_export(format)
        except (OSError, TypeError, UnicodeError, ValueError) as error:
            show_bib_error(self._parent, "Cannot prepare export", str(error))
            return False
        if not run_bib_export_preview_dialog(self._parent, plan.artifact):
            return False
        destination = run_bib_export_destination_dialog(self._parent, format)
        if not destination:
            return False
        result = self._controller.apply_export(plan, destination)
        show_bib_export_result(self._parent, result)
        return result.succeeded
