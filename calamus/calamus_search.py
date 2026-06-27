"""Search, replace and text-stat helpers for Calamus."""
from __future__ import annotations

import re

WORD_CHARS = r"A-Za-zÀ-ÖØ-öø-ÿ'"
WORD_RE = re.compile(r"[" + WORD_CHARS + r"]+")



def normalize_search_query(query):
    """Normalize a repeat-search query to a string."""
    if query is None:
        return ""
    return str(query)


def can_repeat_search(query):
    """Return True when a stored search query can be repeated."""
    return bool(normalize_search_query(query))

def text_stats(text: str) -> tuple[int, int, int]:
    words = len(WORD_RE.findall(text))
    chars = len(text)
    lines = text.count("\n") + 1 if text else 1
    return words, chars, lines


def search_matches(text: str, needle: str, match_case: bool = False, whole_word: bool = False):
    if not needle:
        return []
    flags = 0 if match_case else re.IGNORECASE
    if whole_word:
        escaped = re.escape(needle)
        pattern = r"(?<![" + WORD_CHARS + r"])" + escaped + r"(?![" + WORD_CHARS + r"])"
    else:
        pattern = re.escape(needle)
    return list(re.finditer(pattern, text, flags))

def replace_all_literal_text(text: str, old: str, new: str, match_case: bool = False, whole_word: bool = False) -> tuple[str, int]:
    matches = search_matches(text, old, match_case=match_case, whole_word=whole_word)
    if not old or not matches:
        return text, 0
    pieces: list[str] = []
    last = 0
    for match in matches:
        pieces.append(text[last:match.start()])
        pieces.append(new)
        last = match.end()
    pieces.append(text[last:])
    return "".join(pieces), len(matches)
