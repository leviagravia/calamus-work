"""GTK-free transactional coordinator for W78 reference integrity commands."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from calamus_document_structure import DocumentStructure
from calamus_reference_integrity import (
    ReferenceMigrationPlan,
    ResearchCheckReport,
    plan_reference_key_migration,
    run_research_check,
)
from calamus_reference_store import (
    MarkdownReferenceStore,
    ReferenceLibrarySnapshot,
    ReferenceSaveResult,
)
from calamus_research_file import FileToken
from calamus_source_note_store import (
    MarkdownSourceNoteStore,
    SourceNoteSaveResult,
    SourceNoteSnapshot,
    source_notes_path,
)


class ReferenceStore(Protocol):
    def load(self) -> ReferenceLibrarySnapshot: ...
    def save(self, records, expected_token: FileToken, *, force: bool = False) -> ReferenceSaveResult: ...


class SourceNoteStore(Protocol):
    path: str
    def load(self) -> SourceNoteSnapshot: ...
    def save(self, notes, expected_token: FileToken, *, force: bool = False) -> SourceNoteSaveResult: ...


@dataclass(frozen=True)
class IntegrityCommandResult:
    status: str
    message: str = ""
    recovery_errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"success", "cancelled", "stale", "error", "recovery-required"}:
            raise ValueError("integrity command status is invalid")

    @property
    def succeeded(self) -> bool:
        return self.status == "success"


@dataclass(frozen=True)
class _LoadedContext:
    reference_snapshot: ReferenceLibrarySnapshot
    source_note_store: SourceNoteStore | None
    source_note_snapshot: SourceNoteSnapshot
    document_text: str
    document_structure: DocumentStructure


class ResearchIntegrityController:
    """Create fresh plans and apply them with conflict-aware compensation."""

    def __init__(
        self,
        *,
        reference_store: ReferenceStore | None = None,
        source_note_store_factory: Callable[[str], SourceNoteStore] = MarkdownSourceNoteStore,
        document_path_provider: Callable[[], str | None],
        document_text_provider: Callable[[], str],
        document_structure_provider: Callable[[], DocumentStructure],
        replace_document_text: Callable[[str, str], bool],
        refresh_references: Callable[[], None],
        refresh_source_notes: Callable[[], None],
    ) -> None:
        callbacks = (
            source_note_store_factory,
            document_path_provider,
            document_text_provider,
            document_structure_provider,
            replace_document_text,
            refresh_references,
            refresh_source_notes,
        )
        if any(not callable(callback) for callback in callbacks):
            raise TypeError("research integrity callbacks must be callable")
        store = reference_store or MarkdownReferenceStore()
        if not hasattr(store, "load") or not hasattr(store, "save"):
            raise TypeError("reference_store must implement load and save")
        self._reference_store = store
        self._source_note_store_factory = source_note_store_factory
        self._document_path_provider = document_path_provider
        self._document_text_provider = document_text_provider
        self._document_structure_provider = document_structure_provider
        self._replace_document_text = replace_document_text
        self._refresh_references = refresh_references
        self._refresh_source_notes = refresh_source_notes
        self._prepared: tuple[ReferenceMigrationPlan, FileToken, FileToken] | None = None

    def prepare_migration(
        self,
        old_key: str,
        new_key: str,
        *,
        preserve_old_alias: bool = True,
    ) -> ReferenceMigrationPlan:
        context = self._load_context()
        plan = plan_reference_key_migration(
            context.reference_snapshot.records,
            context.document_text,
            context.source_note_snapshot.notes,
            old_key,
            new_key,
            preserve_old_alias=preserve_old_alias,
        )
        self._prepared = (
            plan,
            context.reference_snapshot.token,
            context.source_note_snapshot.token,
        )
        return plan

    def apply_migration(self, approved_plan: ReferenceMigrationPlan) -> IntegrityCommandResult:
        if not isinstance(approved_plan, ReferenceMigrationPlan):
            raise TypeError("approved_plan must be ReferenceMigrationPlan")
        prepared = self._prepared
        self._prepared = None
        if prepared is None or prepared[0] != approved_plan:
            return IntegrityCommandResult(
                "stale",
                "Impact preview is no longer current. Nothing was written.",
            )
        approved_reference_token, approved_source_token = prepared[1], prepared[2]
        try:
            context = self._load_context()
            if (
                context.reference_snapshot.token != approved_reference_token
                or context.source_note_snapshot.token != approved_source_token
            ):
                return IntegrityCommandResult(
                    "stale",
                    "References or Source Notes changed after impact preview. Nothing was written.",
                )
            fresh_plan = plan_reference_key_migration(
                context.reference_snapshot.records,
                context.document_text,
                context.source_note_snapshot.notes,
                approved_plan.impact.old_key,
                approved_plan.impact.new_key,
                preserve_old_alias=approved_plan.impact.preserved_alias,
            )
        except (OSError, TypeError, ValueError) as error:
            return IntegrityCommandResult("error", str(error))

        if fresh_plan != approved_plan:
            return IntegrityCommandResult(
                "stale",
                "References, the active document, or Source Notes changed after impact preview. Nothing was written.",
            )

        reference_result = self._reference_store.save(
            fresh_plan.candidate_records,
            context.reference_snapshot.token,
        )
        if not reference_result.saved:
            return IntegrityCommandResult(
                "stale" if reference_result.status == "conflict" else "error",
                reference_result.message or "Could not save References.",
            )

        note_result: SourceNoteSaveResult | None = None
        if fresh_plan.source_notes_changed:
            assert context.source_note_store is not None
            note_result = context.source_note_store.save(
                fresh_plan.source_notes_after,
                context.source_note_snapshot.token,
            )
            if not note_result.saved:
                recovery = self._rollback_references(
                    fresh_plan,
                    reference_result.token,
                )
                return self._failure_after_recovery(
                    note_result.message or "Could not save Source Notes.",
                    recovery,
                )

        # The buffer is an authority too: do not apply an approved plan to a new snapshot.
        if self._document_text_provider() != fresh_plan.document_before:
            recovery = self._rollback_persistent(
                fresh_plan,
                context.source_note_store,
                note_result.token if note_result is not None else None,
                reference_result.token,
            )
            return self._failure_after_recovery(
                "The active document changed after persistence began; migration was cancelled.",
                recovery,
                stale=True,
            )

        if fresh_plan.document_changed:
            changed = self._replace_document_text(
                fresh_plan.document_before,
                fresh_plan.document_after,
            )
            if not changed or self._document_text_provider() != fresh_plan.document_after:
                recovery_errors: list[str] = []
                current_text = self._document_text_provider()
                if current_text == fresh_plan.document_after:
                    if not self._replace_document_text(
                        fresh_plan.document_after,
                        fresh_plan.document_before,
                    ):
                        recovery_errors.append("Active document could not be restored automatically.")
                elif current_text != fresh_plan.document_before:
                    recovery_errors.append(
                        "Active document changed unexpectedly and was not overwritten during recovery."
                    )
                recovery_errors.extend(
                    self._rollback_persistent(
                        fresh_plan,
                        context.source_note_store,
                        note_result.token if note_result is not None else None,
                        reference_result.token,
                    )
                )
                return self._failure_after_recovery(
                    "The active document could not be updated through the canonical Undo gateway.",
                    tuple(recovery_errors),
                )

        self._refresh_references()
        self._refresh_source_notes()
        return IntegrityCommandResult(
            "success",
            f"Renamed {fresh_plan.impact.old_key} to {fresh_plan.impact.new_key}.",
        )

    def research_check(self) -> ResearchCheckReport:
        context = self._load_context()
        return run_research_check(
            context.reference_snapshot.records,
            context.document_text,
            context.source_note_snapshot.notes,
            context.document_structure,
        )

    def _load_context(self) -> _LoadedContext:
        reference_snapshot = self._reference_store.load()
        if reference_snapshot.diagnostics:
            detail = "; ".join(item.message for item in reference_snapshot.diagnostics[:8])
            raise ValueError("References contains blocking diagnostics: " + detail)

        source_store: SourceNoteStore | None = None
        source_snapshot = SourceNoteSnapshot((), FileToken(False), ())
        sidecar = source_notes_path(self._document_path_provider())
        if sidecar is not None:
            source_store = self._source_note_store_factory(sidecar)
            source_snapshot = source_store.load()
            if source_snapshot.diagnostics:
                detail = "; ".join(item.message for item in source_snapshot.diagnostics[:8])
                raise ValueError("Source Notes contains blocking diagnostics: " + detail)

        document_text = self._document_text_provider()
        if not isinstance(document_text, str):
            raise TypeError("document_text_provider must return str")
        structure = self._document_structure_provider()
        if not isinstance(structure, DocumentStructure):
            raise TypeError("document_structure_provider must return DocumentStructure")
        return _LoadedContext(
            reference_snapshot,
            source_store,
            source_snapshot,
            document_text,
            structure,
        )

    def _rollback_references(
        self,
        plan: ReferenceMigrationPlan,
        expected_token: FileToken,
    ) -> tuple[str, ...]:
        result = self._reference_store.save(plan.original_records, expected_token)
        if result.saved:
            return ()
        return (result.message or "References rollback failed.",)

    def _rollback_persistent(
        self,
        plan: ReferenceMigrationPlan,
        source_store: SourceNoteStore | None,
        source_expected_token: FileToken | None,
        reference_expected_token: FileToken,
    ) -> tuple[str, ...]:
        errors: list[str] = []
        if source_expected_token is not None:
            assert source_store is not None
            result = source_store.save(plan.source_notes_before, source_expected_token)
            if not result.saved:
                errors.append(result.message or "Source Notes rollback failed.")
        errors.extend(self._rollback_references(plan, reference_expected_token))
        self._refresh_references()
        self._refresh_source_notes()
        return tuple(errors)

    @staticmethod
    def _failure_after_recovery(
        message: str,
        recovery_errors: tuple[str, ...],
        *,
        stale: bool = False,
    ) -> IntegrityCommandResult:
        if recovery_errors:
            return IntegrityCommandResult(
                "recovery-required",
                message,
                recovery_errors,
            )
        return IntegrityCommandResult("stale" if stale else "error", message)
