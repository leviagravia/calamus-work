"""Pure W90 model for a narrow external Pandoc/citeproc handoff.

Calamus keeps ``references.md`` as the sole bibliographic authority.  This
module validates one closed export surface, selects canonical Reference records,
and builds deterministic derived document projections.  It performs no file
I/O, starts no process and imports no GTK code.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Iterable

from calamus_citations import parse_citation_clusters
from calamus_reference_integrity import build_identity_index, resolve_reference
from calamus_reference_sets import ReferenceSet, canonicalize_reference_set
from calamus_references import ReferenceRecord

PRODUCT_BIBLIOGRAPHY = "formatted-bibliography"
PRODUCT_DOCUMENT = "current-document"
PRODUCTS = (PRODUCT_BIBLIOGRAPHY, PRODUCT_DOCUMENT)

SCOPE_CITED = "cited"
SCOPE_ALL = "all"
SCOPE_REFERENCE_SET = "reference-set"
SCOPES = (SCOPE_CITED, SCOPE_ALL, SCOPE_REFERENCE_SET)

FORMAT_PLAIN = "plain"
FORMAT_HTML = "html"
FORMAT_ODT = "odt"
FORMAT_DOCX = "docx"
FORMAT_EPUB = "epub"
FORMAT_RTF = "rtf"
FORMAT_LATEX = "latex"


_REMOTE_MARKDOWN_MEDIA_RE = re.compile(
    r"!\[[^\]\n]*\]\(\s*<?https?://", re.IGNORECASE
)
_REMOTE_HTML_MEDIA_RE = re.compile(
    r"<(?:img|audio|video|source)\b[^>]*\b(?:src|poster)\s*=\s*[\"']?https?://",
    re.IGNORECASE,
)
_FENCE_LINE_RE = re.compile(r"^[ \t]*(?P<mark>`{3,}|~{3,})")
_INLINE_CODE_RE = re.compile(r"(`+)(.*?)\1")


def reject_remote_media(text: str) -> None:
    """Reject Markdown/HTML media that could make Pandoc access the network.

    Ordinary links are allowed because Pandoc renders them without fetching the
    target.  Media sources are blocked.  Fenced and inline code are ignored.
    """
    if not isinstance(text, str):
        raise TypeError("document text must be a string")
    fenced_mark = ""
    visible: list[str] = []
    for line in text.splitlines(keepends=True):
        match = _FENCE_LINE_RE.match(line.rstrip("\r\n"))
        if fenced_mark:
            if match and match.group("mark")[0] == fenced_mark[0] and len(match.group("mark")) >= len(fenced_mark):
                fenced_mark = ""
            visible.append("\n" if line.endswith(("\n", "\r")) else "")
            continue
        if match:
            fenced_mark = match.group("mark")
            visible.append("\n" if line.endswith(("\n", "\r")) else "")
            continue
        visible.append(_INLINE_CODE_RE.sub("", line))
    projected = "".join(visible)
    if _REMOTE_MARKDOWN_MEDIA_RE.search(projected) or _REMOTE_HTML_MEDIA_RE.search(projected):
        raise ValueError(
            "Remote images or media are not allowed in W90 Pandoc export; "
            "use a local file or remove the remote media reference."
        )

_PRODUCT_TITLES = {
    PRODUCT_BIBLIOGRAPHY: "Formatted Bibliography",
    PRODUCT_DOCUMENT: "Current Document with Citations",
}
_SCOPE_TITLES = {
    SCOPE_CITED: "References cited in the current document",
    SCOPE_ALL: "All References",
    SCOPE_REFERENCE_SET: "One Reference Set",
}


@dataclass(frozen=True)
class PandocFormat:
    id: str
    label: str
    extension: str
    writer: str
    binary: bool
    products: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.id or not self.label or not self.extension.startswith("."):
            raise ValueError("Pandoc format descriptor is incomplete")
        if not self.writer or not self.products:
            raise ValueError("Pandoc format descriptor is incomplete")
        if any(product not in PRODUCTS for product in self.products):
            raise ValueError("Pandoc format descriptor has an invalid product")


_FORMATS = (
    PandocFormat(FORMAT_PLAIN, "Plain text", ".txt", "plain", False, (PRODUCT_BIBLIOGRAPHY,)),
    PandocFormat(FORMAT_HTML, "HTML", ".html", "html5", False, PRODUCTS),
    PandocFormat(FORMAT_ODT, "OpenDocument Text", ".odt", "odt", True, PRODUCTS),
    PandocFormat(FORMAT_DOCX, "Microsoft Word", ".docx", "docx", True, PRODUCTS),
    PandocFormat(FORMAT_EPUB, "EPUB", ".epub", "epub3", True, (PRODUCT_DOCUMENT,)),
    PandocFormat(FORMAT_RTF, "Rich Text Format", ".rtf", "rtf", False, PRODUCTS),
    PandocFormat(FORMAT_LATEX, "LaTeX source", ".tex", "latex", False, PRODUCTS),
)
_FORMAT_BY_ID = {item.id: item for item in _FORMATS}


@dataclass(frozen=True)
class PandocExportRequest:
    product: str
    scope: str
    format: str
    destination: str
    reference_set_name: str = ""
    csl_path: str = ""

    def __post_init__(self) -> None:
        if self.product not in PRODUCTS:
            raise ValueError("Choose a supported Pandoc export product.")
        if self.scope not in SCOPES:
            raise ValueError("Choose a supported Reference scope.")
        descriptor = pandoc_format(self.product, self.format)
        destination = self.destination.strip() if isinstance(self.destination, str) else ""
        if not destination:
            raise ValueError("Choose an export destination.")
        set_name = self.reference_set_name.strip() if isinstance(self.reference_set_name, str) else ""
        if self.scope == SCOPE_REFERENCE_SET and not set_name:
            raise ValueError("Choose one Reference Set.")
        csl_path = self.csl_path.strip() if isinstance(self.csl_path, str) else ""
        object.__setattr__(self, "destination", destination)
        object.__setattr__(self, "reference_set_name", set_name)
        object.__setattr__(self, "csl_path", csl_path)
        if Path(destination).suffix.casefold() != descriptor.extension:
            raise ValueError(
                f"{descriptor.label} export requires the {descriptor.extension} extension."
            )


@dataclass(frozen=True)
class PandocSelection:
    records: tuple[ReferenceRecord, ...]
    keys: tuple[str, ...]
    document_text: str
    cited_keys: tuple[str, ...]
    reference_set_name: str = ""

    def __post_init__(self) -> None:
        if not self.records or not self.keys:
            raise ValueError("Pandoc export requires at least one Reference.")
        if tuple(record.key for record in self.records) != self.keys:
            raise ValueError("Pandoc selection keys must match record order.")


def product_title(product: str) -> str:
    try:
        return _PRODUCT_TITLES[product]
    except KeyError as error:
        raise ValueError("Unsupported Pandoc export product.") from error


def scope_title(scope: str) -> str:
    try:
        return _SCOPE_TITLES[scope]
    except KeyError as error:
        raise ValueError("Unsupported Reference scope.") from error


def pandoc_formats(product: str) -> tuple[PandocFormat, ...]:
    if product not in PRODUCTS:
        raise ValueError("Unsupported Pandoc export product.")
    return tuple(item for item in _FORMATS if product in item.products)


def pandoc_format(product: str, format_id: str) -> PandocFormat:
    descriptor = _FORMAT_BY_ID.get(format_id)
    if descriptor is None or product not in descriptor.products:
        raise ValueError("Choose a format supported by the selected product.")
    return descriptor


def default_format(product: str) -> str:
    if product == PRODUCT_BIBLIOGRAPHY:
        return FORMAT_PLAIN
    if product == PRODUCT_DOCUMENT:
        return FORMAT_ODT
    raise ValueError("Unsupported Pandoc export product.")


def document_digest(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("document text must be a string")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonicalize_document_citations(
    records: Iterable[ReferenceRecord],
    text: str,
) -> tuple[str, tuple[str, ...]]:
    """Return a derived document with alias citations replaced by primary keys.

    The caller owns the returned projection only.  The source document is never
    changed.  Missing or ambiguous identities fail closed before Pandoc runs.
    """
    if not isinstance(text, str):
        raise TypeError("document text must be a string")
    snapshot = tuple(records)
    build_identity_index(snapshot)
    replacements: list[tuple[int, int, str]] = []
    cited: list[str] = []
    for cluster in parse_citation_clusters(text):
        for item in cluster.items:
            resolution = resolve_reference(snapshot, item.key)
            if resolution.status == "missing":
                raise ValueError(f"Citation refers to a missing Reference: {item.key}.")
            if resolution.status == "ambiguous":
                raise ValueError(f"Citation identity is ambiguous: {item.key}.")
            canonical = resolution.canonical_key
            assert canonical is not None
            if canonical not in cited:
                cited.append(canonical)
            if canonical != item.key:
                replacements.append((item.start, item.end, canonical))
    projected = text
    for start, end, canonical in reversed(replacements):
        projected = projected[:start] + canonical + projected[end:]
    return projected, tuple(cited)


def _exact_reference_set(
    reference_sets: tuple[ReferenceSet, ...],
    requested_name: str,
) -> ReferenceSet:
    exact = [item for item in reference_sets if item.name == requested_name]
    if len(exact) == 1:
        return exact[0]
    folded = [item for item in reference_sets if item.name.casefold() == requested_name.casefold()]
    if folded:
        raise ValueError(
            "Reference Set names are case-sensitive; choose the exact stored name: "
            + folded[0].name
            + "."
        )
    raise ValueError(f"Reference Set is unavailable: {requested_name}.")


def select_references(
    records: Iterable[ReferenceRecord],
    reference_sets: Iterable[ReferenceSet],
    document_text: str,
    *,
    product: str,
    scope: str,
    reference_set_name: str = "",
) -> PandocSelection:
    if product not in PRODUCTS:
        raise ValueError("Unsupported Pandoc export product.")
    if scope not in SCOPES:
        raise ValueError("Unsupported Reference scope.")
    record_snapshot = tuple(records)
    if not record_snapshot:
        raise ValueError("References is empty.")
    build_identity_index(record_snapshot)
    record_by_key = {record.key: record for record in record_snapshot}
    projected_text, cited = canonicalize_document_citations(record_snapshot, document_text)
    if product == PRODUCT_DOCUMENT:
        reject_remote_media(projected_text)

    selected_keys: tuple[str, ...]
    selected_set_name = ""
    if scope == SCOPE_ALL:
        selected_keys = tuple(record.key for record in record_snapshot)
    elif scope == SCOPE_CITED:
        if not cited:
            raise ValueError("The current document contains no Pandoc citations.")
        selected_keys = cited
    else:
        selected = _exact_reference_set(tuple(reference_sets), reference_set_name)
        canonical = canonicalize_reference_set(selected, record_snapshot)
        if not canonical.members:
            raise ValueError(f"Reference Set is empty: {selected.name}.")
        selected_keys = canonical.members
        selected_set_name = selected.name

    if product == PRODUCT_DOCUMENT:
        outside = tuple(key for key in cited if key not in selected_keys)
        if outside:
            raise ValueError(
                "The selected Reference scope omits citation(s) used by the document: "
                + ", ".join(outside)
                + "."
            )

    selected_records = tuple(record_by_key[key] for key in selected_keys)
    return PandocSelection(
        selected_records,
        selected_keys,
        projected_text,
        cited,
        selected_set_name,
    )


def suggested_output_name(
    document_path: str | None,
    product: str,
    format_id: str,
) -> str:
    descriptor = pandoc_format(product, format_id)
    stem = "calamus"
    if isinstance(document_path, str) and document_path.strip():
        candidate = Path(document_path.strip()).stem.strip()
        if candidate:
            stem = candidate
    suffix = "bibliography" if product == PRODUCT_BIBLIOGRAPHY else "with-citations"
    return f"{stem}-{suffix}{descriptor.extension}"
