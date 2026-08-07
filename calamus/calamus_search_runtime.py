"""W107 application runtime for Find/Replace orchestration.

The runtime imports no GTK namespace and never receives the whole App object.
It consumes the existing W97 SearchController, W103 editor transaction authority,
and narrow presentation/projection capabilities.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class SearchRuntimePorts:
    open_find_replace: Callable[[Callable[..., Any], Callable[..., Any]], Any]
    open_find_all: Callable[[], Any]
    show_info: Callable[[str], Any]
    project_committed_change: Callable[[str], Any]

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not callable(value):
                raise TypeError(f"{name} must be callable")


class SearchApplicationRuntime:
    """Own all application-level search command orchestration."""

    __slots__ = ("controller", "transaction", "buffer_adapter", "ports")

    def __init__(self, controller, transaction, buffer_adapter, ports: SearchRuntimePorts) -> None:
        if controller is None or transaction is None or buffer_adapter is None:
            raise TypeError("search controller, editor transaction and buffer adapter are required")
        if not isinstance(ports, SearchRuntimePorts):
            raise TypeError("ports must be SearchRuntimePorts")
        self.controller = controller
        self.transaction = transaction
        self.buffer_adapter = buffer_adapter
        self.ports = ports

    def on_find_replace(self, *_):
        return self.ports.open_find_replace(self.replace_current_match, self.replace_all_literal)

    def on_find_all(self, *_):
        return self.ports.open_find_all()

    def on_find_next(self, *_):
        if not self.controller.has_query():
            self.on_find_replace()
            return None
        if not self.controller.repeat():
            self.ports.show_info("No match found.")
        return None

    def on_find_previous(self, *_):
        if not self.controller.has_query():
            self.on_find_replace()
            return None
        if not self.controller.repeat(backwards=True):
            self.ports.show_info("No previous match found.")
        return None

    def search_matches(self, needle, match_case=False, whole_word=False):
        return self.controller.matches(
            needle,
            match_case=match_case,
            whole_word=whole_word,
            wrap=self.controller.query.options.wrap,
        )

    def highlight_all_search(self, needle, match_case=False, whole_word=False):
        return self.controller.highlight(
            needle,
            match_case=match_case,
            whole_word=whole_word,
            wrap=self.controller.query.options.wrap,
        )

    def find_text(self, needle, backwards=False, match_case=False, whole_word=False, wrap=True):
        return self.controller.find(
            needle,
            backwards=backwards,
            match_case=match_case,
            whole_word=whole_word,
            wrap=wrap,
        )

    def find_text_previous(self, needle):
        return self.controller.find(needle, backwards=True)

    def _execute(self, label: str, edit_func, *, select_range=None) -> bool:
        result = self.transaction.execute_command(label, edit_func, select_range=select_range)
        if result.changed:
            self.ports.project_committed_change(label)
        return bool(result.changed)

    def replace_current_match(
        self,
        needle_or_replacement,
        replacement=None,
        match_case=False,
        whole_word=False,
    ):
        if replacement is None:
            replacement = needle_or_replacement
        else:
            self.controller.configure(
                needle_or_replacement,
                match_case=match_case,
                whole_word=whole_word,
                wrap=self.controller.query.options.wrap,
            )
        plan = self.controller.prepare_current_replacement(replacement)
        if plan is None:
            return False
        start, end, replacement_text, next_match = plan

        def edit(buffer):
            it1 = buffer.get_iter_at_offset(start)
            it2 = buffer.get_iter_at_offset(end)
            buffer.delete(it1, it2)
            buffer.insert(buffer.get_iter_at_offset(start), replacement_text)

        changed = self._execute(
            "Replace Selection",
            edit,
            select_range=(start, start + len(replacement_text)),
        )
        if changed:
            self.controller.commit_current_replacement(next_match)
        return changed

    def replace_all_literal(self, old_or_replacement, new=None, match_case=False, whole_word=False):
        if new is None:
            replacement = old_or_replacement
        else:
            self.controller.configure(
                old_or_replacement,
                match_case=match_case,
                whole_word=whole_word,
                wrap=self.controller.query.options.wrap,
            )
            replacement = new
        before = self.buffer_adapter.capture().text
        replaced, count = self.controller.prepare_replace_all(replacement)
        if not count or replaced == before:
            return 0

        def edit(buffer):
            start, end = buffer.get_bounds()
            buffer.delete(start, end)
            buffer.insert(buffer.get_start_iter(), replaced)

        if self._execute("Replace All", edit):
            self.controller.clear_current_match()
            return count
        return 0
