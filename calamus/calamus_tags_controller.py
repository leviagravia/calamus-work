"""GTK-free controller for the derived Calamus Tags Research client."""
from __future__ import annotations

from typing import Any, Callable, Protocol

from calamus_tag_integrity import (
    TAG_SCOPE_ALL,
    TAG_SCOPE_REFERENCES,
    TAG_SCOPE_SCRATCHPAD,
    TAG_SCOPE_SOURCE_NOTES,
    TagInventory,
    TagInventoryItem,
    TagMutationPlan,
    TagUse,
)
from calamus_tag_integrity_controller import TagCommandResult, TagIntegrityController

TAG_SORT_NAME = "name"
TAG_SORT_USAGE = "usage"
TAG_PANEL_SORTS = (TAG_SORT_NAME, TAG_SORT_USAGE)

TAG_PANEL_SCOPES = (
    TAG_SCOPE_ALL,
    TAG_SCOPE_REFERENCES,
    TAG_SCOPE_SOURCE_NOTES,
    TAG_SCOPE_SCRATCHPAD,
)


class TagsView(Protocol):
    """The minimal view surface consumed by :class:`TagsController`.

    GTK lifecycle affordances such as focus and map handling intentionally do
    not belong here.  They are owned by ``TagsRuntime`` and the concrete panel
    adapter, so a lifecycle refactor cannot leave a stale controller contract.
    """

    @property
    def widget(self) -> Any: ...
    def render_tags(
        self,
        items: tuple[TagInventoryItem, ...],
        selected_identity: str | None,
        status: str,
    ) -> None: ...
    def render_uses(
        self,
        uses: tuple[TagUse, ...],
        selected_index: int | None,
        status: str,
    ) -> None: ...
    def selected_tag_identity(self) -> str | None: ...
    def selected_use(self) -> TagUse | None: ...
    def set_query(self, value: str) -> None: ...
    def set_scope(self, value: str) -> None: ...
    def set_issues_only(self, active: bool) -> None: ...
    def set_sort(self, value: str) -> None: ...


TAGS_VIEW_REQUIRED_MEMBERS = (
    "widget",
    "render_tags",
    "render_uses",
    "selected_tag_identity",
    "selected_use",
    "set_query",
    "set_scope",
    "set_issues_only",
    "set_sort",
)


class TagsController:
    """Maintain one transient projection over existing Markdown tag fields."""

    def __init__(
        self,
        view: TagsView,
        integrity_controller: TagIntegrityController,
        *,
        show_reference: Callable[[str], bool],
        show_source_note: Callable[[str], bool],
        show_scratchpad_entry: Callable[[str], bool],
        on_error: Callable[[str], None],
    ) -> None:
        missing = tuple(
            name for name in TAGS_VIEW_REQUIRED_MEMBERS
            if not hasattr(view, name)
        )
        if missing:
            raise TypeError(
                "view must implement TagsView; missing: " + ", ".join(missing)
            )
        if not isinstance(integrity_controller, TagIntegrityController):
            raise TypeError("integrity_controller must be TagIntegrityController")
        callbacks = (show_reference, show_source_note, show_scratchpad_entry, on_error)
        if any(not callable(callback) for callback in callbacks):
            raise TypeError("Tags callbacks must be callable")
        self._view = view
        self._integrity = integrity_controller
        self._show_reference = show_reference
        self._show_source_note = show_source_note
        self._show_scratchpad_entry = show_scratchpad_entry
        self._on_error = on_error
        self._inventory = TagInventory((), TAG_SCOPE_ALL)
        self._visible: tuple[TagInventoryItem, ...] = ()
        self._query = ""
        self._scope = TAG_SCOPE_ALL
        self._issues_only = False
        self._sort = TAG_SORT_NAME

    @property
    def widget(self) -> Any:
        return self._view.widget

    @property
    def scope(self) -> str:
        return self._scope

    @property
    def issues_only(self) -> bool:
        return self._issues_only

    @property
    def sort(self) -> str:
        return self._sort

    @property
    def inventory(self) -> TagInventory:
        return self._inventory

    @property
    def visible_items(self) -> tuple[TagInventoryItem, ...]:
        return self._visible

    def activate(self) -> bool:
        # Activation renders the projection only. Focus/reveal is a GTK
        # lifecycle concern owned by TagsRuntime/TagsPanelViewAdapter.
        return self.refresh()

    def refresh(self) -> bool:
        selected = self._view.selected_tag_identity()
        try:
            self._inventory = self._integrity.inventory(scope=self._scope)
        except (OSError, TypeError, ValueError) as error:
            self._inventory = TagInventory((), self._scope)
            self._visible = ()
            self._view.render_tags((), None, "Tags could not be loaded.")
            self._view.render_uses((), None, "No tag selected.")
            self._on_error(str(error))
            return False
        self._render(selected)
        return True

    def set_query(self, query: str) -> tuple[TagInventoryItem, ...]:
        self._query = query if isinstance(query, str) else ""
        self._render(self._view.selected_tag_identity())
        return self._visible

    def set_scope(self, scope: str) -> bool:
        if scope not in TAG_PANEL_SCOPES:
            scope = TAG_SCOPE_ALL
        if scope == self._scope:
            return self.refresh()
        self._scope = scope
        return self.refresh()

    def set_sort(self, value: str) -> tuple[TagInventoryItem, ...]:
        self._sort = value if value in TAG_PANEL_SORTS else TAG_SORT_NAME
        self._view.set_sort(self._sort)
        self._render(self._view.selected_tag_identity())
        return self._visible

    def set_issues_only(self, active: bool) -> tuple[TagInventoryItem, ...]:
        self._issues_only = bool(active)
        self._view.set_issues_only(self._issues_only)
        self._render(self._view.selected_tag_identity())
        return self._visible

    def show_issues(self) -> bool:
        self._issues_only = True
        self._view.set_issues_only(True)
        return self.refresh()

    def show_all_tags_az(self) -> bool:
        """Reset presentation state to the complete A–Z tag inventory."""
        self._query = ""
        self._scope = TAG_SCOPE_ALL
        self._issues_only = False
        self._sort = TAG_SORT_NAME
        self._view.set_query("")
        self._view.set_scope(TAG_SCOPE_ALL)
        self._view.set_issues_only(False)
        self._view.set_sort(TAG_SORT_NAME)
        return self.refresh()

    def select_tag(self, identity: str | None) -> None:
        item = self._find_visible(identity)
        uses = item.uses if item is not None else ()
        label = f"{len(uses)} explicit use(s)." if item is not None else "No tag selected."
        self._view.render_uses(uses, 0 if uses else None, label)

    def selected_item(self) -> TagInventoryItem | None:
        return self._find_visible(self._view.selected_tag_identity())

    def selected_use(self) -> TagUse | None:
        return self._view.selected_use()

    def open_selected_use(self) -> bool:
        use = self.selected_use()
        if use is None:
            return False
        try:
            if use.authority == TAG_SCOPE_REFERENCES:
                return bool(self._show_reference(use.owner_id))
            if use.authority == TAG_SCOPE_SOURCE_NOTES:
                return bool(self._show_source_note(use.owner_id))
            if use.authority == TAG_SCOPE_SCRATCHPAD:
                return bool(self._show_scratchpad_entry(use.owner_id))
        except (OSError, TypeError, ValueError) as error:
            self._on_error(str(error))
            return False
        self._on_error("Selected tag use has an unsupported authority.")
        return False

    def prepare(
        self,
        *,
        action: str,
        source_tag: str = "",
        target_tag: str = "",
    ) -> TagMutationPlan:
        return self._integrity.prepare(
            action=action,
            scope=self._scope,
            source_tag=source_tag,
            target_tag=target_tag,
        )

    def apply(self, plan: TagMutationPlan) -> TagCommandResult:
        result = self._integrity.apply(plan)
        if result.succeeded:
            self.refresh()
        return result

    def _render(self, preferred_identity: str | None) -> None:
        needle = self._query.strip().casefold()
        visible: list[TagInventoryItem] = []
        for item in self._inventory.items:
            if self._issues_only and not item.needs_normalization:
                continue
            if needle and needle not in self._item_search_text(item):
                continue
            visible.append(item)
        visible.sort(key=lambda item: self._visible_sort_key(item, needle))
        self._visible = tuple(visible)
        selected = preferred_identity if self._find_visible(preferred_identity) is not None else None
        if selected is None and self._visible:
            selected = self._visible[0].identity
        status = self._status_text()
        self._view.render_tags(self._visible, selected, status)
        self.select_tag(selected)


    def _visible_sort_key(self, item: TagInventoryItem, needle: str) -> tuple[object, ...]:
        if needle:
            names = tuple(value.casefold() for value in (item.canonical, *item.variants))
            if needle in names:
                rank = 0
            elif any(value.startswith(needle) for value in names):
                rank = 1
            elif any(needle in value for value in names):
                rank = 2
            else:
                rank = 3
        else:
            rank = 0
        if self._sort == TAG_SORT_USAGE:
            return (rank, -item.total_count, item.canonical.casefold(), item.canonical)
        return (rank, item.canonical.casefold(), item.canonical)

    def _find_visible(self, identity: str | None) -> TagInventoryItem | None:
        if not isinstance(identity, str) or not identity:
            return None
        return next((item for item in self._visible if item.identity == identity), None)

    @staticmethod
    def _item_search_text(item: TagInventoryItem) -> str:
        parts = [item.canonical, *item.variants]
        for use in item.uses:
            parts.extend((use.authority, use.owner_id, use.owner_label, use.variant))
        return "\n".join(parts).casefold()

    def _status_text(self) -> str:
        total = len(self._inventory.items)
        visible = len(self._visible)
        issues = self._inventory.issue_count
        filtered = bool(self._query.strip() or self._issues_only)
        scope = {
            TAG_SCOPE_ALL: "all authorities",
            TAG_SCOPE_REFERENCES: "References",
            TAG_SCOPE_SOURCE_NOTES: "Source Notes",
            TAG_SCOPE_SCRATCHPAD: "Scratchpad",
        }.get(self._scope, "the selected scope")

        if not filtered and self._sort == TAG_SORT_NAME:
            base = f"{total} tags — All tags A–Z ({scope})"
        elif not filtered:
            base = f"{total} tags — Most used first ({scope})"
        else:
            base = f"{visible} of {total} tags ({scope})"
        if issues:
            return f"{base}; {issues} variant group(s) need attention."
        return f"{base}; no spelling variants need attention."
