"""GTK-free transient decision state for BibTeX/BibLaTeX imports.

The session is a presentation coordinator only. ``references.md`` remains the
sole bibliographic authority and no decision is persisted until the controller
revalidates and commits an immutable import plan.
"""
from __future__ import annotations

from dataclasses import dataclass

from calamus_bibtex import (
    ACTION_IMPORT,
    ACTION_SKIP,
    BibImportDecision,
    BibImportItem,
    BibImportPreview,
    COLLISION_ALIAS,
    COLLISION_INPUT,
    COLLISION_KEY,
    COLLISION_PROBABLE,
)

_AMBIGUOUS_COLLISIONS = frozenset((
    COLLISION_ALIAS,
    COLLISION_INPUT,
    COLLISION_KEY,
    COLLISION_PROBABLE,
))


@dataclass(frozen=True)
class BibImportSessionRow:
    """Read-only state projected to one UI row."""

    item: BibImportItem
    action: str | None

    @property
    def resolved(self) -> bool:
        return self.action is not None

    @property
    def action_label_key(self) -> str:
        return self.action or "unresolved"


class BibImportSession:
    """Own per-entry decisions without owning GTK or persistence."""

    def __init__(self, preview: BibImportPreview) -> None:
        if not isinstance(preview, BibImportPreview):
            raise TypeError("preview must be BibImportPreview")
        self._preview = preview
        self._items = {item.index: item for item in preview.items}
        self._actions: dict[int, str | None] = {}
        for item in preview.items:
            if item.record is None:
                action: str | None = ACTION_SKIP
            elif item.collision in _AMBIGUOUS_COLLISIONS:
                action = None
            else:
                action = item.default_action
            self._actions[item.index] = action

    @property
    def preview(self) -> BibImportPreview:
        return self._preview

    def item(self, index: int) -> BibImportItem:
        try:
            return self._items[index]
        except KeyError as error:
            raise ValueError(f"unknown import item index: {index}") from error

    def row(self, index: int) -> BibImportSessionRow:
        return BibImportSessionRow(self.item(index), self._actions[index])

    def rows(self) -> tuple[BibImportSessionRow, ...]:
        return tuple(self.row(item.index) for item in self._preview.items)

    def action(self, index: int) -> str | None:
        self.item(index)
        return self._actions[index]

    def set_action(self, index: int, action: str) -> BibImportSessionRow:
        item = self.item(index)
        if action not in item.allowed_actions:
            raise ValueError(f"action {action!r} is not allowed for {item.source_key!r}")
        self._actions[index] = action
        return self.row(index)

    @property
    def unresolved_indices(self) -> tuple[int, ...]:
        return tuple(
            item.index for item in self._preview.items
            if self._actions[item.index] is None
        )

    @property
    def unresolved_count(self) -> int:
        return len(self.unresolved_indices)

    @property
    def can_review(self) -> bool:
        return self.unresolved_count == 0

    def decisions(self) -> tuple[BibImportDecision, ...]:
        if not self.can_review:
            keys = ", ".join(self.item(index).source_key for index in self.unresolved_indices)
            raise ValueError(f"collision decisions are unresolved: {keys}")
        return tuple(
            BibImportDecision(item.index, self._actions[item.index] or ACTION_SKIP)
            for item in self._preview.items
        )

    def count(self, action: str) -> int:
        return sum(value == action for value in self._actions.values())
