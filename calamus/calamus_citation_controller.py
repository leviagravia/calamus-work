"""GTK-free Quick Cite and citation-to-Reference coordination."""
from __future__ import annotations

from typing import Callable, Iterable

from calamus_citations import citation_lookup_at, format_pandoc_citation
from calamus_references import ReferenceRecord, normalize_key


class CitationController:
    def __init__(
        self,
        *,
        reference_records_provider: Callable[[], Iterable[ReferenceRecord]],
        insert_text: Callable[[str], bool],
        show_reference: Callable[[str], bool],
        choose_key: Callable[[tuple[str, ...]], str | None],
        on_error: Callable[[str], None],
    ) -> None:
        callbacks = (
            reference_records_provider,
            insert_text,
            show_reference,
            choose_key,
            on_error,
        )
        if any(not callable(callback) for callback in callbacks):
            raise TypeError("citation controller callbacks must be callable")
        self._reference_records_provider = reference_records_provider
        self._insert_text = insert_text
        self._show_reference = show_reference
        self._choose_key = choose_key
        self._on_error = on_error

    @property
    def records(self) -> tuple[ReferenceRecord, ...]:
        records = tuple(self._reference_records_provider())
        if any(not isinstance(record, ReferenceRecord) for record in records):
            raise TypeError("reference provider must return ReferenceRecord values")
        return records

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(record.key for record in self.records)

    def resolve_key(self, key: str) -> str | None:
        key_text = normalize_key(key)
        matches = [record.key for record in self.records if key_text in record.identity_keys]
        return matches[0] if len(matches) == 1 else None

    def quick_cite(self, key: str, locator: str = "") -> bool:
        key_text = normalize_key(key)
        canonical = self.resolve_key(key_text)
        if canonical is None:
            self._on_error(f"Reference key is not available: {key_text or '(empty)'}")
            return False
        try:
            citation = format_pandoc_citation(canonical, locator)
        except ValueError as error:
            self._on_error(str(error))
            return False
        if not self._insert_text(citation):
            self._on_error("Citation could not be inserted.")
            return False
        return True

    def open_citation(self, text: str, offset: int) -> bool:
        lookup = citation_lookup_at(text, offset)
        if lookup.status == "none":
            self._on_error("Place the cursor inside a Pandoc citation.")
            return False

        key = lookup.key
        if lookup.status == "ambiguous":
            key = self._choose_key(lookup.keys)
            if not key:
                return False

        key = normalize_key(key)
        canonical = self.resolve_key(key)
        if canonical is None:
            self._on_error(f"Citation key is missing from References: {key}")
            return False
        if not self._show_reference(canonical):
            self._on_error(f"Reference could not be selected: {canonical}")
            return False
        return True
