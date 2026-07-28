"""Canonical Calamus user-guide loading and structured navigation parsing."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re


_GUIDE_RELATIVE = Path("share/doc/calamus/USER_GUIDE.md")
_FALLBACK = """# Calamus User Guide

## Guide unavailable

The installed user-guide file could not be found. Reinstall Calamus or run it from a complete source bundle.
"""
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```+|~~~+)")


@dataclass(frozen=True)
class HelpSection:
    """One legacy level-two guide section.

    The flat section API remains available for command wiring and older tests.
    The GTK guide uses :class:`HelpTopic` for hierarchical navigation.
    """

    title: str
    body: str

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("help section title is required")
        if not isinstance(self.body, str):
            raise TypeError("help section body must be text")


@dataclass(frozen=True)
class HelpTopic:
    """One navigable Markdown heading and its subtree body."""

    title: str
    body: str
    level: int
    parent_index: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("help topic title is required")
        if not isinstance(self.body, str):
            raise TypeError("help topic body must be text")
        if not 1 <= int(self.level) <= 6:
            raise ValueError("help topic level must be between 1 and 6")
        if self.parent_index is not None and self.parent_index < 0:
            raise ValueError("help topic parent index cannot be negative")


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


def _markdown_headings(text: str) -> tuple[tuple[int, int, str], ...]:
    """Return ``(line_index, level, title)`` headings outside code fences."""
    headings: list[tuple[int, int, str]] = []
    fence_marker: str | None = None
    for line_index, line in enumerate(text.splitlines()):
        fence = _FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)[0]
            if fence_marker is None:
                fence_marker = marker
            elif fence_marker == marker:
                fence_marker = None
            continue
        if fence_marker is not None:
            continue
        match = _HEADING_RE.match(line)
        if match:
            headings.append((line_index, len(match.group(1)), match.group(2).strip()))
    return tuple(headings)


def parse_user_guide_sections(text: str) -> tuple[HelpSection, ...]:
    """Split the guide at real level-two headings, excluding fenced examples."""
    if not isinstance(text, str):
        raise TypeError("user guide must be text")
    lines = text.splitlines()
    h2 = tuple(item for item in _markdown_headings(text) if item[1] == 2)
    if not h2:
        return (HelpSection("User Guide", text.strip() or _FALLBACK.strip()),)

    sections: list[HelpSection] = []
    first_line = h2[0][0]
    preface = "\n".join(
        line for line in lines[:first_line] if not line.startswith("# ")
    ).strip()
    if preface:
        sections.append(HelpSection("Overview", preface))

    for index, (line_index, _level, title) in enumerate(h2):
        end = h2[index + 1][0] if index + 1 < len(h2) else len(lines)
        body = "\n".join(lines[line_index + 1:end]).strip()
        sections.append(HelpSection(title, body))
    return tuple(sections)


def parse_user_guide_topics(
    text: str,
    *,
    minimum_level: int = 2,
    maximum_level: int = 4,
) -> tuple[HelpTopic, ...]:
    """Build a deterministic H2–H4 hierarchy for the GTK Help Navigator.

    A topic body includes its subordinate headings and text, but stops before
    the next heading at the same or a higher level. Markdown headings inside
    fenced examples never become navigator entries.
    """
    if not isinstance(text, str):
        raise TypeError("user guide must be text")
    if not 1 <= minimum_level <= maximum_level <= 6:
        raise ValueError("invalid guide topic level range")

    lines = text.splitlines()
    all_headings = _markdown_headings(text)
    selected = tuple(
        item for item in all_headings if minimum_level <= item[1] <= maximum_level
    )
    if not selected:
        fallback = text.strip() or _FALLBACK.strip()
        return (HelpTopic("User Guide", fallback, 1, None),)

    topics: list[HelpTopic] = []
    first_line = selected[0][0]
    preface = "\n".join(
        line for line in lines[:first_line] if not line.startswith("# ")
    ).strip()
    if preface:
        topics.append(HelpTopic("Overview", preface, 1, None))

    latest_at_level: dict[int, int] = {}
    for selected_index, (line_index, level, title) in enumerate(selected):
        end = len(lines)
        for next_line, next_level, _next_title in selected[selected_index + 1:]:
            if next_level <= level:
                end = next_line
                break
        body = "\n".join(lines[line_index + 1:end]).strip()

        parent_index: int | None = None
        for candidate_level in range(level - 1, minimum_level - 1, -1):
            if candidate_level in latest_at_level:
                parent_index = latest_at_level[candidate_level]
                break
        topic_index = len(topics)
        topics.append(HelpTopic(title, body, level, parent_index))
        latest_at_level[level] = topic_index
        for deeper_level in tuple(
            known for known in latest_at_level if known > level
        ):
            del latest_at_level[deeper_level]

    return tuple(topics)
