from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from calamus_search import text_stats as calc_text_stats
from calamus_writing import document_statistics


ROOT = Path(__file__).resolve().parents[1]
BIN_CALAMUS = ROOT / "bin" / "calamus"


def _source() -> str:
    return BIN_CALAMUS.read_text(encoding="utf-8")


def _app_method(name: str) -> str:
    source = _source()
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == name:
                    return "\n".join(lines[child.lineno - 1 : child.end_lineno])
    raise AssertionError(f"App.{name} not found")


def _dispatch_ids() -> list[str]:
    return re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", _source(), flags=re.S)


class StatusWordCountCanonicalizationTests(unittest.TestCase):
    def test_text_stats_uses_document_statistics_for_words_only(self):
        method = _app_method("text_stats")
        self.assertIn("stats = document_statistics(text)", method)
        self.assertIn("_old_words, chars, lines = calc_text_stats(text)", method)
        self.assertIn('return stats["words"], chars, lines', method)

    def test_status_update_still_uses_text_stats(self):
        method = _app_method("update_title")
        self.assertIn("words, chars, lines = self.text_stats()", method)

    def test_document_statistics_is_canonical_for_numbered_lists(self):
        sample = (
            "1. Primo punto con parole e numero 123\n"
            "2. Secondo punto con parole e numero 456\n"
            "3. Terzo punto con parole e numero 789\n"
            "4. Quarto punto con parole e numero 101112\n"
            "5. Quinto punto con parole e numero 131415\n"
            "6. Sesto punto con parole e numero 161718\n"
            "7. Settimo punto con parole e numero 192021"
        )
        stats = document_statistics(sample)
        old_words, chars, lines = calc_text_stats(sample)

        # W13 deliberately made document_statistics the canonical status-bar
        # word-count source. calc_text_stats remains available for chars/lines
        # compatibility and may count words differently. Here the old path
        # counts only 6 alphabetic words per line, while document_statistics
        # also counts the line number and the trailing numeric token.
        self.assertEqual(stats["words"], 56)
        self.assertEqual(old_words, 42)
        self.assertNotEqual(stats["words"], old_words)
        self.assertEqual(lines, 7)
        self.assertEqual(chars, len(sample))

    def test_allowed_command_layer_dispatches_after_w32(self):
        self.assertEqual(sorted(_dispatch_ids()), ["edit.lowercase", "edit.uppercase", "writing.clean-pdf", "writing.join-lines", "writing.reflow-paragraph", "writing.remove-extra-spaces", "writing.remove-trailing-spaces", "writing.smart-typography", "writing.statistics", "writing.title-case"])

    def test_no_other_unapproved_text_transform_wiring_added(self):
        source = _source()
        forbidden = [
            '"writing.sort-lines"',
        ]
        for command_id in forbidden:
            self.assertNotIn(command_id, source)


if __name__ == "__main__":
    unittest.main()
