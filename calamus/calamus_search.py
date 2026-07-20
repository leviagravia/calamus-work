"""Pure search, replacement and result-model helpers for Calamus."""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, replace
import re

WORD_CHARS = r"A-Za-zÀ-ÖØ-öø-ÿ'"
WORD_RE = re.compile(r"[" + WORD_CHARS + r"]+")
DEFAULT_CONTEXT_LIMIT = 120
UNICODE_PARAGRAPH_SEPARATOR = "\u2029"


@dataclass(frozen=True)
class SearchOptions:
    """Typed options shared by Find, Find Previous and Find All."""

    match_case: bool = False
    whole_word: bool = False
    wrap: bool = True

    def __post_init__(self) -> None:
        for name, value in (
            ("match_case", self.match_case),
            ("whole_word", self.whole_word),
            ("wrap", self.wrap),
        ):
            if not isinstance(value, bool):
                raise TypeError(f"{name} must be bool")


@dataclass(frozen=True)
class SearchQuery:
    """One normalized query and its navigation options."""

    text: str = ""
    options: SearchOptions = SearchOptions()

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("search text must be str")
        if not isinstance(self.options, SearchOptions):
            raise TypeError("options must be SearchOptions")


@dataclass(frozen=True)
class SearchSession:
    """Transient in-memory search authority for the active document."""

    query: SearchQuery = SearchQuery()
    current_match: tuple[int, int] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.query, SearchQuery):
            raise TypeError("query must be SearchQuery")
        if self.current_match is None:
            return
        try:
            start, end = self.current_match
        except (TypeError, ValueError) as exc:
            raise TypeError("current_match must be a two-item span") from exc
        if not isinstance(start, int) or isinstance(start, bool):
            raise TypeError("match start must be int")
        if not isinstance(end, int) or isinstance(end, bool):
            raise TypeError("match end must be int")
        if start < 0 or end < start:
            raise ValueError("invalid current_match span")


@dataclass(frozen=True)
class SearchResult:
    """One Find All row with stable document offsets and readable context."""

    start: int
    end: int
    line: int
    column: int
    context: str

    def __post_init__(self) -> None:
        for name, value in (
            ("start", self.start),
            ("end", self.end),
            ("line", self.line),
            ("column", self.column),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be int")
        if self.start < 0 or self.end < self.start:
            raise ValueError("invalid result span")
        if self.line < 1 or self.column < 1:
            raise ValueError("line and column are one-based")
        if not isinstance(self.context, str):
            raise TypeError("context must be str")


def normalize_search_query(query):
    """Normalize a repeat-search query to a string."""
    if query is None:
        return ""
    return str(query)


def can_repeat_search(query):
    """Return True when a stored search query can be repeated."""
    if isinstance(query, SearchQuery):
        return bool(query.text)
    return bool(normalize_search_query(query))


def build_search_query(
    needle: str,
    *,
    match_case: bool = False,
    whole_word: bool = False,
    wrap: bool = True,
) -> SearchQuery:
    if not isinstance(needle, str):
        raise TypeError("needle must be str")
    return SearchQuery(
        text=needle,
        options=SearchOptions(
            match_case=match_case,
            whole_word=whole_word,
            wrap=wrap,
        ),
    )


def update_search_session(
    session: SearchSession,
    query: SearchQuery,
    *,
    current_match: tuple[int, int] | None = None,
) -> SearchSession:
    if not isinstance(session, SearchSession):
        raise TypeError("session must be SearchSession")
    if not isinstance(query, SearchQuery):
        raise TypeError("query must be SearchQuery")
    return SearchSession(query=query, current_match=current_match)


def clear_current_match(session: SearchSession) -> SearchSession:
    if not isinstance(session, SearchSession):
        raise TypeError("session must be SearchSession")
    return replace(session, current_match=None)


def _text_buffer_line_spans(text: str) -> tuple[tuple[int, int], ...]:
    """Return logical line content spans matching the editor buffer.

    Editor paragraphs end at LF, CR, CRLF, or a Unicode paragraph separator
    (U+2029).  CRLF is one delimiter.  The returned end offset excludes the
    delimiter, and a trailing delimiter produces the final empty line.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")

    spans: list[tuple[int, int]] = []
    line_start = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\r":
            spans.append((line_start, index))
            if index + 1 < len(text) and text[index + 1] == "\n":
                index += 2
            else:
                index += 1
            line_start = index
            continue
        if char == "\n" or char == UNICODE_PARAGRAPH_SEPARATOR:
            spans.append((line_start, index))
            index += 1
            line_start = index
            continue
        index += 1

    spans.append((line_start, len(text)))
    return tuple(spans)


def text_buffer_line_count(text: str) -> int:
    """Return the logical line count used by the editor buffer."""
    return len(_text_buffer_line_spans(text))


def text_stats(text: str) -> tuple[int, int, int]:
    words = len(WORD_RE.findall(text))
    chars = len(text)
    lines = text_buffer_line_count(text)
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


def search_matches_for_query(text: str, query: SearchQuery):
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if not isinstance(query, SearchQuery):
        raise TypeError("query must be SearchQuery")
    return search_matches(
        text,
        query.text,
        match_case=query.options.match_case,
        whole_word=query.options.whole_word,
    )


def choose_search_match(matches, cursor: int, backwards: bool = False, wrap: bool = True):
    """Choose the search match to select from a cursor offset."""
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


def _result_context(
    text: str,
    start: int,
    end: int,
    limit: int,
    *,
    line_start: int,
    line_end: int,
) -> str:
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 20:
        raise ValueError("context limit must be an integer of at least 20")
    line_text = text[line_start:line_end].replace("\t", "    ")
    if len(line_text) <= limit:
        return line_text

    relative_start = start - line_start
    relative_end = max(relative_start + 1, end - line_start)
    window_start = max(0, relative_start - (limit // 3))
    window_end = min(len(line_text), window_start + limit)
    if relative_end > window_end:
        window_end = min(len(line_text), relative_end + (limit // 3))
        window_start = max(0, window_end - limit)

    prefix = "…" if window_start > 0 else ""
    suffix = "…" if window_end < len(line_text) else ""
    return prefix + line_text[window_start:window_end] + suffix


def build_search_results(
    text: str,
    query: SearchQuery,
    *,
    context_limit: int = DEFAULT_CONTEXT_LIMIT,
) -> tuple[SearchResult, ...]:
    """Build immutable Find All rows from the current document text."""
    if not isinstance(context_limit, int) or isinstance(context_limit, bool) or context_limit < 20:
        raise ValueError("context limit must be an integer of at least 20")
    matches = search_matches_for_query(text, query)
    line_spans = _text_buffer_line_spans(text)
    line_starts = [line_start for line_start, _line_end in line_spans]
    results: list[SearchResult] = []
    for match in matches:
        start, end = match.start(), match.end()
        line_index = max(0, bisect_right(line_starts, start) - 1)
        line_start, line_end = line_spans[line_index]
        results.append(
            SearchResult(
                start=start,
                end=end,
                line=line_index + 1,
                column=start - line_start + 1,
                context=_result_context(
                    text,
                    start,
                    end,
                    context_limit,
                    line_start=line_start,
                    line_end=line_end,
                ),
            )
        )
    return tuple(results)


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
    """Validate the current match and return a pure replacement plan."""
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
    """Return a pure replace-all plan."""
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
