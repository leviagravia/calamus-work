"""Canonical Calamus user-guide loading and section parsing."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


_GUIDE_RELATIVE = Path("share/doc/calamus/USER_GUIDE.md")
_FALLBACK = """# Calamus User Guide

## Guide unavailable

The installed user-guide file could not be found. Reinstall Calamus or run it from a complete source bundle.
"""


@dataclass(frozen=True)
class HelpSection:
    title: str
    body: str

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("help section title is required")
        if not isinstance(self.body, str):
            raise TypeError("help section body must be text")


def user_guide_candidates(source_root: str | os.PathLike[str] | None = None) -> tuple[Path, ...]:
    """Return deterministic source and installed guide candidates."""
    roots: list[Path] = []
    explicit = Path(source_root).resolve() if source_root else None
    environment = os.environ.get("CALAMUS_SOURCE_ROOT", "").strip()
    if explicit:
        roots.append(explicit)
    if environment:
        roots.append(Path(environment).resolve())
    roots.append(Path(__file__).resolve().parents[1])

    candidates: list[Path] = []
    for root in roots:
        candidate = root / _GUIDE_RELATIVE
        if candidate not in candidates:
            candidates.append(candidate)
    installed = Path("/usr/share/doc/calamus/USER_GUIDE.md")
    if installed not in candidates:
        candidates.append(installed)
    return tuple(candidates)


def load_user_guide(source_root: str | os.PathLike[str] | None = None) -> str:
    """Load UTF-8 help from source or installed data without mutation."""
    for candidate in user_guide_candidates(source_root):
        try:
            if candidate.is_file():
                text = candidate.read_text(encoding="utf-8")
                if text.strip():
                    return text
        except (OSError, UnicodeError):
            continue
    return _FALLBACK


def parse_user_guide_sections(text: str) -> tuple[HelpSection, ...]:
    """Split the guide at level-two Markdown headings for the GTK navigator."""
    if not isinstance(text, str):
        raise TypeError("user guide must be text")
    preface: list[str] = []
    sections: list[HelpSection] = []
    title: str | None = None
    body: list[str] = []

    def flush() -> None:
        nonlocal title, body
        if title is not None:
            sections.append(HelpSection(title.strip(), "\n".join(body).strip()))
        title = None
        body = []

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            title = line[3:].strip()
        elif title is None:
            if not line.startswith("# "):
                preface.append(line)
        else:
            body.append(line)
    flush()

    preface_text = "\n".join(preface).strip()
    if preface_text:
        sections.insert(0, HelpSection("Overview", preface_text))
    if not sections:
        return (HelpSection("User Guide", text.strip() or _FALLBACK.strip()),)
    return tuple(sections)
