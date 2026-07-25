"""Read-only Research snapshots and atomically persist one derived export."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable

from calamus_document_structure import DocumentStructure
from calamus_reference_store import MarkdownReferenceStore
from calamus_research_export import ResearchExportArtifact, build_research_export
from calamus_research_file import atomic_write_utf8
from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path


@dataclass(frozen=True)
class ResearchExportResult:
    status: str
    path: str = ""
    artifact: ResearchExportArtifact | None = None
    message: str = ""

    @property
    def exported(self) -> bool:
        return self.status == "exported"


class ResearchExportController:
    def __init__(
        self,
        *,
        reference_store: MarkdownReferenceStore,
        document_path_provider: Callable[[], str | None],
        document_text_provider: Callable[[], str],
        document_structure_provider: Callable[[], DocumentStructure],
        source_note_store_factory=MarkdownSourceNoteStore,
        writer=atomic_write_utf8,
    ) -> None:
        if not isinstance(reference_store, MarkdownReferenceStore):
            raise TypeError("reference_store must be MarkdownReferenceStore")
        if not all(callable(value) for value in (
            document_path_provider,
            document_text_provider,
            document_structure_provider,
            source_note_store_factory,
            writer,
        )):
            raise TypeError("Research export dependencies must be callable")
        self._reference_store = reference_store
        self._document_path_provider = document_path_provider
        self._document_text_provider = document_text_provider
        self._document_structure_provider = document_structure_provider
        self._source_note_store_factory = source_note_store_factory
        self._writer = writer

    def prepare(self, kind: str) -> ResearchExportArtifact:
        document_path = self._document_path()
        document_text = self._document_text_provider()
        structure = self._document_structure_provider()
        if not isinstance(document_text, str):
            raise TypeError("document_text_provider must return text")
        if not isinstance(structure, DocumentStructure):
            raise TypeError("document_structure_provider must return DocumentStructure")

        reference_snapshot = self._reference_store.load()
        blocking_references = tuple(
            item.message for item in reference_snapshot.diagnostics if item.blocking
        )
        if blocking_references:
            raise ValueError(
                "References contains blocking diagnostics: " + "; ".join(blocking_references)
            )

        sidecar_path = source_notes_path(document_path)
        assert sidecar_path is not None
        note_snapshot = self._source_note_store_factory(sidecar_path).load()
        blocking_notes = tuple(item.message for item in note_snapshot.diagnostics if item.blocking)
        if blocking_notes:
            raise ValueError(
                "Source Notes contains blocking diagnostics: " + "; ".join(blocking_notes)
            )

        return build_research_export(
            kind,
            document_name=os.path.basename(document_path),
            document_text=document_text,
            records=reference_snapshot.records,
            notes=note_snapshot.notes,
            structure=structure,
        )

    def export(self, kind: str, output_path: str) -> ResearchExportResult:
        try:
            artifact = self.prepare(kind)
            destination = self._validated_output_path(output_path)
            self._writer(destination, artifact.markdown)
        except (OSError, TypeError, ValueError) as error:
            return ResearchExportResult("error", message=str(error))
        return ResearchExportResult(
            "exported",
            path=destination,
            artifact=artifact,
            message=(
                f"Exported {artifact.source_note_count} Source Notes and "
                f"{artifact.reference_count} References."
            ),
        )

    def _document_path(self) -> str:
        value = self._document_path_provider()
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Save the current document before exporting Research apparatus.")
        path = os.path.abspath(os.path.expanduser(value.strip()))
        if not os.path.isfile(path):
            raise ValueError("The current document path is not an existing regular file.")
        return path

    def _validated_output_path(self, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("An export destination is required.")
        path = os.path.abspath(os.path.expanduser(value.strip()))
        if Path(path).suffix.casefold() != ".md":
            raise ValueError("Research apparatus exports must use the .md extension.")
        document_path = self._document_path()
        sidecar = source_notes_path(document_path)
        protected = {
            os.path.normcase(os.path.realpath(document_path)),
            os.path.normcase(os.path.realpath(self._reference_store.path)),
        }
        if sidecar:
            protected.add(os.path.normcase(os.path.realpath(sidecar)))
        if os.path.normcase(os.path.realpath(path)) in protected:
            raise ValueError("The export destination cannot replace a canonical Research authority.")
        if os.path.isdir(path):
            raise ValueError("The export destination is a directory.")
        parent = os.path.dirname(path) or os.curdir
        if not os.path.isdir(parent):
            raise ValueError("The export destination folder does not exist.")
        return path
