"""Canonical descriptors for document-owned Calamus Markdown sidecars."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


@dataclass(frozen=True)
class ManagedSidecarSpec:
    key: str
    label: str
    suffix: str

    def __post_init__(self) -> None:
        if not self.key or not self.label or not self.suffix.startswith("."):
            raise ValueError("managed sidecar fields are required")


SOURCE_NOTES_SIDECAR = ManagedSidecarSpec(
    "source-notes",
    "Source Notes",
    ".source-notes.md",
)
SCRATCHPAD_SIDECAR = ManagedSidecarSpec(
    "scratchpad",
    "Scratchpad",
    ".scratchpad.md",
)
MANAGED_DOCUMENT_SIDECARS = (SOURCE_NOTES_SIDECAR, SCRATCHPAD_SIDECAR)
MANAGED_DOCUMENT_SIDECAR_SUFFIXES = tuple(item.suffix for item in MANAGED_DOCUMENT_SIDECARS)

SOURCE_NOTES_SUFFIX = SOURCE_NOTES_SIDECAR.suffix
SCRATCHPAD_SUFFIX = SCRATCHPAD_SIDECAR.suffix


def document_sidecar_path(document_path: Any, spec: ManagedSidecarSpec) -> str | None:
    """Return the canonical absolute sidecar path owned by *document_path*."""
    if not isinstance(spec, ManagedSidecarSpec):
        raise TypeError("spec must be a ManagedSidecarSpec")
    if not isinstance(document_path, str) or not document_path.strip():
        return None
    document = os.path.abspath(os.path.expanduser(document_path.strip()))
    return document + spec.suffix


def sidecar_spec_for_suffix(suffix: str) -> ManagedSidecarSpec | None:
    if not isinstance(suffix, str):
        return None
    folded = suffix.casefold()
    return next(
        (item for item in MANAGED_DOCUMENT_SIDECARS if item.suffix.casefold() == folded),
        None,
    )


def is_managed_sidecar_name(name: Any) -> bool:
    if not isinstance(name, str):
        return False
    folded = name.casefold()
    return any(folded.endswith(item.suffix.casefold()) for item in MANAGED_DOCUMENT_SIDECARS)
