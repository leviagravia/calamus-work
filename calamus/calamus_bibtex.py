"""Pure BibTeX/BibLaTeX parsing, mapping and deterministic export for Calamus.

``references.md`` remains the only bibliographic authority.  This module builds
immutable projections and derived text; it performs no file I/O and imports no
GTK code.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import re
import unicodedata
from typing import Iterable, Mapping, Sequence

from calamus_references import ReferenceRecord, suggest_reference_key

BIBTEX = "bibtex"
BIBLATEX = "biblatex"
BIB_FORMATS = (BIBLATEX, BIBTEX)

ACTION_IMPORT = "import"
ACTION_SKIP = "skip"
ACTION_REPLACE = "replace"
ACTION_MERGE = "merge"
ACTION_NEW_KEY = "new-key"

COLLISION_NONE = "new"
COLLISION_SAME = "same-key-same-content"
COLLISION_KEY = "same-key-different-content"
COLLISION_ALIAS = "alias-collision"
COLLISION_PROBABLE = "probable-duplicate"
COLLISION_INPUT = "duplicate-input-key"

_MONTHS = {
    "jan": "January", "feb": "February", "mar": "March", "apr": "April",
    "may": "May", "jun": "June", "jul": "July", "aug": "August",
    "sep": "September", "oct": "October", "nov": "November", "dec": "December",
}

_TYPE_TO_CALAMUS = {
    "book": "book", "mvbook": "book",
    "inbook": "book-chapter", "bookinbook": "book-chapter",
    "incollection": "book-chapter", "suppbook": "book-chapter",
    "suppcollection": "book-chapter",
    "article": "journal-article",
    "inreference": "encyclopedia-entry",
    "thesis": "thesis", "mastersthesis": "thesis", "phdthesis": "thesis",
    "inproceedings": "conference-paper", "conference": "conference-paper",
    "report": "report", "techreport": "report",
    "online": "website", "electronic": "website", "www": "website",
    "unpublished": "manuscript",
}

_CALAMUS_TO_TYPE_BIBLATEX = {
    "book": "book",
    "book-chapter": "incollection",
    "journal-article": "article",
    "encyclopedia-entry": "inreference",
    "thesis": "thesis",
    "conference-paper": "inproceedings",
    "report": "report",
    "institutional-document": "report",
    "website": "online",
    "manuscript": "unpublished",
    "other": "misc",
}

_CALAMUS_TO_TYPE_BIBTEX = {
    **_CALAMUS_TO_TYPE_BIBLATEX,
    "encyclopedia-entry": "incollection",
    "thesis": "phdthesis",
    "report": "techreport",
    "institutional-document": "techreport",
    "website": "misc",
}

_NATIVE_FIELDS = {
    "author", "editor", "title", "year", "date", "journal", "journaltitle",
    "booktitle", "publisher", "location", "address", "volume", "number", "issue",
    "pages", "doi", "isbn", "issn", "url", "language", "langid", "file",
    "keywords", "annotation", "abstract", "note",
}

_FIELD_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:+-]*$")
_COMMAND_RE = re.compile(r"\\([A-Za-z]+)\*?")


@dataclass(frozen=True)
class BibDiagnostic:
    line: int
    column: int
    code: str
    message: str
    blocking: bool = False


@dataclass(frozen=True)
class BibEntry:
    index: int
    line: int
    entry_type: str
    key: str
    fields: tuple[tuple[str, str], ...]
    raw: str = ""

    def field_map(self) -> dict[str, str]:
        return dict(self.fields)


@dataclass(frozen=True)
class BibLibrary:
    format: str
    entries: tuple[BibEntry, ...]
    diagnostics: tuple[BibDiagnostic, ...]
    strings: tuple[tuple[str, str], ...] = ()
    comments: tuple[str, ...] = ()
    preambles: tuple[str, ...] = ()

    @property
    def blocking(self) -> bool:
        return any(item.blocking for item in self.diagnostics)


@dataclass(frozen=True)
class MappedBibEntry:
    source: BibEntry
    record: ReferenceRecord | None
    diagnostics: tuple[BibDiagnostic, ...] = ()

    @property
    def importable(self) -> bool:
        return self.record is not None and not any(item.blocking for item in self.diagnostics)


@dataclass(frozen=True)
class BibImportItem:
    index: int
    source_line: int
    source_key: str
    record: ReferenceRecord | None
    collision: str
    target_key: str
    allowed_actions: tuple[str, ...]
    default_action: str
    status: str
    diagnostics: tuple[BibDiagnostic, ...] = ()
    existing_record: ReferenceRecord | None = None


@dataclass(frozen=True)
class BibImportPreview:
    format: str
    items: tuple[BibImportItem, ...]
    diagnostics: tuple[BibDiagnostic, ...]
    comments: int
    preambles: int
    strings: int

    @property
    def importable_count(self) -> int:
        return sum(item.record is not None for item in self.items)


@dataclass(frozen=True)
class BibImportDecision:
    index: int
    action: str


@dataclass(frozen=True)
class BibImportProjection:
    records: tuple[ReferenceRecord, ...]
    imported: int
    replaced: int
    merged: int
    skipped: int
    rekeyed: int
    messages: tuple[str, ...]


@dataclass(frozen=True)
class BibExportArtifact:
    format: str
    text: str
    reference_count: int
    warnings: tuple[str, ...] = ()


def _line_col(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    last = text.rfind("\n", 0, offset)
    return line, offset + 1 if last < 0 else offset - last


def _balanced_outer(value: str) -> bool:
    if len(value) < 2 or value[0] != "{" or value[-1] != "}":
        return False
    depth = 0
    quote = False
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"' and depth == 0:
            quote = not quote
        if quote:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and index != len(value) - 1:
                return False
            if depth < 0:
                return False
    return depth == 0


def _strip_outer(value: str) -> str:
    value = value.strip()
    while _balanced_outer(value):
        value = value[1:-1].strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    return value


def _split_top_level(text: str, separator: str = ",") -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote = False
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"' and depth == 0:
            quote = not quote
            continue
        if quote:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
        elif char == separator and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return parts


def _split_and_names(text: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote = False
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if char == "\\":
            escaped = True
            index += 1
            continue
        if char == '"' and depth == 0:
            quote = not quote
            index += 1
            continue
        if not quote:
            if char == "{":
                depth += 1
            elif char == "}":
                depth = max(0, depth - 1)
            elif depth == 0 and text[index:index + 5].casefold() == " and ":
                parts.append(text[start:index])
                start = index + 5
                index += 5
                continue
        index += 1
    parts.append(text[start:])
    return [part.strip() for part in parts if part.strip()]


def _split_concat(text: str) -> list[str]:
    return [part.strip() for part in _split_top_level(text, "#") if part.strip()]


def _find_matching_block(text: str, opening: int) -> int | None:
    """Return the matching entry delimiter without treating protected text as syntax.

    Parenthesis-delimited BibTeX entries may legally contain unmatched
    parentheses inside braced field values.  Track brace depth independently so
    those characters cannot close the outer block.
    """
    opener = text[opening]
    closer = "}" if opener == "{" else ")"
    depth = 0
    brace_depth = 0
    quote = False
    escaped = False
    for index in range(opening, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if opener == "(" and not quote:
            if char == "{":
                brace_depth += 1
                continue
            if char == "}" and brace_depth:
                brace_depth -= 1
                continue
        if char == '"' and depth == 1 and brace_depth == 0:
            quote = not quote
            continue
        if quote or brace_depth:
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    return None


def _parse_atom(atom: str, strings: Mapping[str, str]) -> tuple[str, str | None]:
    value = atom.strip()
    if not value:
        return "", "empty value atom"
    if value[0] == "{" and _balanced_outer(value):
        return value[1:-1], None
    if value[0] == '"' and value[-1:] == '"':
        return value[1:-1], None
    if re.fullmatch(r"[+-]?\d+", value):
        return value, None
    key = value.casefold()
    if key in strings:
        return strings[key], None
    if key in _MONTHS:
        return _MONTHS[key], None
    return value, f"undefined string macro: {value}"


def _parse_value(expression: str, strings: Mapping[str, str]) -> tuple[str, tuple[str, ...]]:
    values: list[str] = []
    warnings: list[str] = []
    for atom in _split_concat(expression):
        value, warning = _parse_atom(atom, strings)
        values.append(value)
        if warning:
            warnings.append(warning)
    return "".join(values).strip(), tuple(warnings)


def parse_bibliography(text: str, format: str) -> BibLibrary:
    """Parse enough of BibTeX/BibLaTeX for safe, preview-first Calamus import.

    Malformed blocks are diagnosed and retained as non-importable evidence.  A
    malformed block never silently overwrites a prior entry.
    """
    if format not in BIB_FORMATS:
        raise ValueError("format must be bibtex or biblatex")
    if not isinstance(text, str):
        raise TypeError("bibliography must be text")

    diagnostics: list[BibDiagnostic] = []
    entries: list[BibEntry] = []
    comments: list[str] = []
    preambles: list[str] = []
    strings: dict[str, str] = {}
    seen_keys: dict[str, int] = {}
    cursor = 0
    entry_index = 0

    while True:
        marker = text.find("@", cursor)
        if marker < 0:
            break
        name_match = re.match(r"@\s*([A-Za-z]+)\s*", text[marker:])
        if not name_match:
            line, col = _line_col(text, marker)
            diagnostics.append(BibDiagnostic(line, col, "invalid-block", "Expected a block type after @.", True))
            cursor = marker + 1
            continue
        block_type = name_match.group(1).casefold()
        opening = marker + name_match.end()
        if opening >= len(text) or text[opening] not in "{(":
            line, col = _line_col(text, opening)
            diagnostics.append(BibDiagnostic(line, col, "invalid-block", f"@{block_type} has no opening delimiter.", True))
            cursor = opening
            continue
        closing = _find_matching_block(text, opening)
        if closing is None:
            line, col = _line_col(text, opening)
            diagnostics.append(BibDiagnostic(line, col, "unclosed-block", f"@{block_type} is not closed.", True))
            break
        raw = text[marker:closing + 1]
        body = text[opening + 1:closing]
        line, col = _line_col(text, marker)
        cursor = closing + 1

        if block_type == "comment":
            comments.append(body.strip())
            continue
        if block_type == "preamble":
            value, warnings = _parse_value(body, strings)
            preambles.append(value)
            for warning in warnings:
                diagnostics.append(BibDiagnostic(line, col, "preamble-warning", warning, False))
            continue
        if block_type == "string":
            assignments = _split_top_level(body)
            for assignment in assignments:
                if not assignment.strip():
                    continue
                if "=" not in assignment:
                    diagnostics.append(BibDiagnostic(line, col, "invalid-string", "@string assignment has no =.", True))
                    continue
                name, expression = assignment.split("=", 1)
                key = name.strip().casefold()
                if not _FIELD_NAME_RE.fullmatch(name.strip()):
                    diagnostics.append(BibDiagnostic(line, col, "invalid-string", f"Invalid @string name: {name.strip()}.", True))
                    continue
                value, warnings = _parse_value(expression, strings)
                strings[key] = value
                for warning in warnings:
                    diagnostics.append(BibDiagnostic(line, col, "string-warning", warning, False))
            continue

        parts = _split_top_level(body)
        key = parts[0].strip() if parts else ""
        if not key:
            diagnostics.append(BibDiagnostic(line, col, "missing-key", f"@{block_type} has no citation key.", True))
            continue
        fields: list[tuple[str, str]] = []
        seen_fields: set[str] = set()
        for chunk in parts[1:]:
            if not chunk.strip():
                continue
            if "=" not in chunk:
                diagnostics.append(BibDiagnostic(line, col, "invalid-field", f"{key}: field has no =: {chunk.strip()[:60]}", True))
                continue
            name, expression = chunk.split("=", 1)
            field = name.strip().casefold()
            if not _FIELD_NAME_RE.fullmatch(name.strip()):
                diagnostics.append(BibDiagnostic(line, col, "invalid-field-name", f"{key}: invalid field name {name.strip()}.", True))
                continue
            if field in seen_fields:
                diagnostics.append(BibDiagnostic(line, col, "duplicate-field", f"{key}: duplicate field {field}.", True))
                continue
            seen_fields.add(field)
            value, warnings = _parse_value(expression, strings)
            fields.append((field, value))
            for warning in warnings:
                diagnostics.append(BibDiagnostic(line, col, "undefined-string", f"{key}.{field}: {warning}", False))
        entry = BibEntry(entry_index, line, block_type, key, tuple(fields), raw)
        if key in seen_keys:
            diagnostics.append(BibDiagnostic(line, col, "duplicate-key", f"Duplicate input citation key: {key}.", True))
        else:
            seen_keys[key] = entry_index
        entries.append(entry)
        entry_index += 1

    return BibLibrary(
        format,
        tuple(entries),
        tuple(diagnostics),
        tuple(strings.items()),
        tuple(comments),
        tuple(preambles),
    )


_COMBINING_ACCENTS = {
    "'": "\u0301", "`": "\u0300", '"': "\u0308", "^": "\u0302",
    "~": "\u0303", "c": "\u0327", "v": "\u030c", "H": "\u030b",
    "u": "\u0306", "=": "\u0304", ".": "\u0307", "r": "\u030a",
    "k": "\u0328", "b": "\u0331", "d": "\u0323",
}
_SIMPLE_COMMANDS = {
    "ae": "æ", "AE": "Æ", "oe": "œ", "OE": "Œ", "aa": "å", "AA": "Å",
    "o": "ø", "O": "Ø", "l": "ł", "L": "Ł", "ss": "ß",
    "textbackslash": "\\", "textasciitilde": "~", "textasciicircum": "^",
    "&": "&", "%": "%", "_": "_", "#": "#", "$": "$", "{": "{", "}": "}",
}


def decode_latex(value: str) -> tuple[str, tuple[str, ...]]:
    """Decode a conservative, deterministic LaTeX subset to Unicode.

    Unknown commands remain visible and are reported instead of being dropped.
    """
    if not isinstance(value, str):
        raise TypeError("LaTeX value must be text")
    text = value
    warnings: list[str] = []

    # Common one-letter accent commands, with or without braces.  Unicode
    # composition gives wider language coverage than a hand-written table.
    accent_re = re.compile(
        r"\\(?:([\'`\"^~=\.])\s*\{?([A-Za-z])\}?|([cvHurkbd])(?:\s*\{([A-Za-z])\}|\s+([A-Za-z])))"
    )
    def accent_replace(match):
        accent = match.group(1) or match.group(3)
        letter = match.group(2) or match.group(4) or match.group(5)
        combining = _COMBINING_ACCENTS.get(accent)
        if combining:
            return unicodedata.normalize("NFC", letter + combining)
        warnings.append(f"unsupported accent command: {match.group(0)}")
        return match.group(0)
    text = accent_re.sub(accent_replace, text)

    # Transparent formatting commands whose textual argument is retained.
    transparent = re.compile(r"\\(?:emph|textit|textbf|textrm|textsc|texttt|url)\*?\s*\{([^{}]*)\}")
    previous = None
    while previous != text:
        previous = text
        text = transparent.sub(lambda match: match.group(1), text)

    # Simple commands.
    simple_re = re.compile(r"\\(AE|OE|AA|[a-zA-Z]+|[&%_#$\{\}])(?:\s*\{\})?")
    def simple_replace(match):
        command = match.group(1)
        if command in _SIMPLE_COMMANDS:
            return _SIMPLE_COMMANDS[command]
        warnings.append(f"unknown LaTeX command: \\{command}")
        return match.group(0)
    text = simple_re.sub(simple_replace, text)

    # Braces used only for case protection are not an internal authority.
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text).strip()
    return unicodedata.normalize("NFC", text), tuple(dict.fromkeys(warnings))


def _is_corporate_name(value: str) -> bool:
    stripped = value.strip()
    return _balanced_outer(stripped)


def parse_person_names(value: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    names: list[str] = []
    warnings: list[str] = []
    for raw_name in _split_and_names(value):
        corporate = _is_corporate_name(raw_name)
        decoded, name_warnings = decode_latex(_strip_outer(raw_name))
        warnings.extend(name_warnings)
        if not decoded:
            continue
        if corporate:
            names.append(decoded)
            continue
        comma_parts = [part.strip() for part in _split_top_level(decoded) if part.strip()]
        if len(comma_parts) == 2:
            family, given = comma_parts
            names.append(f"{family}, {given}" if given else family)
        elif len(comma_parts) >= 3:
            family, suffix, given = comma_parts[0], comma_parts[1], ", ".join(comma_parts[2:])
            display = f"{family}, {given}" if given else family
            if suffix:
                display += f", {suffix}"
            names.append(display)
        else:
            tokens = decoded.split()
            if len(tokens) <= 1:
                names.append(decoded)
                continue
            family_start = next(
                (index for index, token in enumerate(tokens[:-1]) if token[:1].islower()),
                len(tokens) - 1,
            )
            given = " ".join(tokens[:family_start])
            family = " ".join(tokens[family_start:])
            names.append(f"{family}, {given}" if given else family)
    return tuple(names), tuple(dict.fromkeys(warnings))


def _split_keywords(value: str) -> tuple[str, ...]:
    parts = re.split(r"[;,]", value)
    return tuple(dict.fromkeys(item.strip() for item in parts if item.strip()))


def map_bib_entry(entry: BibEntry, format: str) -> MappedBibEntry:
    if format not in BIB_FORMATS:
        raise ValueError("format must be bibtex or biblatex")
    fields = entry.field_map()
    diagnostics: list[BibDiagnostic] = []

    decoded: dict[str, str] = {}
    for name, value in fields.items():
        converted, warnings = decode_latex(value)
        decoded[name] = converted
        for warning in warnings:
            diagnostics.append(BibDiagnostic(entry.line, 1, "latex-warning", f"{entry.key}.{name}: {warning}", False))

    title = decoded.get("title", "").strip()
    if not title:
        diagnostics.append(BibDiagnostic(entry.line, 1, "missing-title", f"{entry.key}: title is required by Calamus.", True))
        return MappedBibEntry(entry, None, tuple(diagnostics))

    authors, author_warnings = parse_person_names(fields.get("author", ""))
    editors, editor_warnings = parse_person_names(fields.get("editor", ""))
    for warning in (*author_warnings, *editor_warnings):
        diagnostics.append(BibDiagnostic(entry.line, 1, "name-warning", f"{entry.key}: {warning}", False))

    source_type = entry.entry_type.casefold()
    record_type = _TYPE_TO_CALAMUS.get(source_type, "other")
    consumed = {
        "author", "editor", "title", "publisher", "volume", "pages",
        "doi", "isbn", "issn", "url", "file", "keywords",
    }

    def choose(*names: str) -> str:
        for name in names:
            value = decoded.get(name, "")
            if value:
                consumed.add(name)
                return value
        return ""

    year = choose("date", "year") if format == BIBLATEX else choose("year", "date")
    if record_type == "journal-article":
        container = choose("journaltitle", "journal") if format == BIBLATEX else choose("journal", "journaltitle")
    elif record_type in {"book-chapter", "conference-paper", "encyclopedia-entry"}:
        container = choose("booktitle")
    else:
        container = (
            choose("journaltitle", "journal", "booktitle")
            if format == BIBLATEX
            else choose("journal", "booktitle", "journaltitle")
        )
    location = choose("location", "address") if format == BIBLATEX else choose("address", "location")
    issue = choose("number", "issue")
    language = choose("langid", "language") if format == BIBLATEX else choose("language", "langid")
    annotation = (
        choose("annotation", "abstract", "note")
        if format == BIBLATEX
        else choose("note", "abstract", "annotation")
    )
    tags = _split_keywords(decoded.get("keywords", ""))

    extras: list[tuple[str, str]] = []
    for name, value in decoded.items():
        if name not in consumed and value:
            extras.append((name, value))
            if name in _NATIVE_FIELDS:
                diagnostics.append(BibDiagnostic(
                    entry.line, 1, "preserved-alternate-field",
                    f"{entry.key}.{name}: preserved as an extra field because the selected {format} mapping uses another native slot.",
                    False,
                ))
    if source_type not in _TYPE_TO_CALAMUS:
        extras.insert(0, ("bib-entry-type", source_type))
        diagnostics.append(BibDiagnostic(
            entry.line, 1, "type-mapping",
            f"{entry.key}: unsupported entry type {source_type} mapped to other and preserved.",
            False,
        ))
    elif _CALAMUS_TO_TYPE_BIBLATEX.get(record_type) != source_type and _CALAMUS_TO_TYPE_BIBTEX.get(record_type) != source_type:
        extras.insert(0, ("bib-entry-type", source_type))
        diagnostics.append(BibDiagnostic(
            entry.line, 1, "type-mapping",
            f"{entry.key}: entry type {source_type} mapped to {record_type}; the original type is preserved.",
            False,
        ))

    try:
        record = ReferenceRecord(
            key=entry.key,
            title=title,
            type=record_type,
            authors=authors,
            year=year,
            editors=editors,
            container_title=container,
            publisher=decoded.get("publisher", ""),
            location=location,
            volume=decoded.get("volume", ""),
            issue=issue,
            pages=decoded.get("pages", ""),
            doi=decoded.get("doi", ""),
            isbn=decoded.get("isbn", ""),
            issn=decoded.get("issn", ""),
            url=decoded.get("url", ""),
            language=language,
            file_path=decoded.get("file", ""),
            tags=tags,
            annotation=annotation,
            extra_fields=tuple(extras),
        )
    except ValueError as error:
        diagnostics.append(BibDiagnostic(entry.line, 1, "invalid-record", f"{entry.key}: {error}", True))
        return MappedBibEntry(entry, None, tuple(diagnostics))
    return MappedBibEntry(entry, record, tuple(diagnostics))


def _record_content_signature(record: ReferenceRecord) -> tuple:
    return (
        record.title.casefold(), record.type, tuple(item.casefold() for item in record.authors),
        record.year, tuple(item.casefold() for item in record.editors),
        record.container_title.casefold(), record.publisher.casefold(), record.location.casefold(),
        record.volume, record.issue, record.pages, record.doi.casefold(), record.isbn.casefold(),
        record.issn.casefold(), record.url.casefold(), record.language.casefold(),
        tuple(tag.casefold() for tag in record.tags), record.annotation.strip(),
        tuple((name.casefold(), value) for name, value in record.extra_fields),
    )


def _probable_duplicate_key(record: ReferenceRecord, existing: Sequence[ReferenceRecord]) -> str | None:
    doi = record.doi.casefold().strip()
    isbn = re.sub(r"[^0-9Xx]", "", record.isbn)
    title = record.title.casefold().strip()
    author = record.primary_author.casefold().strip()
    year = record.year.strip()
    for item in existing:
        if doi and item.doi.casefold().strip() == doi:
            return item.key
        if isbn and re.sub(r"[^0-9Xx]", "", item.isbn) == isbn:
            return item.key
        if title and item.title.casefold().strip() == title and item.year.strip() == year:
            if not author or item.primary_author.casefold().strip() == author:
                return item.key
    return None


def build_import_preview(
    library: BibLibrary,
    existing: Sequence[ReferenceRecord],
) -> BibImportPreview:
    if not isinstance(library, BibLibrary):
        raise TypeError("library must be BibLibrary")
    existing_by_key = {record.key: record for record in existing}
    identity_owner = {identity: record.key for record in existing for identity in record.identity_keys}
    input_counts: dict[str, int] = {}
    for entry in library.entries:
        input_counts[entry.key] = input_counts.get(entry.key, 0) + 1

    items: list[BibImportItem] = []
    for entry in library.entries:
        mapped = map_bib_entry(entry, library.format)
        entry_diagnostics = tuple(
            item for item in library.diagnostics
            if item.line == entry.line and item.code != "duplicate-key"
        )
        combined_diagnostics = tuple((*mapped.diagnostics, *entry_diagnostics))
        record = mapped.record
        if record is None or any(item.blocking for item in combined_diagnostics):
            items.append(BibImportItem(
                index=entry.index,
                source_line=entry.line,
                source_key=entry.key,
                record=None,
                collision="invalid",
                target_key="",
                allowed_actions=(ACTION_SKIP,),
                default_action=ACTION_SKIP,
                status="Invalid entry",
                diagnostics=combined_diagnostics,
                existing_record=None,
            ))
            continue
        if input_counts.get(record.key, 0) > 1:
            collision = COLLISION_INPUT
            target = ""
            allowed = (ACTION_SKIP, ACTION_NEW_KEY)
            default = ACTION_SKIP
            status = "Duplicate key inside input"
        elif record.key in existing_by_key:
            target = record.key
            if _record_content_signature(record) == _record_content_signature(existing_by_key[record.key]):
                collision = COLLISION_SAME
                allowed = (ACTION_SKIP, ACTION_REPLACE)
                default = ACTION_SKIP
                status = "Same key and equivalent content"
            else:
                collision = COLLISION_KEY
                allowed = (ACTION_SKIP, ACTION_REPLACE, ACTION_MERGE, ACTION_NEW_KEY)
                default = ACTION_SKIP
                status = "Existing key has different content"
        elif record.key in identity_owner:
            collision = COLLISION_ALIAS
            target = identity_owner[record.key]
            allowed = (ACTION_SKIP, ACTION_NEW_KEY)
            default = ACTION_SKIP
            status = f"Key collides with alias of {target}"
        else:
            probable = _probable_duplicate_key(record, existing)
            if probable:
                collision = COLLISION_PROBABLE
                target = probable
                allowed = (ACTION_SKIP, ACTION_IMPORT, ACTION_MERGE, ACTION_NEW_KEY)
                default = ACTION_SKIP
                status = f"Probable duplicate of {probable}"
            else:
                collision = COLLISION_NONE
                target = ""
                allowed = (ACTION_IMPORT, ACTION_SKIP, ACTION_NEW_KEY)
                default = ACTION_IMPORT
                status = "New reference"
        items.append(BibImportItem(
            index=entry.index,
            source_line=entry.line,
            source_key=entry.key,
            record=record,
            collision=collision,
            target_key=target,
            allowed_actions=allowed,
            default_action=default,
            status=status,
            diagnostics=mapped.diagnostics,
            existing_record=existing_by_key.get(target) if target else None,
        ))
    all_diagnostics = list(library.diagnostics)
    for item in items:
        all_diagnostics.extend(item.diagnostics)
    return BibImportPreview(
        library.format,
        tuple(items),
        tuple(dict.fromkeys(all_diagnostics)),
        len(library.comments), len(library.preambles), len(library.strings),
    )


def _merge_records(existing: ReferenceRecord, incoming: ReferenceRecord, *, preserve_incoming_key_alias: bool = True) -> ReferenceRecord:
    def scalar(name: str):
        current = getattr(existing, name)
        return current if current else getattr(incoming, name)
    def many(name: str):
        current = tuple(getattr(existing, name))
        incoming_values = tuple(getattr(incoming, name))
        if name == "tags":
            return tuple(dict.fromkeys((*current, *incoming_values)))
        return current if current else incoming_values
    aliases = list(existing.aliases)
    for alias in incoming.aliases:
        if alias != existing.key and alias not in aliases:
            aliases.append(alias)
    if preserve_incoming_key_alias and incoming.key != existing.key and incoming.key not in aliases:
        aliases.append(incoming.key)
    existing_extra = {name.casefold() for name, _ in existing.extra_fields}
    extras = list(existing.extra_fields)
    for name, value in incoming.extra_fields:
        if name.casefold() not in existing_extra:
            extras.append((name, value))
            existing_extra.add(name.casefold())
    return ReferenceRecord(
        key=existing.key,
        title=scalar("title"),
        type=existing.type if existing.type != "other" else incoming.type,
        authors=many("authors"),
        year=scalar("year"),
        editors=many("editors"),
        container_title=scalar("container_title"),
        publisher=scalar("publisher"),
        location=scalar("location"),
        volume=scalar("volume"),
        issue=scalar("issue"),
        pages=scalar("pages"),
        doi=scalar("doi"),
        isbn=scalar("isbn"),
        issn=scalar("issn"),
        url=scalar("url"),
        language=scalar("language"),
        file_path=scalar("file_path"),
        aliases=tuple(aliases),
        tags=many("tags"),
        annotation=scalar("annotation"),
        extra_fields=tuple(extras),
    )


def apply_import_decisions(
    preview: BibImportPreview,
    existing: Sequence[ReferenceRecord],
    decisions: Sequence[BibImportDecision],
) -> BibImportProjection:
    if not isinstance(preview, BibImportPreview):
        raise TypeError("preview must be BibImportPreview")
    decision_map = {decision.index: decision.action for decision in decisions}
    if len(decision_map) != len(decisions):
        raise ValueError("duplicate decision index")
    records = list(existing)
    imported = replaced = merged = skipped = rekeyed = 0
    messages: list[str] = []

    for item in preview.items:
        action = decision_map.get(item.index, item.default_action)
        if action not in item.allowed_actions:
            raise ValueError(f"Action {action} is not allowed for {item.source_key}")
        if action == ACTION_SKIP or item.record is None:
            skipped += 1
            continue
        incoming = item.record
        identities = {identity for record in records for identity in record.identity_keys}
        if action == ACTION_NEW_KEY:
            new_key = suggest_reference_key(incoming.authors, incoming.year, incoming.title, identities)
            incoming = incoming.with_key(new_key, preserve_old_alias=False)
            if incoming.key in identities:
                raise ValueError(f"Could not generate a unique key for {item.source_key}")
            records.append(incoming)
            imported += 1
            rekeyed += 1
            messages.append(f"{item.source_key} imported as {incoming.key}")
            continue
        if action == ACTION_IMPORT:
            if incoming.key in identities:
                raise ValueError(f"Reference identity already exists: {incoming.key}")
            records.append(incoming)
            imported += 1
            continue
        target_key = item.target_key or incoming.key
        position = next((index for index, record in enumerate(records) if record.key == target_key), None)
        if position is None:
            raise ValueError(f"Collision target no longer exists: {target_key}")
        if action == ACTION_REPLACE:
            old = records[position]
            aliases = tuple(dict.fromkeys((*old.aliases, *incoming.aliases)))
            replacement = replace(incoming, key=old.key, aliases=aliases)
            records[position] = replacement
            replaced += 1
        elif action == ACTION_MERGE:
            records[position] = _merge_records(records[position], incoming)
            merged += 1
        else:
            raise ValueError(f"Unsupported import action: {action}")

    # Final authority integrity gate.
    owners: dict[str, str] = {}
    for record in records:
        for identity in record.identity_keys:
            prior = owners.get(identity)
            if prior is not None and prior != record.key:
                raise ValueError(f"Reference identity collision after import: {identity}")
            owners[identity] = record.key
    return BibImportProjection(tuple(records), imported, replaced, merged, skipped, rekeyed, tuple(messages))


def _escape_bib_value(value: str) -> str:
    text = unicodedata.normalize("NFC", value or "")
    placeholder = ""
    text = text.replace("\\", placeholder)
    for char in ("%", "&", "_", "#", "$"):
        text = text.replace(char, "\\" + char)
    text = text.replace("{", r"\{").replace("}", r"\}")
    return text.replace(placeholder, r"\textbackslash{}")


_BIBLATEX_LITERAL_LIST_FIELDS = frozenset({"publisher", "location"})


def _literal_list_atom_to_bib(value: str) -> str:
    """Encode one Calamus scalar as one BibLaTeX literal-list atom.

    BibLaTeX treats fields such as ``publisher`` and ``location`` as literal
    lists and uses the token ``and`` as the item separator.  Calamus models
    both fields as one canonical scalar, so an additional brace group is
    required to keep values such as ``Herder and Herder`` as one item when
    Pandoc/citeproc reads the transient bibliography.
    """
    return "{" + _escape_bib_value(value) + "}"


def _person_to_bib(name: str) -> str:
    """Encode one canonical Calamus display name as a BibTeX name atom.

    Multi-word names without a comma are treated as corporate authors and kept
    inside a protected group.  The group braces are syntax and must not be
    escaped as literal characters.
    """
    value = (name or "").strip()
    if not value:
        return ""
    escaped = _escape_bib_value(value)
    if "," in value or len(value.split()) <= 1:
        return escaped
    return "{" + escaped + "}"


def _people_to_bib(names: Sequence[str]) -> str:
    return " and ".join(part for part in (_person_to_bib(name) for name in names) if part)


def _valid_extra_field(name: str) -> bool:
    return bool(_FIELD_NAME_RE.fullmatch(name or ""))


def export_references(records: Iterable[ReferenceRecord], format: str) -> BibExportArtifact:
    if format not in BIB_FORMATS:
        raise ValueError("format must be bibtex or biblatex")
    rows = tuple(records)
    if any(not isinstance(record, ReferenceRecord) for record in rows):
        raise TypeError("records must contain ReferenceRecord values")
    warnings: list[str] = []
    blocks: list[str] = []
    type_map = _CALAMUS_TO_TYPE_BIBLATEX if format == BIBLATEX else _CALAMUS_TO_TYPE_BIBTEX

    for record in rows:
        extra_map = dict(record.extra_fields)
        original_type = extra_map.get("bib-entry-type", "").strip().casefold()
        if original_type and _FIELD_NAME_RE.fullmatch(original_type):
            entry_type = original_type
        else:
            entry_type = type_map.get(record.type, "misc")
            if record.type not in type_map:
                warnings.append(f"{record.key}: internal type {record.type} exported as misc")
            lossy_types = {
                BIBTEX: {"encyclopedia-entry", "thesis", "institutional-document", "website", "other"},
                BIBLATEX: {"institutional-document", "other"},
            }
            if record.type in lossy_types[format]:
                warnings.append(f"{record.key}: internal type {record.type} is represented as {entry_type} in {format}")

        fields: list[tuple[str, str]] = []
        if record.authors:
            fields.append(("author", _people_to_bib(record.authors)))
        if record.editors:
            fields.append(("editor", _people_to_bib(record.editors)))
        fields.append(("title", record.title))
        if record.year:
            field = "date" if format == BIBLATEX and re.search(r"[-/]", record.year) else "year"
            fields.append((field, record.year))
            if format == BIBTEX and re.search(r"[-/]", record.year):
                warnings.append(f"{record.key}: full date {record.year!r} is emitted in the BibTeX year field")
        if record.container_title:
            if record.type == "journal-article":
                fields.append(("journaltitle" if format == BIBLATEX else "journal", record.container_title))
            else:
                fields.append(("booktitle", record.container_title))
        if record.publisher:
            fields.append(("publisher", record.publisher))
        if record.location:
            fields.append(("location" if format == BIBLATEX else "address", record.location))
        for name, value in (
            ("volume", record.volume),
            ("number", record.issue),
            ("pages", record.pages),
            ("doi", record.doi),
            ("isbn", record.isbn),
            ("issn", record.issn),
            ("url", record.url),
            ("langid" if format == BIBLATEX else "language", record.language),
            ("file", record.file_path),
        ):
            if value:
                fields.append((name, value))
        if record.tags:
            fields.append(("keywords", ", ".join(record.tags)))
        if record.annotation:
            fields.append(("annotation" if format == BIBLATEX else "note", record.annotation))

        occupied = {name.casefold() for name, _ in fields}
        occupied.add("bib-entry-type")
        for name, value in record.extra_fields:
            key = name.strip().casefold()
            if not value:
                continue
            if key in occupied:
                warnings.append(f"{record.key}: extra field {name!r} was omitted because the canonical mapping already owns {key}")
                continue
            if not _valid_extra_field(key):
                warnings.append(f"{record.key}: extra field {name!r} was not representable")
                continue
            fields.append((key, value))
            occupied.add(key)

        lines = [f"@{entry_type}{{{record.key},"]
        for index, (name, value) in enumerate(fields):
            comma = "," if index < len(fields) - 1 else ""
            if name in {"author", "editor"}:
                rendered = value
            elif format == BIBLATEX and name in _BIBLATEX_LITERAL_LIST_FIELDS:
                rendered = _literal_list_atom_to_bib(value)
            else:
                rendered = _escape_bib_value(value)
            lines.append(f"  {name} = {{{rendered}}}{comma}")
        lines.append("}")
        blocks.append("\n".join(lines))

    text = "\n\n".join(blocks)
    if text:
        text += "\n"
    return BibExportArtifact(format, text, len(rows), tuple(dict.fromkeys(warnings)))
