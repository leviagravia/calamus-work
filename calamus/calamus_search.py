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


def choose_search_match(matches, cursor: int, backwards: bool = False, wrap: bool = True):
    """Choose the search match to select from a cursor offset.

    The function is intentionally pure: it accepts already computed matches and
    returns one match object or None. Editor selection and scrolling stay in App.
    """
    if not matches:
        return None
    cursor = int(cursor)
    if backwards:
        for match in reversed(matches):
            if match.start() < cursor:
                return match
        return matches[-1] if wrap else None
    for match in matches:
        if match.start() >= cursor:
            return match
    return matches[0] if wrap else None


def is_whole_word_span(text: str, start: int, end: int) -> bool:
    """Return True when a span is bounded by non-word characters."""
    before = text[start - 1] if start > 0 else ""
    after = text[end] if end < len(text) else ""
    return not re.match(r"[" + WORD_CHARS + r"]", before) and not re.match(r"[" + WORD_CHARS + r"]", after)


def prepare_current_replacement(
    text: str,
    needle: str,
    replacement: str,
    current_match,
    match_case: bool = False,
    whole_word: bool = False,
):
    """Validate the current match and return a pure replacement plan.

    Return value:
        (start, end, replacement, next_match_span) or None.

    Buffer mutation, undo grouping, selection and scrolling intentionally remain
    outside this helper.
    """
    if not needle or current_match is None:
        return None
    try:
        start, end = current_match
        start = int(start)
        end = int(end)
    except (TypeError, ValueError):
        return None
    if start < 0 or end > len(text) or end < start:
        return None
    current = text[start:end]
    if whole_word and not is_whole_word_span(text, start, end):
        return None
    if match_case:
        if current != needle:
            return None
    elif current.lower() != needle.lower():
        return None
    return start, end, replacement, (start, start + len(replacement))


def prepare_replace_all_plan(text: str, needle: str, replacement: str, match_case: bool = False, whole_word: bool = False):
    """Return a pure replace-all plan.

    Return value:
        (new_text, count)

    This helper intentionally performs no buffer mutation, no undo grouping, no
    selection, no scrolling, and no dirty/file lifecycle work.
    """
    if not needle:
        return text, 0
    return replace_all_literal_text(
        text,
        needle,
        replacement,
        match_case=match_case,
        whole_word=whole_word,
    )

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
