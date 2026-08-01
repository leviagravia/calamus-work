"""GTK-free refresh/state controller for the W96 Document Dossier Core."""
from __future__ import annotations

from collections.abc import Callable

from calamus_document_dossier import (
    DocumentDossierAuthorityStamp,
    DocumentDossierInputs,
    DocumentDossierSnapshot,
    build_document_dossier,
    document_dossier_authority_stamp,
)


class DocumentDossierController:
    """Own one derived snapshot without owning any document authority."""

    def __init__(
        self,
        source_provider: Callable[[], DocumentDossierInputs],
        *,
        builder: Callable[[DocumentDossierInputs], DocumentDossierSnapshot] = build_document_dossier,
    ) -> None:
        if not callable(source_provider):
            raise TypeError("source_provider must be callable")
        if not callable(builder):
            raise TypeError("builder must be callable")
        self._source_provider = source_provider
        self._builder = builder
        self._snapshot: DocumentDossierSnapshot | None = None
        self._marked_stale = True
        self._refresh_count = 0

    @property
    def snapshot(self) -> DocumentDossierSnapshot | None:
        return self._snapshot

    @property
    def refresh_count(self) -> int:
        return self._refresh_count

    @property
    def marked_stale(self) -> bool:
        return self._marked_stale

    def mark_stale(self) -> None:
        self._marked_stale = True

    def current_authority_stamp(self) -> DocumentDossierAuthorityStamp:
        return document_dossier_authority_stamp(self._source_provider())

    def is_current(self) -> bool:
        if self._snapshot is None or self._marked_stale:
            return False
        return self.current_authority_stamp() == self._snapshot.authority_stamp

    def refresh(self) -> DocumentDossierSnapshot:
        inputs = self._source_provider()
        if not isinstance(inputs, DocumentDossierInputs):
            raise TypeError("source_provider must return DocumentDossierInputs")
        snapshot = self._builder(inputs)
        self._snapshot = snapshot
        self._marked_stale = False
        self._refresh_count += 1
        return snapshot

    def ensure_current(self) -> DocumentDossierSnapshot:
        if not self.is_current():
            return self.refresh()
        assert self._snapshot is not None
        return self._snapshot
