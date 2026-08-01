"""Build the disposable W96 manual-validation authorities.

This module deliberately contains no GTK import.  The package runner and the
preflight execute the same package-qualified entry point.
"""
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

_FILLER = "\n\n".join(
    f"Background paragraph {index}. This line makes destination navigation visibly scroll."
    for index in range(1, 61)
)

_DOCUMENT = (
    "# W96 Document Overview Core Validation {#w96-overview}\n\n"
    "See [Go to Method](#method).\n\n"
    "## Introduction {#introduction}\n\n"
    "Alpha [@alpha, p. 12]. Missing [@missing2026].\n\n"
    "## Background {#background}\n\n"
    + _FILLER
    + "\n\n## Method {#method}\n\nMethod target.\n\n"
    "## Conclusion {#conclusion}\n\nConclusion.\n"
)


def build_fixture(document_path: str) -> tuple[Path, Path, Path, Path, Path]:
    document = Path(document_path).expanduser().resolve()
    document.parent.mkdir(parents=True, exist_ok=True)
    document.write_text(_DOCUMENT, encoding="utf-8")

    references_path = Path(default_references_path())
    reference_store = MarkdownReferenceStore(str(references_path))
    reference_snapshot = reference_store.load()
    references = (
        ReferenceRecord(
            key="alpha",
            title="Alpha: Cited Primary Source",
            authors=("Alpha, Anna",),
            year="2020",
            extra_fields=(("Related Keys", "beta"),),
        ),
        ReferenceRecord(
            key="beta",
            title="Beta: Related Background Source",
            authors=("Beta, Bruno",),
            year="2021",
            extra_fields=(("Related Keys", "alpha"),),
        ),
        ReferenceRecord(
            key="gamma",
            title="Gamma: Set-only Source",
            authors=("Gamma, Giulia",),
            year="2022",
        ),
        ReferenceRecord(
            key="delta",
            title="Delta: Unrelated Global Record",
            authors=("Delta, Davide",),
            year="2023",
        ),
    )
    result = reference_store.save(references, reference_snapshot.token)
    if not result.saved:
        raise RuntimeError(result.message or "could not save W96 references")

    sets_path = Path(default_reference_sets_path())
    set_store = MarkdownReferenceSetStore(str(sets_path))
    set_snapshot = set_store.load()
    result = set_store.save(
        (ReferenceSet("Core sources", "W96 validation.", ("beta", "gamma")),),
        set_snapshot.token,
    )
    if not result.saved:
        raise RuntimeError(result.message or "could not save W96 reference set")

    notes_path_value = source_notes_path(str(document))
    if notes_path_value is None:
        raise RuntimeError("saved W96 document did not receive a sidecar path")
    notes_path = Path(notes_path_value)
    note_store = MarkdownSourceNoteStore(str(notes_path))
    note_snapshot = note_store.load()
    result = note_store.save(
        (
            SourceNote(
                id="w96-method-note",
                kind="quote",
                text="Method quotation",
                reference_key="alpha",
                locator=SourceLocator(page="42"),
                target="#method",
                comment="Disposable W96 validation note.",
                tags=("w96", "method"),
            ),
        ),
        note_snapshot.token,
    )
    if not result.saved:
        raise RuntimeError(result.message or "could not save W96 source note")

    settings_path = Path.home() / ".config" / "calamus" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "width": 1120,
                "height": 780,
                "last_file": str(document),
                "word_wrap": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    _verify_fixture(document, references_path, sets_path, notes_path, settings_path)
    return document, references_path, sets_path, notes_path, settings_path


def _verify_fixture(
    document: Path,
    references_path: Path,
    sets_path: Path,
    notes_path: Path,
    settings_path: Path,
) -> None:
    for path in (document, references_path, sets_path, notes_path, settings_path):
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"W96 fixture file missing or empty: {path}")
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    if settings.get("last_file") != str(document):
        raise RuntimeError("W96 settings do not point to the fixture document")
    if "[@missing2026]" not in document.read_text(encoding="utf-8"):
        raise RuntimeError("W96 unresolved-citation fixture is missing")
    if "## delta" not in references_path.read_text(encoding="utf-8"):
        raise RuntimeError("W96 unrelated global reference is missing")
    if "Core sources" not in sets_path.read_text(encoding="utf-8"):
        raise RuntimeError("W96 pertinent reference set is missing")
    if "w96-method-note" not in notes_path.read_text(encoding="utf-8"):
        raise RuntimeError("W96 source-note fixture is missing")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("document")
    args = parser.parse_args(argv)
    paths = build_fixture(args.document)
    print(f"W96_FIXTURE_DOCUMENT={paths[0]}")
    print(f"W96_FIXTURE_REFERENCES={paths[1]}")
    print(f"W96_FIXTURE_REFERENCE_SETS={paths[2]}")
    print(f"W96_FIXTURE_SOURCE_NOTES={paths[3]}")
    print(f"W96_FIXTURE_SETTINGS={paths[4]}")
    print("W96_MANUAL_FIXTURE_GENERATOR=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
