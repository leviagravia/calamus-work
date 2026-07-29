"""GTK-free transactional coordinator for Calamus tag maintenance.

W94 extends the published W86 transaction from References + Source Notes to the
three canonical tag-bearing Markdown authorities: References, current Source
Notes and current Scratchpad.  The controller still owns no tag database or
persistent index.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from calamus_reference_store import (
    MarkdownReferenceStore,
    ReferenceLibrarySnapshot,
    ReferenceSaveResult,
)
from calamus_research_file import FileToken
from calamus_scratchpad_store import (
    MarkdownScratchpadStore,
    ScratchpadSaveResult,
    ScratchpadSnapshot,
    scratchpad_path,
)
from calamus_source_note_store import (
    MarkdownSourceNoteStore,
    SourceNoteSaveResult,
    SourceNoteSnapshot,
    source_notes_path,
)
from calamus_source_notes import now_iso
from calamus_tag_integrity import (
    TAG_SCOPE_BOTH,
    TAG_SCOPE_REFERENCES,
    TAG_SCOPE_SCRATCHPAD,
    TAG_SCOPE_SOURCE_NOTES,
    TagInventory,
    TagMutationPlan,
    authority_in_scope,
    build_tag_inventory,
    plan_tag_mutation,
)


class ReferenceStore(Protocol):
    def load(self) -> ReferenceLibrarySnapshot: ...
    def save(self, records, expected_token: FileToken, *, force: bool = False) -> ReferenceSaveResult: ...


class SourceNoteStore(Protocol):
    path: str
    def load(self) -> SourceNoteSnapshot: ...
    def save(self, notes, expected_token: FileToken, *, force: bool = False) -> SourceNoteSaveResult: ...


class ScratchpadStore(Protocol):
    path: str
    def load(self) -> ScratchpadSnapshot: ...
    def save(self, entries, expected_token: FileToken, *, force: bool = False) -> ScratchpadSaveResult: ...


@dataclass(frozen=True)
class TagCommandResult:
    status: str
    message: str = ""
    recovery_errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"success", "stale", "error", "recovery-required"}:
            raise ValueError("tag command status is invalid")

    @property
    def succeeded(self) -> bool:
        return self.status == "success"


@dataclass(frozen=True)
class _TagContext:
    reference_snapshot: ReferenceLibrarySnapshot
    source_note_store: SourceNoteStore | None
    source_note_snapshot: SourceNoteSnapshot
    scratchpad_store: ScratchpadStore | None
    scratchpad_snapshot: ScratchpadSnapshot


@dataclass(frozen=True)
class _PreparedTagPlan:
    plan: TagMutationPlan
    reference_token: FileToken
    source_note_token: FileToken
    scratchpad_token: FileToken


class TagIntegrityController:
    """Build fresh tag projections and apply approved plans with compensation."""

    def __init__(
        self,
        *,
        reference_store: ReferenceStore | None = None,
        source_note_store_factory: Callable[[str], SourceNoteStore] = MarkdownSourceNoteStore,
        scratchpad_store_factory: Callable[[str], ScratchpadStore] = MarkdownScratchpadStore,
        document_path_provider: Callable[[], str | None],
        refresh_references: Callable[[], None],
        refresh_source_notes: Callable[[], None],
        refresh_scratchpad: Callable[[], None] | None = None,
        now_provider: Callable[[], str] = now_iso,
    ) -> None:
        callbacks = (
            source_note_store_factory,
            scratchpad_store_factory,
            document_path_provider,
            refresh_references,
            refresh_source_notes,
            now_provider,
        )
        if any(not callable(callback) for callback in callbacks):
            raise TypeError("tag integrity callbacks must be callable")
        if refresh_scratchpad is not None and not callable(refresh_scratchpad):
            raise TypeError("refresh_scratchpad must be callable")
        store = reference_store or MarkdownReferenceStore()
        if not hasattr(store, "load") or not hasattr(store, "save"):
            raise TypeError("reference_store must implement load and save")
        self._reference_store = store
        self._source_note_store_factory = source_note_store_factory
        self._scratchpad_store_factory = scratchpad_store_factory
        self._document_path_provider = document_path_provider
        self._refresh_references = refresh_references
        self._refresh_source_notes = refresh_source_notes
        self._refresh_scratchpad = refresh_scratchpad or (lambda: None)
        self._now_provider = now_provider
        self._prepared: _PreparedTagPlan | None = None

    def inventory(self, *, scope: str = TAG_SCOPE_BOTH) -> TagInventory:
        context = self._load_context(scope=scope)
        return build_tag_inventory(
            context.reference_snapshot.records,
            context.source_note_snapshot.notes,
            context.scratchpad_snapshot.entries,
            scope=scope,
        )

    def prepare(
        self,
        *,
        action: str,
        scope: str = TAG_SCOPE_BOTH,
        source_tag: str = "",
        target_tag: str = "",
    ) -> TagMutationPlan:
        context = self._load_context(scope=scope)
        stamp = self._now_provider()
        if not isinstance(stamp, str):
            raise TypeError("now_provider must return str")
        plan = plan_tag_mutation(
            context.reference_snapshot.records,
            context.source_note_snapshot.notes,
            context.scratchpad_snapshot.entries,
            action=action,
            scope=scope,
            source_tag=source_tag,
            target_tag=target_tag,
            modified_stamp=stamp,
        )
        self._prepared = _PreparedTagPlan(
            plan,
            context.reference_snapshot.token,
            context.source_note_snapshot.token,
            context.scratchpad_snapshot.token,
        )
        return plan

    def apply(self, approved_plan: TagMutationPlan) -> TagCommandResult:
        if not isinstance(approved_plan, TagMutationPlan):
            raise TypeError("approved_plan must be TagMutationPlan")
        prepared = self._prepared
        self._prepared = None
        if prepared is None or prepared.plan != approved_plan:
            return TagCommandResult(
                "stale",
                "Impact preview is no longer current. Nothing was written.",
            )

        try:
            context = self._load_context(scope=approved_plan.impact.scope)
            if not self._tokens_are_current(prepared, context, approved_plan.impact.scope):
                return TagCommandResult(
                    "stale",
                    "A selected Markdown authority changed after impact preview. Nothing was written.",
                )
            impact = approved_plan.impact
            fresh_plan = plan_tag_mutation(
                context.reference_snapshot.records,
                context.source_note_snapshot.notes,
                context.scratchpad_snapshot.entries,
                action=impact.action,
                scope=impact.scope,
                source_tag=impact.source_display,
                target_tag=impact.target_display,
                modified_stamp=approved_plan.modified_stamp,
            )
        except (OSError, TypeError, ValueError) as error:
            return TagCommandResult("error", str(error))

        if fresh_plan != approved_plan:
            return TagCommandResult(
                "stale",
                "A selected Markdown authority changed after impact preview. Nothing was written.",
            )

        reference_result: ReferenceSaveResult | None = None
        source_result: SourceNoteSaveResult | None = None
        scratch_result: ScratchpadSaveResult | None = None

        if fresh_plan.references_changed:
            reference_result = self._reference_store.save(
                fresh_plan.references_after,
                context.reference_snapshot.token,
            )
            if not reference_result.saved:
                return TagCommandResult(
                    "stale" if reference_result.status == "conflict" else "error",
                    reference_result.message or "Could not save References.",
                )

        if fresh_plan.source_notes_changed:
            if context.source_note_store is None:
                recovery = self._rollback_references(
                    fresh_plan,
                    reference_result.token if reference_result is not None else None,
                )
                return self._failure_after_recovery(
                    "The active document has no Source Notes sidecar.",
                    recovery,
                )
            source_result = context.source_note_store.save(
                fresh_plan.source_notes_after,
                context.source_note_snapshot.token,
            )
            if not source_result.saved:
                recovery = self._rollback_references(
                    fresh_plan,
                    reference_result.token if reference_result is not None else None,
                )
                return self._failure_after_recovery(
                    source_result.message or "Could not save Source Notes.",
                    recovery,
                    stale=source_result.status == "conflict",
                )

        if fresh_plan.scratchpad_changed:
            if context.scratchpad_store is None:
                recovery = self._rollback_after_scratchpad_failure(
                    fresh_plan,
                    context,
                    reference_result,
                    source_result,
                )
                return self._failure_after_recovery(
                    "The active document has no Scratchpad sidecar.",
                    recovery,
                )
            scratch_result = context.scratchpad_store.save(
                fresh_plan.scratchpad_after,
                context.scratchpad_snapshot.token,
            )
            if not scratch_result.saved:
                recovery = self._rollback_after_scratchpad_failure(
                    fresh_plan,
                    context,
                    reference_result,
                    source_result,
                )
                return self._failure_after_recovery(
                    scratch_result.message or "Could not save Scratchpad.",
                    recovery,
                    stale=scratch_result.status == "conflict",
                )

        self._refresh_references()
        self._refresh_source_notes()
        self._refresh_scratchpad()
        return TagCommandResult("success", self._success_message(fresh_plan))

    def _load_context(self, *, scope: str = TAG_SCOPE_BOTH) -> _TagContext:
        reference_snapshot = self._reference_store.load()
        if authority_in_scope(TAG_SCOPE_REFERENCES, scope) and reference_snapshot.diagnostics:
            detail = "; ".join(item.message for item in reference_snapshot.diagnostics[:8])
            raise ValueError("References contains blocking diagnostics: " + detail)

        document_path = self._document_path_provider()

        source_store: SourceNoteStore | None = None
        source_snapshot = SourceNoteSnapshot((), FileToken(False), ())
        source_sidecar = source_notes_path(document_path)
        if source_sidecar is not None:
            source_store = self._source_note_store_factory(source_sidecar)
            source_snapshot = source_store.load()
            if authority_in_scope(TAG_SCOPE_SOURCE_NOTES, scope) and source_snapshot.diagnostics:
                detail = "; ".join(item.message for item in source_snapshot.diagnostics[:8])
                raise ValueError("Source Notes contains blocking diagnostics: " + detail)

        scratch_store: ScratchpadStore | None = None
        scratch_snapshot = ScratchpadSnapshot((), FileToken(False), ())
        scratch_sidecar = scratchpad_path(document_path)
        if scratch_sidecar is not None:
            scratch_store = self._scratchpad_store_factory(scratch_sidecar)
            scratch_snapshot = scratch_store.load()
            if authority_in_scope(TAG_SCOPE_SCRATCHPAD, scope) and scratch_snapshot.diagnostics:
                detail = "; ".join(item.message for item in scratch_snapshot.diagnostics[:8])
                raise ValueError("Scratchpad contains blocking diagnostics: " + detail)

        return _TagContext(
            reference_snapshot,
            source_store,
            source_snapshot,
            scratch_store,
            scratch_snapshot,
        )

    @staticmethod
    def _tokens_are_current(
        prepared: _PreparedTagPlan,
        context: _TagContext,
        scope: str,
    ) -> bool:
        checks: list[bool] = []
        if authority_in_scope(TAG_SCOPE_REFERENCES, scope):
            checks.append(context.reference_snapshot.token == prepared.reference_token)
        if authority_in_scope(TAG_SCOPE_SOURCE_NOTES, scope):
            checks.append(context.source_note_snapshot.token == prepared.source_note_token)
        if authority_in_scope(TAG_SCOPE_SCRATCHPAD, scope):
            checks.append(context.scratchpad_snapshot.token == prepared.scratchpad_token)
        return all(checks)

    def _rollback_after_scratchpad_failure(
        self,
        plan: TagMutationPlan,
        context: _TagContext,
        reference_result: ReferenceSaveResult | None,
        source_result: SourceNoteSaveResult | None,
    ) -> tuple[str, ...]:
        errors: list[str] = []
        if plan.source_notes_changed and context.source_note_store is not None and source_result is not None:
            result = context.source_note_store.save(plan.source_notes_before, source_result.token)
            if not result.saved:
                errors.append(result.message or "Source Notes rollback failed.")
        errors.extend(
            self._rollback_references(
                plan,
                reference_result.token if reference_result is not None else None,
            )
        )
        return tuple(errors)

    def _rollback_references(
        self,
        plan: TagMutationPlan,
        expected_token: FileToken | None,
    ) -> tuple[str, ...]:
        if not plan.references_changed or expected_token is None:
            return ()
        result = self._reference_store.save(plan.references_before, expected_token)
        if result.saved:
            return ()
        return (result.message or "References rollback failed.",)

    @staticmethod
    def _failure_after_recovery(
        message: str,
        recovery_errors: tuple[str, ...],
        *,
        stale: bool = False,
    ) -> TagCommandResult:
        if recovery_errors:
            return TagCommandResult("recovery-required", message, recovery_errors)
        return TagCommandResult("stale" if stale else "error", message)

    @staticmethod
    def _success_message(plan: TagMutationPlan) -> str:
        impact = plan.impact
        counts = (
            f"{impact.reference_records_changed} reference(s), "
            f"{impact.source_notes_changed} source note(s), "
            f"{impact.scratchpad_entries_changed} Scratchpad item(s)"
        )
        if impact.action == "rename-merge":
            return f"Updated tag {impact.source_display} to {impact.target_display}: {counts}."
        if impact.action == "remove":
            return f"Removed tag {impact.source_display}: {counts}."
        return f"Normalized tags in {counts}."
