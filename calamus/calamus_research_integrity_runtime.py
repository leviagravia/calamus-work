"""Thin GTK coordinator for W78 Research integrity commands."""
from __future__ import annotations

from typing import Callable, Iterable

from calamus_references import ReferenceRecord
from calamus_research_integrity_controller import ResearchIntegrityController
from calamus_research_integrity_dialogs import (
    confirm_reference_migration,
    run_reference_key_rename_dialog,
    show_integrity_error,
    show_integrity_result,
    show_research_check_report,
)


class ResearchIntegrityRuntime:
    def __init__(
        self,
        parent,
        controller: ResearchIntegrityController,
        *,
        records_provider: Callable[[], Iterable[ReferenceRecord]],
        selected_key_provider: Callable[[], str | None],
    ) -> None:
        if not isinstance(controller, ResearchIntegrityController):
            raise TypeError("controller must be ResearchIntegrityController")
        if not callable(records_provider) or not callable(selected_key_provider):
            raise TypeError("Research integrity providers must be callable")
        self._parent = parent
        self._controller = controller
        self._records_provider = records_provider
        self._selected_key_provider = selected_key_provider

    def rename_reference_key(self) -> bool:
        records = tuple(self._records_provider())
        if not records:
            show_integrity_error(
                self._parent,
                "Rename Reference Key",
                "References is empty.",
            )
            return False
        request = run_reference_key_rename_dialog(
            self._parent,
            records,
            initial_key=self._selected_key_provider(),
        )
        if request is None:
            return False
        old_key, new_key, preserve_alias = request
        try:
            plan = self._controller.prepare_migration(
                old_key,
                new_key,
                preserve_old_alias=preserve_alias,
            )
        except (OSError, TypeError, ValueError) as error:
            show_integrity_error(self._parent, "Cannot prepare migration", str(error))
            return False
        if not confirm_reference_migration(self._parent, plan):
            return False
        result = self._controller.apply_migration(plan)
        show_integrity_result(self._parent, result)
        return result.succeeded

    def research_check(self) -> bool:
        try:
            report = self._controller.research_check()
        except (OSError, TypeError, ValueError) as error:
            show_integrity_error(self._parent, "Research Check failed", str(error))
            return False
        show_research_check_report(self._parent, report)
        return True
