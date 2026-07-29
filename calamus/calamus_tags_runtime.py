"""Thin GTK coordinator for the persistent W94 Tags Research client."""
from __future__ import annotations

from typing import Callable

from calamus_tag_integrity import (
    TAG_ACTION_NORMALIZE_ALL,
    TAG_ACTION_REMOVE,
    TAG_ACTION_RENAME_MERGE,
)
from calamus_tag_integrity_controller import TagIntegrityController
from calamus_tag_integrity_dialogs import (
    confirm_tag_mutation,
    run_tag_target_dialog,
    show_tag_error,
    show_tag_result,
)
from calamus_tags_controller import TagsController
from calamus_tags_panel import build_tags_panel_view


class TagsRuntime:
    def __init__(
        self,
        parent,
        integrity_controller: TagIntegrityController,
        *,
        show_reference: Callable[[str], bool],
        show_source_note: Callable[[str], bool],
        show_scratchpad_entry: Callable[[str], bool],
    ) -> None:
        if not isinstance(integrity_controller, TagIntegrityController):
            raise TypeError("integrity_controller must be TagIntegrityController")
        callbacks = (show_reference, show_source_note, show_scratchpad_entry)
        if any(not callable(callback) for callback in callbacks):
            raise TypeError("Tags runtime callbacks must be callable")
        self._parent = parent
        self._view = build_tags_panel_view(
            self.on_open,
            self.on_rename,
            self.on_remove,
            self.on_normalize,
            self.on_refresh,
            self.on_show_all,
        )
        self._controller = TagsController(
            self._view,
            integrity_controller,
            show_reference=show_reference,
            show_source_note=show_source_note,
            show_scratchpad_entry=show_scratchpad_entry,
            on_error=lambda message: show_tag_error(parent, "Tags", message),
        )
        self._view.bind_controls(
            self._controller.set_query,
            self._controller.set_scope,
            self._controller.set_sort,
            self._controller.set_issues_only,
            self._controller.select_tag,
        )

    @property
    def widget(self):
        return self._view.widget

    @property
    def controller(self) -> TagsController:
        return self._controller

    def activate(self) -> bool:
        # Activation refreshes the derived projection only. The Tags client
        # deliberately does not steal focus; visual row selection is applied by
        # the concrete view from a cancellable post-map idle callback.
        return self._controller.activate()

    def show_issues(self) -> bool:
        return self._controller.show_issues()

    def on_refresh(self, *_):
        return self._controller.refresh()

    def on_show_all(self, *_):
        return self._controller.show_all_tags_az()

    def on_open(self, *_):
        return self._controller.open_selected_use()

    def on_rename(self, *_):
        item = self._controller.selected_item()
        if item is None:
            show_tag_error(self._parent, "Tags", "Select one tag before renaming it.")
            return False
        target = run_tag_target_dialog(self._parent, item, self._controller.inventory)
        if target is None:
            return False
        return self._prepare_confirm_apply(
            TAG_ACTION_RENAME_MERGE,
            source_tag=item.canonical,
            target_tag=target,
        )

    def on_remove(self, *_):
        item = self._controller.selected_item()
        if item is None:
            show_tag_error(self._parent, "Tags", "Select one tag before removing it.")
            return False
        return self._prepare_confirm_apply(
            TAG_ACTION_REMOVE,
            source_tag=item.canonical,
        )

    def on_normalize(self, *_):
        return self._prepare_confirm_apply(TAG_ACTION_NORMALIZE_ALL)

    def _prepare_confirm_apply(
        self,
        action: str,
        *,
        source_tag: str = "",
        target_tag: str = "",
    ) -> bool:
        try:
            plan = self._controller.prepare(
                action=action,
                source_tag=source_tag,
                target_tag=target_tag,
            )
        except (OSError, TypeError, ValueError) as error:
            show_tag_error(self._parent, "Cannot prepare tag operation", str(error))
            return False
        if not confirm_tag_mutation(self._parent, plan):
            return False
        result = self._controller.apply(plan)
        show_tag_result(self._parent, result)
        return result.succeeded
