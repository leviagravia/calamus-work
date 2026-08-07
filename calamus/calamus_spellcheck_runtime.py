"""W107 GTK-free application orchestration for interactive Hunspell checking."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable

from calamus_search import WORD_RE
from calamus_spellcheck import (
    hunspell_dict as spell_hunspell_dict,
    hunspell_base_command as spell_hunspell_base_command,
    hunspell_misspelled_words as spell_hunspell_misspelled_words,
    hunspell_suggestions as spell_hunspell_suggestions,
)


@dataclass(frozen=True)
class SpellcheckRuntimePorts:
    language_provider: Callable[[], str]
    update_language: Callable[[str], Any]
    spelling_dialog: Callable[[str, tuple[str, ...] | list[str]], tuple[Any, str]]
    decode_response: Callable[[Any], str]
    show_info: Callable[[str], Any]
    show_error: Callable[[str], Any]
    clear_spell_tags: Callable[[], Any]
    select_range: Callable[[int, int], Any]
    update_title: Callable[[], Any]
    project_committed_change: Callable[[str], Any]

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not callable(value):
                raise TypeError(f"{name} must be callable")


class SpellcheckApplicationRuntime:
    """Own spellcheck command flow without retaining the App object."""

    __slots__ = ("transaction", "buffer_adapter", "ports")

    def __init__(self, transaction, buffer_adapter, ports: SpellcheckRuntimePorts) -> None:
        if transaction is None or buffer_adapter is None:
            raise TypeError("spellcheck editor dependencies are required")
        if not isinstance(ports, SpellcheckRuntimePorts):
            raise TypeError("ports must be SpellcheckRuntimePorts")
        self.transaction = transaction
        self.buffer_adapter = buffer_adapter
        self.ports = ports

    @property
    def language(self) -> str:
        return self.ports.language_provider()

    def on_lang(self, item, lang):
        if item.get_active():
            return self.ports.update_language(lang)
        return False

    def clear_spell_tags(self):
        return self.ports.clear_spell_tags()

    def hunspell_dict(self):
        return spell_hunspell_dict(self.language)

    def hunspell_base_command(self):
        return spell_hunspell_base_command(self.language)

    def hunspell_misspelled_words(self, text):
        return spell_hunspell_misspelled_words(text, self.language)

    def hunspell_suggestions(self, word):
        return spell_hunspell_suggestions(word, self.language)

    def find_next_error(self, start_offset, misspelled):
        text = self.buffer_adapter.capture().text
        for match in WORD_RE.finditer(text, max(0, start_offset)):
            word = match.group(0)
            if word in misspelled:
                return match.start(), match.end(), word
        return None

    def select_range(self, start, end):
        return self.ports.select_range(start, end)

    def spelling_dialog(self, word, suggestions):
        return self.ports.spelling_dialog(word, suggestions)

    def _execute(self, label: str, edit_func, *, select_range=None) -> bool:
        result = self.transaction.execute_command(label, edit_func, select_range=select_range)
        if result.changed:
            self.ports.project_committed_change(label)
        return bool(result.changed)

    def replace_buffer_range(self, start, end, replacement):
        def edit(buffer):
            it1 = buffer.get_iter_at_offset(start)
            it2 = buffer.get_iter_at_offset(end)
            buffer.delete(it1, it2)
            buffer.insert(buffer.get_iter_at_offset(start), replacement)
        return self._execute(
            "Replace Selection",
            edit,
            select_range=(start, start + len(replacement)),
        )

    def replace_all_word(self, old, new, from_offset=0):
        text = self.buffer_adapter.capture().text
        pattern = re.compile(r"(?<![A-Za-zÀ-ÖØ-öø-ÿ'])" + re.escape(old) + r"(?![A-Za-zÀ-ÖØ-öø-ÿ'])")
        matches = list(pattern.finditer(text, max(0, from_offset)))
        if not matches:
            return 0

        def edit(buffer):
            shift = 0
            for match in matches:
                start = match.start() + shift
                end = match.end() + shift
                it1 = buffer.get_iter_at_offset(start)
                it2 = buffer.get_iter_at_offset(end)
                buffer.delete(it1, it2)
                buffer.insert(buffer.get_iter_at_offset(start), new)
                shift += len(new) - len(old)

        return len(matches) if self._execute("Replace All Word", edit) else 0

    def on_check(self, *_):
        self.clear_spell_tags()
        try:
            if not self.hunspell_base_command():
                self.ports.show_error(
                    "Hunspell was not found. Install hunspell and the required dictionaries, "
                    "for example hunspell-it and hunspell-en-us."
                )
                return None
            misspelled = self.hunspell_misspelled_words(self.buffer_adapter.capture().text)
            if misspelled is None:
                self.ports.show_error("Hunspell was not found.")
                return None
            if not misspelled:
                self.ports.show_info("No spelling issues found.")
                return None

            ignored = set()
            offset = 0
            fixed = 0
            ignored_count = 0

            while True:
                active_errors = misspelled - ignored
                found = self.find_next_error(offset, active_errors)
                if not found:
                    break
                start, end, word = found
                self.select_range(start, end)
                suggestions = self.hunspell_suggestions(word)
                response, replacement = self.spelling_dialog(word, suggestions)
                action = self.ports.decode_response(response)

                if action == "cancel":
                    self.clear_spell_tags()
                    self.ports.update_title()
                    return None
                if action == "ignore":
                    ignored_count += 1
                    offset = end
                    continue
                if action == "ignore-all":
                    ignored.add(word)
                    ignored_count += 1
                    offset = end
                    continue
                if action == "replace":
                    if replacement and replacement != word:
                        self.replace_buffer_range(start, end, replacement)
                        fixed += 1
                        offset = start + len(replacement)
                    else:
                        offset = end
                    continue
                if action == "replace-all":
                    if replacement and replacement != word:
                        fixed += self.replace_all_word(word, replacement, start)
                        misspelled.discard(word)
                        offset = start + len(replacement)
                    else:
                        offset = end
                    continue
                raise ValueError(f"Unknown spelling response action: {action}")

            self.clear_spell_tags()
            self.ports.update_title()
            self.ports.show_info(
                f"Spellcheck complete. Replacements: {fixed}. Ignored: {ignored_count}."
            )
        except Exception as error:
            self.ports.show_error(str(error))
        return None
