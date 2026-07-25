"""GTK-free W87 controller for safe BibTeX/BibLaTeX import and export."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable, Protocol, Sequence

from calamus_bibtex import (
    BIB_FORMATS,
    BibExportArtifact,
    BibImportDecision,
    BibImportPreview,
    BibImportProjection,
    apply_import_decisions,
    build_import_preview,
    export_references,
    parse_bibliography,
)
from calamus_reference_store import ReferenceLibrarySnapshot, ReferenceSaveResult
from calamus_research_file import FileToken, atomic_write_utf8, file_token
from calamus_references import ReferenceRecord

_MAX_IMPORT_BYTES = 8 * 1024 * 1024
_MAX_IMPORT_ENTRIES = 5000


class ReferenceStore(Protocol):
    path: str
    def load(self) -> ReferenceLibrarySnapshot: ...
    def save(self, records, expected_token: FileToken, *, force: bool = False) -> ReferenceSaveResult: ...


@dataclass(frozen=True)
class BibImportInspection:
    source_path: str
    source_token: FileToken
    reference_token: FileToken
    preview: BibImportPreview


@dataclass(frozen=True)
class BibImportPlan:
    source_path: str
    source_token: FileToken
    reference_token: FileToken
    preview: BibImportPreview
    decisions: tuple[BibImportDecision, ...]
    projection: BibImportProjection


@dataclass(frozen=True)
class BibImportResult:
    status: str
    message: str
    projection: BibImportProjection | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "imported"


@dataclass(frozen=True)
class BibExportPlan:
    format: str
    reference_token: FileToken
    artifact: BibExportArtifact


@dataclass(frozen=True)
class BibExportResult:
    status: str
    message: str
    path: str = ""
    artifact: BibExportArtifact | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "exported"


class BibtexController:
    def __init__(
        self,
        reference_store: ReferenceStore,
        *,
        refresh_references: Callable[[], None] = lambda: None,
        writer: Callable[[str, str], FileToken] = atomic_write_utf8,
    ) -> None:
        if not hasattr(reference_store, "load") or not hasattr(reference_store, "save"):
            raise TypeError("reference_store must implement load/save")
        if not callable(refresh_references) or not callable(writer):
            raise TypeError("controller callbacks must be callable")
        self._store = reference_store
        self._refresh_references = refresh_references
        self._writer = writer

    def inspect_import(self, source_path: str, format: str) -> BibImportInspection:
        path = self._validated_import_path(source_path)
        if format not in BIB_FORMATS:
            raise ValueError("Choose BibTeX or BibLaTeX.")
        source_token = file_token(path)
        text = self._read_import(path)
        library = parse_bibliography(text, format)
        if len(library.entries) > _MAX_IMPORT_ENTRIES:
            raise ValueError(f"Import is limited to {_MAX_IMPORT_ENTRIES} entries per operation.")
        snapshot = self._load_writable_references()
        preview = build_import_preview(library, snapshot.records)
        return BibImportInspection(path, source_token, snapshot.token, preview)

    def prepare_import(
        self,
        inspection: BibImportInspection,
        decisions: Sequence[BibImportDecision],
    ) -> BibImportPlan:
        if not isinstance(inspection, BibImportInspection):
            raise TypeError("inspection must be BibImportInspection")
        projection = apply_import_decisions(
            inspection.preview,
            self._records_for_token(inspection.reference_token),
            tuple(decisions),
        )
        if projection.imported + projection.replaced + projection.merged == 0:
            raise ValueError("The selected import actions would not change References.")
        return BibImportPlan(
            inspection.source_path,
            inspection.source_token,
            inspection.reference_token,
            inspection.preview,
            tuple(decisions),
            projection,
        )

    def apply_import(self, plan: BibImportPlan) -> BibImportResult:
        if not isinstance(plan, BibImportPlan):
            raise TypeError("plan must be BibImportPlan")
        try:
            source_path = self._validated_import_path(plan.source_path)
        except (OSError, TypeError, ValueError):
            return BibImportResult("stale", "The .bib source is no longer the same regular file; nothing was imported.")
        if source_path != plan.source_path or file_token(source_path) != plan.source_token:
            return BibImportResult("stale", "The .bib source changed after preview; nothing was imported.")
        snapshot = self._store.load()
        if snapshot.token != plan.reference_token:
            return BibImportResult("stale", "References changed after preview; nothing was imported.")
        if any(item.blocking for item in snapshot.diagnostics):
            return BibImportResult("error", "References has blocking diagnostics and is read-only.")
        try:
            library = parse_bibliography(self._read_import(plan.source_path), plan.preview.format)
            preview = build_import_preview(library, snapshot.records)
            if preview != plan.preview:
                return BibImportResult("stale", "The exact import projection changed after preview.")
            projection = apply_import_decisions(preview, snapshot.records, plan.decisions)
            if projection != plan.projection:
                return BibImportResult("stale", "The exact import plan changed after preview.")
        except (OSError, TypeError, UnicodeError, ValueError) as error:
            return BibImportResult("error", str(error))
        result = self._store.save(projection.records, snapshot.token)
        if not result.saved:
            return BibImportResult(
                "stale" if result.status == "conflict" else "error",
                result.message or "Could not save References.",
            )
        self._refresh_references()
        return BibImportResult(
            "imported",
            (
                f"Imported {projection.imported}, replaced {projection.replaced}, "
                f"merged {projection.merged}, skipped {projection.skipped}."
            ),
            projection,
        )

    def prepare_export(self, format: str) -> BibExportPlan:
        if format not in BIB_FORMATS:
            raise ValueError("Choose BibTeX or BibLaTeX.")
        snapshot = self._load_writable_references()
        artifact = export_references(snapshot.records, format)
        return BibExportPlan(format, snapshot.token, artifact)

    def apply_export(self, plan: BibExportPlan, output_path: str) -> BibExportResult:
        if not isinstance(plan, BibExportPlan):
            raise TypeError("plan must be BibExportPlan")
        try:
            destination = self._validated_export_path(output_path)
        except (TypeError, ValueError) as error:
            return BibExportResult("error", str(error))
        snapshot = self._store.load()
        if snapshot.token != plan.reference_token:
            return BibExportResult("stale", "References changed after export preview; no .bib file was written.")
        if any(item.blocking for item in snapshot.diagnostics):
            return BibExportResult("error", "References has blocking diagnostics and is read-only.")
        rebuilt = export_references(snapshot.records, plan.format)
        if rebuilt != plan.artifact:
            return BibExportResult("stale", "The exact export projection changed after preview.")
        try:
            self._writer(destination, plan.artifact.text)
        except (OSError, TypeError, ValueError) as error:
            return BibExportResult("error", str(error))
        return BibExportResult(
            "exported",
            f"Exported {plan.artifact.reference_count} References as {plan.format}.",
            destination,
            plan.artifact,
        )

    def _load_writable_references(self) -> ReferenceLibrarySnapshot:
        snapshot = self._store.load()
        blocking = tuple(item.message for item in snapshot.diagnostics if item.blocking)
        if blocking:
            raise ValueError("References contains blocking diagnostics: " + "; ".join(blocking))
        return snapshot

    def _records_for_token(self, token: FileToken) -> tuple[ReferenceRecord, ...]:
        snapshot = self._load_writable_references()
        if snapshot.token != token:
            raise ValueError("References changed after import inspection.")
        return snapshot.records

    def _validated_import_path(self, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Choose a .bib file to import.")
        path = os.path.abspath(os.path.expanduser(value.strip()))
        if Path(path).suffix.casefold() != ".bib":
            raise ValueError("BibTeX/BibLaTeX import requires a .bib file.")
        if not os.path.isfile(path) or os.path.islink(path):
            raise ValueError("Import source must be an existing regular, non-symlink .bib file.")
        if os.path.getsize(path) > _MAX_IMPORT_BYTES:
            raise ValueError("Import source exceeds the 8 MiB safety limit.")
        return path

    def _validated_export_path(self, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Choose an export destination.")
        path = os.path.abspath(os.path.expanduser(value.strip()))
        if Path(path).suffix.casefold() != ".bib":
            raise ValueError("BibTeX/BibLaTeX export requires the .bib extension.")
        if os.path.normcase(os.path.realpath(path)) == os.path.normcase(os.path.realpath(self._store.path)):
            raise ValueError("Export cannot replace the canonical references.md authority.")
        if os.path.isdir(path) or os.path.islink(path):
            raise ValueError("Export destination cannot be a directory or symlink.")
        if os.path.exists(path) and not os.path.isfile(path):
            raise ValueError("Export destination must be a regular file path.")
        parent = os.path.dirname(path) or os.curdir
        if not os.path.isdir(parent):
            raise ValueError("The export destination folder does not exist.")
        return path

    @staticmethod
    def _read_import(path: str) -> str:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return handle.read()
