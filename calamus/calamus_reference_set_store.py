"""Canonical UTF-8 Markdown persistence for Calamus static Reference Sets."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Iterable

from calamus_reference_sets import (
    ReferenceSet,
    ReferenceSetDiagnostic,
    parse_reference_sets_markdown,
    serialize_reference_sets_markdown,
)
from calamus_research_file import FileToken, atomic_write_utf8, file_token


@dataclass(frozen=True)
class ReferenceSetSnapshot:
    sets: tuple[ReferenceSet, ...]
    token: FileToken
    diagnostics: tuple[ReferenceSetDiagnostic, ...] = ()

    @property
    def writable(self) -> bool:
        return not any(item.blocking for item in self.diagnostics)


@dataclass(frozen=True)
class ReferenceSetSaveResult:
    status: str
    token: FileToken
    message: str = ""

    @property
    def saved(self) -> bool:
        return self.status == "saved"


def default_reference_sets_path(home: str | None = None, data_home: str | None = None) -> str:
    base_home = os.path.expanduser(home or "~")
    root = data_home or os.environ.get("XDG_DATA_HOME") or os.path.join(base_home, ".local", "share")
    return os.path.join(root, "calamus", "research", "reference-sets.md")


class MarkdownReferenceSetStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or default_reference_sets_path()

    def load(self) -> ReferenceSetSnapshot:
        token = file_token(self.path)
        if not token.exists:
            return ReferenceSetSnapshot((), token, ())
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError as error:
            return ReferenceSetSnapshot((), token, (ReferenceSetDiagnostic(1, str(error)),))
        sets, diagnostics = parse_reference_sets_markdown(text)
        return ReferenceSetSnapshot(sets, token, diagnostics)

    def save(
        self,
        sets: Iterable[ReferenceSet],
        expected_token: FileToken,
        *,
        force: bool = False,
    ) -> ReferenceSetSaveResult:
        current = file_token(self.path)
        if not force and current != expected_token:
            return ReferenceSetSaveResult("conflict", current, "Reference Sets file changed outside Calamus.")
        try:
            text = serialize_reference_sets_markdown(tuple(sets))
        except (TypeError, ValueError) as error:
            return ReferenceSetSaveResult("error", current, str(error))
        try:
            return ReferenceSetSaveResult("saved", atomic_write_utf8(self.path, text))
        except OSError as error:
            return ReferenceSetSaveResult("error", current, str(error))
