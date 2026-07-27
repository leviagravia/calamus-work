"""Semantic normalization helpers for rendered Pandoc artifacts.

Rendered artifacts may wrap lines or use platform-specific whitespace without
changing bibliographic meaning.  These helpers normalize Unicode and collapse
whitespace while preserving punctuation, so list-separator corruption such as
``Herder; Herder`` remains distinguishable from the canonical scalar
``Herder and Herder``.
"""
from __future__ import annotations

import unicodedata


def normalize_rendered_text(value: str, *, casefold: bool = False) -> str:
    """Return NFC text with every whitespace run collapsed to one space."""
    if not isinstance(value, str):
        raise TypeError("value must be str")
    normalized = unicodedata.normalize("NFC", value)
    normalized = " ".join(normalized.split())
    return normalized.casefold() if casefold else normalized


def contains_semantic_text(haystack: str, needle: str, *, casefold: bool = False) -> bool:
    """Compare semantic text while retaining punctuation distinctions."""
    return normalize_rendered_text(needle, casefold=casefold) in normalize_rendered_text(
        haystack, casefold=casefold
    )
