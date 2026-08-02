"""Build disposable W97 Bibliography Manager Core manual authorities."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from calamus_reference_set_store import MarkdownReferenceSetStore, default_reference_sets_path
from calamus_reference_sets import ReferenceSet
from calamus_reference_store import MarkdownReferenceStore, default_references_path
from calamus_references import ReferenceRecord
from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
from calamus_source_notes import SourceLocator, SourceNote


_DOCUMENT = (
    """# W97 Bibliography Manager Core Validation {#w97-bibliography}

This document cites Alpha [@alpha2020, p. 12] and Beta [@beta2021].

## Working section {#working-section}

Use Quick Cite here:"""
    + " \n"
)


def _minimal_pdf_bytes() -> bytes:
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Length 53 >>\nstream\nBT /F1 12 Tf 36 90 Td (Calamus W97 local file) Tj ET\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def build_fixture(document_path: str) -> tuple[Path, Path, Path, Path, Path, Path]:
    document = Path(document_path).expanduser().resolve()
    document.parent.mkdir(parents=True, exist_ok=True)
    document.write_text(_DOCUMENT, encoding="utf-8")

    local_file = document.parent / "Alpha_Local_File.pdf"
    local_file.write_bytes(_minimal_pdf_bytes())
    missing_file = document.parent / "Missing_Gamma_File.pdf"

    reference_path = Path(default_references_path())
    store = MarkdownReferenceStore(str(reference_path))
    result = store.save(
        (
            ReferenceRecord(
                key="alpha2020",
                aliases=("alpha-old",),
                type="book",
                authors=("Rossi, Anna",),
                title="Alpha Book",
                year="2020",
                publisher="Calamus Press",
                location="Treviso",
                isbn="9780000000001",
                language="Italian",
                tags=("theology", "core"),
                file_path=str(local_file),
                annotation="Primary working source.",
                extra_fields=(("Custom", "Patristics"), ("Related Keys", "beta2021")),
            ),
            ReferenceRecord(
                key="beta2021",
                type="journal-article",
                authors=("Bianchi, Bruno",),
                title="Beta Article",
                year="2021",
                container_title="Journal of Calamus Studies",
                volume="4",
                issue="2",
                pages="10-28",
                doi="10.1000/beta",
                tags=("history", "core"),
                extra_fields=(("Related Keys", "alpha2020"),),
            ),
            ReferenceRecord(
                key="gamma2019",
                type="thesis",
                title="Gamma Thesis",
                file_path=str(missing_file),
            ),
            ReferenceRecord(
                key="delta2022",
                type="web-page",
                authors=("Delta Group",),
                title="Delta Web Resource",
                year="2022",
                url="https://example.invalid/delta",
                tags=("unused",),
            ),
        ),
        store.load().token,
    )
    if not result.saved:
        raise RuntimeError(result.message or "could not save W97 references")

    set_path = Path(default_reference_sets_path())
    set_store = MarkdownReferenceSetStore(str(set_path))
    result = set_store.save(
        (ReferenceSet("Core sources", "W97 validation set.", ("alpha2020", "beta2021")),),
        set_store.load().token,
    )
    if not result.saved:
        raise RuntimeError(result.message or "could not save W97 reference sets")

    note_value = source_notes_path(str(document))
    if note_value is None:
        raise RuntimeError("saved W97 document did not receive a Source Notes path")
    note_path = Path(note_value)
    note_store = MarkdownSourceNoteStore(str(note_path))
    result = note_store.save(
        (
            SourceNote(
                id="w97-alpha-note",
                kind="quote",
                text="Alpha quotation for Show Uses.",
                reference_key="alpha2020",
                locator=SourceLocator(page="12"),
                target="#working-section",
                tags=("theology",),
            ),
        ),
        note_store.load().token,
    )
    if not result.saved:
        raise RuntimeError(result.message or "could not save W97 Source Notes")

    settings = Path.home() / ".config" / "calamus" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(
        json.dumps(
            {"width": 1180, "height": 820, "last_file": str(document), "word_wrap": True},
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    for path in (document, local_file, reference_path, set_path, note_path, settings):
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"W97 fixture file missing or empty: {path}")
    reference_text = reference_path.read_text(encoding="utf-8")
    for token in ("## alpha2020", "Custom: Patristics", "## gamma2019", str(missing_file)):
        if token not in reference_text:
            raise RuntimeError(f"W97 fixture token missing: {token}")
    return document, reference_path, set_path, note_path, local_file, settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("document")
    args = parser.parse_args(argv)
    paths = build_fixture(args.document)
    print(f"W97_FIXTURE_DOCUMENT={paths[0]}")
    print(f"W97_FIXTURE_REFERENCES={paths[1]}")
    print(f"W97_FIXTURE_REFERENCE_SETS={paths[2]}")
    print(f"W97_FIXTURE_SOURCE_NOTES={paths[3]}")
    print(f"W97_FIXTURE_LOCAL_FILE={paths[4]}")
    print(f"W97_FIXTURE_SETTINGS={paths[5]}")
    print("W97_BIBLIOGRAPHY_MANUAL_FIXTURE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
