"""Pure, filesystem-free tag inventory and mutation planning for Calamus Research.

Tags remain embedded in the canonical Markdown authorities: the global
``references.md`` library and the active document Source Notes and Scratchpad
sidecars.  This module derives a transient logical inventory, deterministic
presentation colours, exact uses and immutable mutation plans.  It never reads
or writes files and never owns persistent state.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import unicodedata
from typing import Any, Iterable

from calamus_references import ReferenceRecord
from calamus_scratchpad import ScratchpadEntry
from calamus_source_notes import SourceNote

# ``both`` is retained for the published W86 contract: References + Source
# Notes.  W94 adds ``all`` and ``scratchpad`` without silently changing the
# meaning of historical callers.
TAG_SCOPE_ALL = "all"
TAG_SCOPE_BOTH = "both"
TAG_SCOPE_REFERENCES = "references"
TAG_SCOPE_SOURCE_NOTES = "source-notes"
TAG_SCOPE_SCRATCHPAD = "scratchpad"
TAG_SCOPES = (
    TAG_SCOPE_ALL,
    TAG_SCOPE_BOTH,
    TAG_SCOPE_REFERENCES,
    TAG_SCOPE_SOURCE_NOTES,
    TAG_SCOPE_SCRATCHPAD,
)

TAG_ACTION_RENAME_MERGE = "rename-merge"
TAG_ACTION_REMOVE = "remove"
TAG_ACTION_NORMALIZE_ALL = "normalize-all"
TAG_ACTIONS = (TAG_ACTION_RENAME_MERGE, TAG_ACTION_REMOVE, TAG_ACTION_NORMALIZE_ALL)

TAG_RENAME_MODE_RENAME = "rename"
TAG_RENAME_MODE_MERGE = "merge"
TAG_RENAME_MODE_NORMALIZE = "normalize"
TAG_RENAME_MODES = (
    TAG_RENAME_MODE_RENAME,
    TAG_RENAME_MODE_MERGE,
    TAG_RENAME_MODE_NORMALIZE,
)

# Fixed palette: deterministic, theme-independent presentation only. Colours
# are not persisted and do not become another Research authority.
_TAG_PALETTE = (
    "#8B3A3A", "#9A5A16", "#6B6B18", "#2E6B3E",
    "#1D6B68", "#245F8F", "#4E4B8F", "#70458B",
    "#8A3F70", "#7B4B2A", "#476A7A", "#5C5C5C",
)


def clean_tag_display(value: Any) -> str:
    """Return NFC text with all Unicode whitespace runs collapsed to one space."""
    if not isinstance(value, str):
        return ""
    return unicodedata.normalize("NFC", " ".join(value.split()))


def tag_identity(value: Any) -> str:
    """Return the logical, case-insensitive identity used by tag tools."""
    return clean_tag_display(value).casefold()


def tag_color(identity: Any) -> str:
    """Return one stable derived swatch colour for a logical tag identity."""
    logical = tag_identity(identity)
    if not logical:
        return _TAG_PALETTE[-1]
    index = int.from_bytes(hashlib.sha256(logical.encode("utf-8")).digest()[:4], "big")
    return _TAG_PALETTE[index % len(_TAG_PALETTE)]


def _validate_scope(scope: str) -> str:
    if scope not in TAG_SCOPES:
        raise ValueError("tag scope is invalid")
    return scope


def authority_in_scope(authority: str, scope: str) -> bool:
    """Return whether one canonical tag authority participates in ``scope``."""
    _validate_scope(scope)
    if authority not in {
        TAG_SCOPE_REFERENCES,
        TAG_SCOPE_SOURCE_NOTES,
        TAG_SCOPE_SCRATCHPAD,
    }:
        raise ValueError("tag authority is invalid")
    if scope == TAG_SCOPE_ALL:
        return True
    if scope == TAG_SCOPE_BOTH:
        return authority in {TAG_SCOPE_REFERENCES, TAG_SCOPE_SOURCE_NOTES}
    return authority == scope


@dataclass(frozen=True, order=True)
class TagUse:
    authority: str
    owner_id: str
    owner_label: str
    variant: str

    def __post_init__(self) -> None:
        if self.authority not in {
            TAG_SCOPE_REFERENCES,
            TAG_SCOPE_SOURCE_NOTES,
            TAG_SCOPE_SCRATCHPAD,
        }:
            raise ValueError("tag use authority is invalid")
        if not all(isinstance(value, str) and value for value in (
            self.owner_id, self.owner_label, self.variant,
        )):
            raise ValueError("tag use fields must be non-empty strings")


@dataclass(frozen=True)
class TagInventoryItem:
    identity: str
    canonical: str
    variants: tuple[str, ...]
    uses: tuple[TagUse, ...]
    color: str
    needs_normalization: bool

    def __post_init__(self) -> None:
        if not self.identity or not self.canonical or not self.variants or not self.uses:
            raise ValueError("tag inventory item is incomplete")
        if tag_identity(self.canonical) != self.identity:
            raise ValueError("canonical tag does not match inventory identity")
        if any(tag_identity(variant) != self.identity for variant in self.variants):
            raise ValueError("tag variant does not match inventory identity")

    @property
    def reference_uses(self) -> tuple[TagUse, ...]:
        return tuple(use for use in self.uses if use.authority == TAG_SCOPE_REFERENCES)

    @property
    def source_note_uses(self) -> tuple[TagUse, ...]:
        return tuple(use for use in self.uses if use.authority == TAG_SCOPE_SOURCE_NOTES)

    @property
    def scratchpad_uses(self) -> tuple[TagUse, ...]:
        return tuple(use for use in self.uses if use.authority == TAG_SCOPE_SCRATCHPAD)

    @property
    def reference_count(self) -> int:
        return len(self.reference_uses)

    @property
    def source_note_count(self) -> int:
        return len(self.source_note_uses)

    @property
    def scratchpad_count(self) -> int:
        return len(self.scratchpad_uses)

    @property
    def total_count(self) -> int:
        return len(self.uses)


@dataclass(frozen=True)
class TagInventory:
    items: tuple[TagInventoryItem, ...]
    scope: str = TAG_SCOPE_BOTH

    def __post_init__(self) -> None:
        _validate_scope(self.scope)
        identities = [item.identity for item in self.items]
        if len(identities) != len(set(identities)):
            raise ValueError("tag inventory identities must be unique")

    @property
    def issue_count(self) -> int:
        return sum(item.needs_normalization for item in self.items)

    def get(self, value: str) -> TagInventoryItem | None:
        logical = tag_identity(value)
        return next((item for item in self.items if item.identity == logical), None)


@dataclass(frozen=True)
class TagMutationImpact:
    action: str
    scope: str
    source_identity: str = ""
    source_display: str = ""
    target_display: str = ""
    reference_records_changed: int = 0
    source_notes_changed: int = 0
    occurrences_changed: int = 0
    variants_merged: int = 0
    scratchpad_entries_changed: int = 0
    rename_mode: str = ""

    def __post_init__(self) -> None:
        if self.action not in TAG_ACTIONS:
            raise ValueError("tag action is invalid")
        _validate_scope(self.scope)
        if self.action == TAG_ACTION_RENAME_MERGE:
            if self.rename_mode not in TAG_RENAME_MODES:
                raise ValueError("rename/merge impact mode is invalid")
        elif self.rename_mode:
            raise ValueError("rename mode is only valid for rename/merge actions")
        for value in (
            self.reference_records_changed,
            self.source_notes_changed,
            self.scratchpad_entries_changed,
            self.occurrences_changed,
            self.variants_merged,
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError("tag impact counts must be non-negative integers")


@dataclass(frozen=True)
class TagMutationPlan:
    references_before: tuple[ReferenceRecord, ...]
    references_after: tuple[ReferenceRecord, ...]
    source_notes_before: tuple[SourceNote, ...]
    source_notes_after: tuple[SourceNote, ...]
    impact: TagMutationImpact
    modified_stamp: str = ""
    scratchpad_before: tuple[ScratchpadEntry, ...] = ()
    scratchpad_after: tuple[ScratchpadEntry, ...] = ()

    @property
    def references_changed(self) -> bool:
        return self.references_before != self.references_after

    @property
    def source_notes_changed(self) -> bool:
        return self.source_notes_before != self.source_notes_after

    @property
    def scratchpad_changed(self) -> bool:
        return self.scratchpad_before != self.scratchpad_after

    @property
    def changed(self) -> bool:
        return self.references_changed or self.source_notes_changed or self.scratchpad_changed


def _append_variant(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def build_tag_inventory(
    references: Iterable[ReferenceRecord],
    source_notes: Iterable[SourceNote],
    scratchpad_entries: Iterable[ScratchpadEntry] = (),
    *,
    scope: str = TAG_SCOPE_BOTH,
) -> TagInventory:
    """Build a deterministic first-use projection from Markdown authorities."""
    scope = _validate_scope(scope)
    records = tuple(references)
    notes = tuple(source_notes)
    entries = tuple(scratchpad_entries)
    if any(not isinstance(record, ReferenceRecord) for record in records):
        raise TypeError("references must contain ReferenceRecord values")
    if any(not isinstance(note, SourceNote) for note in notes):
        raise TypeError("source_notes must contain SourceNote values")
    if any(not isinstance(entry, ScratchpadEntry) for entry in entries):
        raise TypeError("scratchpad_entries must contain ScratchpadEntry values")

    order: list[str] = []
    canonical: dict[str, str] = {}
    variants: dict[str, list[str]] = {}
    uses: dict[str, list[TagUse]] = {}
    dirty: dict[str, bool] = {}

    def add(authority: str, owner_id: str, owner_label: str, raw: str) -> None:
        if not authority_in_scope(authority, scope):
            return
        cleaned = clean_tag_display(raw)
        logical = tag_identity(raw)
        if not cleaned or not logical:
            return
        if logical not in canonical:
            order.append(logical)
            canonical[logical] = cleaned
            variants[logical] = []
            uses[logical] = []
            dirty[logical] = False
        _append_variant(variants[logical], raw)
        uses[logical].append(TagUse(authority, owner_id, owner_label, raw))
        if raw != cleaned or cleaned != canonical[logical]:
            dirty[logical] = True

    for record in records:
        label = f"{record.key} — {record.title}"
        for raw in record.tags:
            add(TAG_SCOPE_REFERENCES, record.key, label, raw)
    for note in notes:
        label = f"{note.id} — {note.excerpt}"
        for raw in note.tags:
            add(TAG_SCOPE_SOURCE_NOTES, note.id, label, raw)
    for entry in entries:
        label = f"{entry.id} — {entry.title}"
        for raw in entry.tags:
            add(TAG_SCOPE_SCRATCHPAD, entry.id, label, raw)

    items = tuple(
        TagInventoryItem(
            identity=logical,
            canonical=canonical[logical],
            variants=tuple(variants[logical]),
            uses=tuple(uses[logical]),
            color=tag_color(logical),
            needs_normalization=dirty[logical] or len(variants[logical]) > 1,
        )
        for logical in order
    )
    return TagInventory(items, scope)


def _transform_tags(
    tags: tuple[str, ...],
    *,
    action: str,
    source_identity: str,
    target_display: str,
    normalize_map: dict[str, str],
) -> tuple[tuple[str, ...], int]:
    output: list[str] = []
    seen: set[str] = set()
    changed = 0
    target_identity = tag_identity(target_display)
    for raw in tags:
        logical = tag_identity(raw)
        affected = False
        replacement: str | None = raw
        if action == TAG_ACTION_REMOVE and logical == source_identity:
            replacement = None
            affected = True
        elif action == TAG_ACTION_RENAME_MERGE and logical == source_identity:
            replacement = target_display
            affected = True
        elif action == TAG_ACTION_NORMALIZE_ALL:
            replacement = normalize_map.get(logical, raw)
            affected = logical in normalize_map

        if replacement is None:
            changed += 1
            continue

        replacement_identity = tag_identity(replacement)
        if not replacement_identity:
            changed += 1
            continue

        duplicate = replacement_identity in seen
        if duplicate and (
            action == TAG_ACTION_NORMALIZE_ALL
            or (action == TAG_ACTION_RENAME_MERGE and replacement_identity == target_identity)
        ):
            changed += 1
            continue

        seen.add(replacement_identity)
        rendered = clean_tag_display(replacement) if affected else replacement
        output.append(rendered)
        if raw != rendered:
            changed += 1
    return tuple(output), changed


def plan_tag_mutation(
    references: Iterable[ReferenceRecord],
    source_notes: Iterable[SourceNote],
    scratchpad_entries: Iterable[ScratchpadEntry] = (),
    *,
    action: str,
    scope: str = TAG_SCOPE_BOTH,
    source_tag: str = "",
    target_tag: str = "",
    modified_stamp: str = "",
) -> TagMutationPlan:
    """Return one immutable, previewable mutation across selected authorities."""
    if action not in TAG_ACTIONS:
        raise ValueError("tag action is invalid")
    scope = _validate_scope(scope)
    records_before = tuple(references)
    notes_before = tuple(source_notes)
    scratch_before = tuple(scratchpad_entries)
    inventory = build_tag_inventory(
        records_before,
        notes_before,
        scratch_before,
        scope=scope,
    )

    source_identity = ""
    source_display = ""
    target_display = ""
    affected_variants = 0
    normalize_map: dict[str, str] = {}

    if action in {TAG_ACTION_RENAME_MERGE, TAG_ACTION_REMOVE}:
        source_identity = tag_identity(source_tag)
        item = inventory.get(source_tag)
        if not source_identity or item is None:
            raise ValueError("selected tag is not available in the requested scope")
        source_display = item.canonical
        affected_variants = len(item.variants)
        if action == TAG_ACTION_RENAME_MERGE:
            target_display = clean_tag_display(target_tag)
            if not target_display:
                raise ValueError("target tag is required")
            target_identity = tag_identity(target_display)
            target_item = inventory.get(target_display)
            if target_identity == source_identity:
                rename_mode = TAG_RENAME_MODE_NORMALIZE
            elif target_item is not None:
                rename_mode = TAG_RENAME_MODE_MERGE
            else:
                rename_mode = TAG_RENAME_MODE_RENAME
        else:
            rename_mode = ""
    else:
        rename_mode = ""
        normalize_map = {
            item.identity: item.canonical
            for item in inventory.items
            if item.needs_normalization
        }
        affected_variants = sum(max(0, len(item.variants) - 1) for item in inventory.items)
        if not normalize_map:
            raise ValueError("no tag normalization is required")

    records_after: list[ReferenceRecord] = []
    notes_after: list[SourceNote] = []
    scratch_after: list[ScratchpadEntry] = []
    record_changes = 0
    note_changes = 0
    scratch_changes = 0
    occurrence_changes = 0

    for record in records_before:
        if not authority_in_scope(TAG_SCOPE_REFERENCES, scope):
            records_after.append(record)
            continue
        tags, changed = _transform_tags(
            record.tags,
            action=action,
            source_identity=source_identity,
            target_display=target_display,
            normalize_map=normalize_map,
        )
        if tags != record.tags:
            record_changes += 1
            occurrence_changes += changed
            records_after.append(replace(record, tags=tags))
        else:
            records_after.append(record)

    for note in notes_before:
        if not authority_in_scope(TAG_SCOPE_SOURCE_NOTES, scope):
            notes_after.append(note)
            continue
        tags, changed = _transform_tags(
            note.tags,
            action=action,
            source_identity=source_identity,
            target_display=target_display,
            normalize_map=normalize_map,
        )
        if tags != note.tags:
            note_changes += 1
            occurrence_changes += changed
            changes: dict[str, Any] = {"tags": tags}
            if modified_stamp:
                changes["modified"] = modified_stamp
            notes_after.append(replace(note, **changes))
        else:
            notes_after.append(note)

    for entry in scratch_before:
        if not authority_in_scope(TAG_SCOPE_SCRATCHPAD, scope):
            scratch_after.append(entry)
            continue
        tags, changed = _transform_tags(
            entry.tags,
            action=action,
            source_identity=source_identity,
            target_display=target_display,
            normalize_map=normalize_map,
        )
        if tags != entry.tags:
            scratch_changes += 1
            occurrence_changes += changed
            changes = {"tags": tags}
            if modified_stamp:
                changes["updated"] = modified_stamp
            scratch_after.append(replace(entry, **changes))
        else:
            scratch_after.append(entry)

    plan = TagMutationPlan(
        references_before=records_before,
        references_after=tuple(records_after),
        source_notes_before=notes_before,
        source_notes_after=tuple(notes_after),
        scratchpad_before=scratch_before,
        scratchpad_after=tuple(scratch_after),
        impact=TagMutationImpact(
            action=action,
            scope=scope,
            source_identity=source_identity,
            source_display=source_display,
            target_display=target_display,
            reference_records_changed=record_changes,
            source_notes_changed=note_changes,
            scratchpad_entries_changed=scratch_changes,
            occurrences_changed=occurrence_changes,
            variants_merged=affected_variants,
            rename_mode=rename_mode,
        ),
        modified_stamp=modified_stamp,
    )
    if not plan.changed:
        raise ValueError("tag operation would not change the selected authorities")
    return plan
