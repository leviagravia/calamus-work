"""Thin GTK coordinator for W86 Tag Integrity."""
from __future__ import annotations

from calamus_tag_integrity_controller import TagIntegrityController
from calamus_tag_integrity_dialogs import (
    confirm_tag_mutation,
    run_tag_integrity_dialog,
    show_tag_error,
    show_tag_result,
)


class TagIntegrityRuntime:
    def __init__(self, parent, controller: TagIntegrityController) -> None:
        if not isinstance(controller, TagIntegrityController):
            raise TypeError("controller must be TagIntegrityController")
        self._parent = parent
        self._controller = controller

    def manage(self) -> bool:
        try:
            inventory = self._controller.inventory()
        except (OSError, TypeError, ValueError) as error:
            show_tag_error(self._parent, "Tag Integrity failed", str(error))
            return False
        if not inventory.items:
            show_tag_error(
                self._parent,
                "Tag Integrity",
                "No tags are available in References or the current Source Notes sidecar.",
            )
            return False

        request = run_tag_integrity_dialog(self._parent, inventory)
        if request is None:
            return False
        try:
            plan = self._controller.prepare(
                action=request.action,
                scope=request.scope,
                source_tag=request.source_tag,
                target_tag=request.target_tag,
            )
        except (OSError, TypeError, ValueError) as error:
            show_tag_error(self._parent, "Cannot prepare tag operation", str(error))
            return False
        if not confirm_tag_mutation(self._parent, plan):
            return False
        result = self._controller.apply(plan)
        show_tag_result(self._parent, result)
        return result.succeeded
