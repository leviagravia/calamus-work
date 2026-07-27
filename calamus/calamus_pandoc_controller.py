"""GTK-free W90 controller for safe external Pandoc/citeproc export."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Callable, Protocol

from calamus_bibtex import BIBLATEX, BibExportArtifact, export_references
from calamus_pandoc import (
    PRODUCT_BIBLIOGRAPHY,
    PRODUCT_DOCUMENT,
    SCOPE_CITED,
    SCOPE_REFERENCE_SET,
    PandocExportRequest,
    PandocFormat,
    PandocSelection,
    document_digest,
    pandoc_format,
    product_title,
    scope_title,
    select_references,
)
from calamus_pandoc_process import (
    PandocIdentity,
    PandocProcessResult,
    PandocProcessRunner,
)
from calamus_reference_set_store import ReferenceSetSnapshot
from calamus_reference_store import ReferenceLibrarySnapshot
from calamus_research_file import FileToken, file_token
from calamus_source_note_store import source_notes_path

_MAX_DOCUMENT_BYTES = 16 * 1024 * 1024
_MAX_CSL_BYTES = 4 * 1024 * 1024
_MAX_PREVIEW_BYTES = 4 * 1024 * 1024
_EXPORT_TIMEOUT_SECONDS = 120.0
_PREVIEW_TIMEOUT_SECONDS = 60.0


class ReferenceStore(Protocol):
    path: str
    def load(self) -> ReferenceLibrarySnapshot: ...


class ReferenceSetStore(Protocol):
    path: str
    def load(self) -> ReferenceSetSnapshot: ...


@dataclass(frozen=True)
class PandocExportPlan:
    request: PandocExportRequest
    format: PandocFormat
    identity: PandocIdentity
    selection: PandocSelection
    reference_path: str
    reference_token: FileToken
    reference_set_path: str
    reference_set_token: FileToken
    document_path: str
    document_file_token: FileToken
    document_digest: str
    csl_path: str
    csl_token: FileToken
    destination: str
    destination_token: FileToken
    destination_parent_token: tuple[int, int, int]
    biblatex: BibExportArtifact


@dataclass(frozen=True)
class PandocPreviewResult:
    status: str
    message: str
    text: str = ""
    process: PandocProcessResult | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "previewed"


@dataclass(frozen=True)
class PandocExportResult:
    status: str
    message: str
    path: str = ""
    process: PandocProcessResult | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "exported"


class PandocExportController:
    def __init__(
        self,
        reference_store: ReferenceStore,
        reference_set_store: ReferenceSetStore,
        *,
        document_path_provider: Callable[[], str | None],
        document_text_provider: Callable[[], str],
        runner: PandocProcessRunner | None = None,
    ) -> None:
        if not hasattr(reference_store, "load") or not hasattr(reference_store, "path"):
            raise TypeError("reference_store must implement path/load")
        if not hasattr(reference_set_store, "load") or not hasattr(reference_set_store, "path"):
            raise TypeError("reference_set_store must implement path/load")
        if not callable(document_path_provider) or not callable(document_text_provider):
            raise TypeError("document providers must be callable")
        self._references = reference_store
        self._reference_sets = reference_set_store
        self._document_path_provider = document_path_provider
        self._document_text_provider = document_text_provider
        self._runner = runner or PandocProcessRunner()

    @property
    def active_pid(self) -> int | None:
        return self._runner.active_pid

    def cancel_active(self) -> bool:
        return self._runner.cancel_active()

    def prepare_export(self, request: PandocExportRequest) -> PandocExportPlan:
        if not isinstance(request, PandocExportRequest):
            raise TypeError("request must be PandocExportRequest")
        descriptor = pandoc_format(request.product, request.format)
        identity = self._runner.detect()
        reference_snapshot = self._load_references()
        set_snapshot = self._load_reference_sets(request.scope == SCOPE_REFERENCE_SET)
        document_path, document_file_token = self._document_identity(
            required=request.product == PRODUCT_DOCUMENT
        )
        document_text = self._document_text_provider()
        if not isinstance(document_text, str):
            raise TypeError("document_text_provider must return a string")
        if len(document_text.encode("utf-8")) > _MAX_DOCUMENT_BYTES:
            raise ValueError("Pandoc export is limited to a 16 MiB document snapshot.")
        selection = select_references(
            reference_snapshot.records,
            set_snapshot.sets,
            document_text,
            product=request.product,
            scope=request.scope,
            reference_set_name=request.reference_set_name,
        )
        csl_path, csl_token = self._validated_csl(request.csl_path)
        destination = self._validated_destination(
            request.destination,
            descriptor,
            document_path=document_path,
            csl_path=csl_path,
        )
        destination_parent_token = self._directory_token(os.path.dirname(destination) or os.curdir)
        biblatex = export_references(selection.records, BIBLATEX)
        return PandocExportPlan(
            request,
            descriptor,
            identity,
            selection,
            os.path.abspath(self._references.path),
            reference_snapshot.token,
            os.path.abspath(self._reference_sets.path),
            set_snapshot.token,
            document_path,
            document_file_token,
            document_digest(document_text),
            csl_path,
            csl_token,
            destination,
            file_token(destination),
            destination_parent_token,
            biblatex,
        )

    def build_preview(self, plan: PandocExportPlan) -> PandocPreviewResult:
        if not isinstance(plan, PandocExportPlan):
            raise TypeError("plan must be PandocExportPlan")
        stale = self._stale_message(plan)
        if stale:
            return PandocPreviewResult("stale", stale)
        try:
            with tempfile.TemporaryDirectory(prefix="calamus-pandoc-preview-") as workspace:
                paths = self._write_inputs(plan, workspace)
                output = os.path.join(workspace, "preview.txt")
                argv, cwd = self._build_argv(plan, paths, output, preview=True)
                process = self._runner.run(
                    argv,
                    cwd=cwd,
                    timeout_seconds=_PREVIEW_TIMEOUT_SECONDS,
                )
                failure = self._process_failure(process, "preview")
                if failure:
                    return PandocPreviewResult(process.status, failure, process=process)
                try:
                    size = os.path.getsize(output)
                except OSError as error:
                    return PandocPreviewResult("error", f"Pandoc preview output is unavailable: {error}", process=process)
                if size <= 0:
                    return PandocPreviewResult("error", "Pandoc produced an empty preview.", process=process)
                if size > _MAX_PREVIEW_BYTES:
                    return PandocPreviewResult("error", "Pandoc preview exceeds the 4 MiB safety limit.", process=process)
                with open(output, "r", encoding="utf-8") as handle:
                    text = handle.read()
        except (OSError, TypeError, UnicodeError, ValueError, RuntimeError) as error:
            return PandocPreviewResult("error", str(error))
        stale = self._stale_message(plan)
        if stale:
            return PandocPreviewResult("stale", stale, process=process)
        return PandocPreviewResult(
            "previewed",
            self.render_preview_summary(plan, process),
            text,
            process,
        )

    def apply_export(self, plan: PandocExportPlan) -> PandocExportResult:
        if not isinstance(plan, PandocExportPlan):
            raise TypeError("plan must be PandocExportPlan")
        stale = self._stale_message(plan)
        if stale:
            return PandocExportResult("stale", stale)
        destination_dir = os.path.dirname(plan.destination) or os.curdir
        stage_fd = -1
        stage_path = ""
        process: PandocProcessResult | None = None
        try:
            if self._directory_token(destination_dir) != plan.destination_parent_token:
                return PandocExportResult(
                    "stale",
                    "The destination folder changed after preview; nothing was written.",
                )
            stage_fd, stage_path = tempfile.mkstemp(
                prefix=".calamus-pandoc-",
                suffix=".stage",
                dir=destination_dir,
            )
            os.close(stage_fd)
            stage_fd = -1
            with tempfile.TemporaryDirectory(prefix="calamus-pandoc-export-") as workspace:
                paths = self._write_inputs(plan, workspace)
                argv, cwd = self._build_argv(plan, paths, stage_path, preview=False)
                process = self._runner.run(
                    argv,
                    cwd=cwd,
                    timeout_seconds=_EXPORT_TIMEOUT_SECONDS,
                )
                failure = self._process_failure(process, "export")
                if failure:
                    return PandocExportResult(process.status, failure, process=process)
                self._validate_stage(stage_path)
                stale = self._stale_message(plan)
                if stale:
                    return PandocExportResult("stale", stale, process=process)
                if self._directory_token(destination_dir) != plan.destination_parent_token:
                    return PandocExportResult(
                        "stale",
                        "The destination folder changed before publication; nothing was written.",
                        process=process,
                    )
                os.replace(stage_path, plan.destination)
                stage_path = ""
                self._fsync_directory(destination_dir)
        except (OSError, TypeError, UnicodeError, ValueError, RuntimeError) as error:
            return PandocExportResult("error", str(error), process=process)
        finally:
            if stage_fd >= 0:
                try:
                    os.close(stage_fd)
                except OSError:
                    pass
            if stage_path:
                try:
                    os.unlink(stage_path)
                except OSError:
                    pass
        warning = self._stderr_summary(process.stderr if process else "")
        message = (
            f"Exported {product_title(plan.request.product)} with "
            f"{len(plan.selection.records)} Reference(s)."
        )
        if warning:
            message += " Pandoc reported: " + warning
        return PandocExportResult("exported", message, plan.destination, process)

    def render_preview_summary(
        self,
        plan: PandocExportPlan,
        process: PandocProcessResult | None = None,
    ) -> str:
        style = plan.csl_path or "Pandoc default CSL style"
        set_line = (
            f"Reference Set: {plan.selection.reference_set_name}\n"
            if plan.selection.reference_set_name else ""
        )
        warnings = "\n".join(f"- {item}" for item in plan.biblatex.warnings) or "None"
        process_warning = self._stderr_summary(process.stderr if process else "") or "None"
        return (
            f"Pandoc: {plan.identity.path}\n"
            f"Version: {plan.identity.version}\n"
            f"Product: {product_title(plan.request.product)}\n"
            f"Scope: {scope_title(plan.request.scope)}\n"
            f"{set_line}"
            f"References: {len(plan.selection.records)}\n"
            f"Keys: {', '.join(plan.selection.keys)}\n"
            f"Format: {plan.format.label} ({plan.format.extension})\n"
            f"CSL style: {style}\n"
            f"Destination: {plan.destination}\n"
            f"Destination exists: {'yes' if plan.destination_token.exists else 'no'}\n"
            f"BibLaTeX mapping warnings:\n{warnings}\n"
            f"Pandoc preview warnings: {process_warning}"
        )

    def _stale_message(self, plan: PandocExportPlan) -> str:
        try:
            rebuilt = self.prepare_export(plan.request)
        except (OSError, TypeError, UnicodeError, ValueError, RuntimeError) as error:
            return f"The export plan can no longer be reproduced: {error}"
        if rebuilt != plan:
            return "References, Reference Sets, document, CSL, Pandoc or destination changed after preview; nothing was written."
        return ""

    def _load_references(self) -> ReferenceLibrarySnapshot:
        snapshot = self._references.load()
        blocking = tuple(item.message for item in snapshot.diagnostics if item.blocking)
        if blocking:
            raise ValueError("References contains blocking diagnostics: " + "; ".join(blocking))
        if not snapshot.records:
            raise ValueError("References is empty.")
        return snapshot

    def _load_reference_sets(self, required: bool) -> ReferenceSetSnapshot:
        if not required:
            return ReferenceSetSnapshot((), FileToken(False), ())
        snapshot = self._reference_sets.load()
        blocking = tuple(item.message for item in snapshot.diagnostics if item.blocking)
        if blocking:
            raise ValueError("Reference Sets contains blocking diagnostics: " + "; ".join(blocking))
        return snapshot

    def _document_identity(self, *, required: bool) -> tuple[str, FileToken]:
        value = self._document_path_provider()
        if not isinstance(value, str) or not value.strip():
            if required:
                raise ValueError("Save the current document before exporting it with Pandoc.")
            return "", FileToken(False)
        path = os.path.abspath(os.path.expanduser(value.strip()))
        if not os.path.isfile(path) or os.path.islink(path):
            raise ValueError("The current document must be a regular, non-symlink file.")
        return path, file_token(path)

    def _validated_csl(self, value: str) -> tuple[str, FileToken]:
        if not value:
            return "", FileToken(False)
        path = os.path.abspath(os.path.expanduser(value))
        if Path(path).suffix.casefold() != ".csl":
            raise ValueError("A custom citation style must be a local .csl file.")
        if not os.path.isfile(path) or os.path.islink(path):
            raise ValueError("The CSL style must be an existing regular, non-symlink file.")
        if os.path.getsize(path) > _MAX_CSL_BYTES:
            raise ValueError("The CSL style exceeds the 4 MiB safety limit.")
        return path, file_token(path)

    def _validated_destination(
        self,
        value: str,
        descriptor: PandocFormat,
        *,
        document_path: str,
        csl_path: str,
    ) -> str:
        path = os.path.abspath(os.path.expanduser(value.strip()))
        if Path(path).suffix.casefold() != descriptor.extension:
            raise ValueError(
                f"{descriptor.label} export requires the {descriptor.extension} extension."
            )
        parent = os.path.dirname(path) or os.curdir
        if not os.path.isdir(parent):
            raise ValueError("The export destination folder is unavailable.")
        if not os.access(parent, os.W_OK):
            raise ValueError("The export destination folder is not writable.")
        if os.path.lexists(path) and (os.path.islink(path) or not os.path.isfile(path)):
            raise ValueError("The export destination must be a regular non-symlink file.")
        protected = {
            os.path.abspath(self._references.path),
            os.path.abspath(self._reference_sets.path),
        }
        if document_path:
            protected.add(document_path)
            protected.add(os.path.abspath(source_notes_path(document_path)))
        if csl_path:
            protected.add(csl_path)
        normalized = os.path.normcase(os.path.realpath(path))
        if any(normalized == os.path.normcase(os.path.realpath(item)) for item in protected):
            raise ValueError("Pandoc output cannot replace a canonical Research input or the current document.")
        return path


    @staticmethod
    def _directory_token(path: str) -> tuple[int, int, int]:
        absolute = os.path.abspath(path)
        stat = os.lstat(absolute)
        if os.path.islink(absolute) or not os.path.isdir(absolute):
            raise ValueError("The export destination folder must be a regular non-symlink directory.")
        return (stat.st_dev, stat.st_ino, stat.st_mode)

    def _write_inputs(self, plan: PandocExportPlan, workspace: str) -> dict[str, str]:
        bib_path = os.path.join(workspace, "calamus-references.bib")
        self._write_private_text(bib_path, plan.biblatex.text)
        paths = {"bibliography": bib_path}
        metadata: dict[str, str] = {}
        if plan.request.product == PRODUCT_BIBLIOGRAPHY:
            metadata["title"] = "Calamus Bibliography"
            paths["input"] = bib_path
        else:
            document_path = os.path.join(workspace, "calamus-document.md")
            self._write_private_text(document_path, plan.selection.document_text)
            paths["input"] = document_path
            if plan.request.scope != SCOPE_CITED:
                metadata["nocite"] = "@*"
        if metadata:
            metadata_path = os.path.join(workspace, "calamus-metadata.json")
            self._write_private_text(metadata_path, json.dumps(metadata, ensure_ascii=False))
            paths["metadata"] = metadata_path
        return paths

    def _build_argv(
        self,
        plan: PandocExportPlan,
        paths: dict[str, str],
        output_path: str,
        *,
        preview: bool,
    ) -> tuple[tuple[str, ...], str | None]:
        writer = "plain" if preview else plan.format.writer
        input_format = "biblatex" if plan.request.product == PRODUCT_BIBLIOGRAPHY else "markdown"
        argv: list[str] = [
            plan.identity.path,
            paths["input"],
            "--from", input_format,
            "--to", writer,
            "--citeproc",
            "--standalone",
        ]
        if plan.request.product == PRODUCT_DOCUMENT:
            argv.extend(("--bibliography", paths["bibliography"]))
        if plan.csl_path:
            argv.extend(("--csl", plan.csl_path))
        metadata = paths.get("metadata")
        if metadata:
            argv.extend(("--metadata-file", metadata))
        argv.extend(("--output", output_path))
        cwd = os.path.dirname(plan.document_path) if plan.document_path else None
        return tuple(argv), cwd

    def _validate_stage(self, path: str) -> None:
        if not os.path.isfile(path) or os.path.islink(path):
            raise ValueError("Pandoc did not produce a regular staged output file.")
        if os.path.getsize(path) <= 0:
            raise ValueError("Pandoc produced an empty output file.")
        with open(path, "rb") as handle:
            os.fsync(handle.fileno())

    @staticmethod
    def _write_private_text(path: str, text: str) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(path, flags, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            try:
                os.unlink(path)
            except OSError:
                pass
            raise

    @staticmethod
    def _fsync_directory(path: str) -> None:
        flags = getattr(os, "O_DIRECTORY", 0) | os.O_RDONLY
        try:
            fd = os.open(path, flags)
        except OSError:
            return
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @staticmethod
    def _stderr_summary(stderr: str) -> str:
        lines = [" ".join(line.split()) for line in (stderr or "").splitlines() if line.strip()]
        text = " | ".join(lines)
        return text[:1200]

    def _process_failure(self, process: PandocProcessResult, operation: str) -> str:
        if process.status == "cancelled":
            return f"Pandoc {operation} was cancelled; no final output was written."
        if process.status == "timeout":
            return f"Pandoc {operation} exceeded the time limit; no final output was written."
        if not process.succeeded:
            detail = self._stderr_summary(process.stderr) or self._stderr_summary(process.stdout)
            if not detail:
                detail = f"exit status {process.returncode}"
            return f"Pandoc {operation} failed: {detail}"
        return ""
