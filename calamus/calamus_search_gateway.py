"""Canonical search-session gateway for Calamus."""
from __future__ import annotations

from dataclasses import replace

from calamus_search import (
    SearchOptions,
    SearchQuery,
    SearchResult,
    SearchSession,
    build_search_query,
    build_search_results,
    choose_search_match,
    prepare_current_replacement,
    prepare_replace_all_plan,
    search_matches_for_query,
)


class SearchController:
    """Own transient search state while delegating GTK access to an adapter."""

    def __init__(self, adapter) -> None:
        required = (
            "text",
            "cursor_offset",
            "clear_highlights",
            "apply_highlights",
            "select_span",
            "line_column_for_offset",
        )
        if any(not callable(getattr(adapter, name, None)) for name in required):
            raise TypeError("adapter does not implement the search-view protocol")
        self._adapter = adapter
        self.session = SearchSession()
        self._highlight_source = None

    @property
    def query(self) -> SearchQuery:
        return self.session.query

    @property
    def current_match(self) -> tuple[int, int] | None:
        return self.session.current_match

    def has_query(self) -> bool:
        return bool(self.query.text)

    def configure(
        self,
        needle: str,
        *,
        match_case: bool = False,
        whole_word: bool = False,
        wrap: bool = True,
    ) -> SearchQuery:
        query = build_search_query(
            needle,
            match_case=match_case,
            whole_word=whole_word,
            wrap=wrap,
        )
        current = self.current_match if query == self.query else None
        self.session = SearchSession(query=query, current_match=current)
        return query

    def clear_highlights(self) -> None:
        self._adapter.clear_highlights()

    def _matches(self):
        return search_matches_for_query(self._adapter.text(), self.query)

    def matches(
        self,
        needle: str | None = None,
        *,
        match_case: bool = False,
        whole_word: bool = False,
        wrap: bool = True,
    ):
        if needle is not None:
            self.configure(
                needle,
                match_case=match_case,
                whole_word=whole_word,
                wrap=wrap,
            )
        return self._matches() if self.has_query() else []

    def highlight(
        self,
        needle: str | None = None,
        *,
        match_case: bool = False,
        whole_word: bool = False,
        wrap: bool = True,
    ) -> int:
        if needle is not None:
            self.configure(
                needle,
                match_case=match_case,
                whole_word=whole_word,
                wrap=wrap,
            )
        matches = self._matches() if self.has_query() else []
        spans = tuple((match.start(), match.end()) for match in matches)
        return self._adapter.apply_highlights(spans)

    def find(
        self,
        needle: str | None = None,
        *,
        backwards: bool = False,
        match_case: bool = False,
        whole_word: bool = False,
        wrap: bool = True,
    ) -> bool:
        if not isinstance(backwards, bool):
            raise TypeError("backwards must be bool")
        if needle is not None:
            self.configure(
                needle,
                match_case=match_case,
                whole_word=whole_word,
                wrap=wrap,
            )
        if not self.has_query():
            self.session = replace(self.session, current_match=None)
            return False
        matches = self._matches()
        cursor = self._adapter.cursor_offset(backwards=backwards)
        chosen = choose_search_match(
            matches,
            cursor,
            backwards=backwards,
            wrap=self.query.options.wrap,
        )
        if chosen is None:
            self.session = replace(self.session, current_match=None)
            return False
        span = (chosen.start(), chosen.end())
        self.session = replace(self.session, current_match=span)
        self._adapter.select_span(*span)
        return True

    def repeat(self, *, backwards: bool = False) -> bool:
        if not self.has_query():
            return False
        self.highlight()
        return self.find(backwards=backwards)

    def needs_current_match(
        self,
        needle: str,
        *,
        match_case: bool = False,
        whole_word: bool = False,
        wrap: bool = True,
    ) -> bool:
        query = build_search_query(
            needle,
            match_case=match_case,
            whole_word=whole_word,
            wrap=wrap,
        )
        return self.current_match is None or query != self.query

    def prepare_current_replacement(self, replacement: str):
        if not isinstance(replacement, str):
            raise TypeError("replacement must be str")
        return prepare_current_replacement(
            self._adapter.text(),
            self.query.text,
            replacement,
            self.current_match,
            match_case=self.query.options.match_case,
            whole_word=self.query.options.whole_word,
        )

    def commit_current_replacement(self, next_match: tuple[int, int]) -> None:
        self.session = replace(self.session, current_match=next_match)

    def prepare_replace_all(self, replacement: str) -> tuple[str, int]:
        if not isinstance(replacement, str):
            raise TypeError("replacement must be str")
        return prepare_replace_all_plan(
            self._adapter.text(),
            self.query.text,
            replacement,
            match_case=self.query.options.match_case,
            whole_word=self.query.options.whole_word,
        )

    def clear_current_match(self) -> None:
        self.session = replace(self.session, current_match=None)

    def find_all(
        self,
        needle: str,
        *,
        match_case: bool = False,
        whole_word: bool = False,
        wrap: bool = True,
    ) -> tuple[SearchResult, ...]:
        self.configure(
            needle,
            match_case=match_case,
            whole_word=whole_word,
            wrap=wrap,
        )
        pure_results = build_search_results(self._adapter.text(), self.query)
        results = []
        for result in pure_results:
            line, column = self._adapter.line_column_for_offset(result.start)
            results.append(replace(result, line=line, column=column))
        results = tuple(results)
        self._adapter.apply_highlights((result.start, result.end) for result in results)
        return results

    def navigate_result(self, result: SearchResult) -> None:
        if not isinstance(result, SearchResult):
            raise TypeError("result must be SearchResult")
        span = (result.start, result.end)
        self.session = replace(self.session, current_match=span)
        self._adapter.select_span(*span)

    def schedule_highlight(self, timeout_add, *, delay_ms: int = 300) -> bool:
        if not callable(timeout_add):
            raise TypeError("timeout_add must be callable")
        if not isinstance(delay_ms, int) or isinstance(delay_ms, bool) or delay_ms < 0:
            raise ValueError("delay_ms must be a non-negative integer")
        if not self.has_query() or self._highlight_source is not None:
            return False
        self.session = replace(self.session, current_match=None)

        def run():
            self._highlight_source = None
            self.highlight()
            return False

        self._highlight_source = timeout_add(delay_ms, run)
        return True
