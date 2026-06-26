import ast
from pathlib import Path
import re
import unittest

from calamus_search import text_stats as calc_text_stats
from calamus_writing import document_statistics

ROOT = Path(__file__).resolve().parents[1]
BIN_CALAMUS = ROOT / "bin" / "calamus"

def app_method_source(method_name):
    source = BIN_CALAMUS.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return "\n".join(lines[child.lineno - 1:child.end_lineno])
    raise AssertionError(f"App.{method_name} not found")

class StatusWordCountCanonicalizationTests(unittest.TestCase):
    def test_text_stats_uses_document_statistics_for_words_only(self):
        method = app_method_source("text_stats")
        self.assertIn("text = self.buffer_text()", method)
        self.assertIn("stats = document_statistics(text)", method)
        self.assertIn("calc_text_stats(text)", method)
        self.assertIn('return stats["words"], chars, lines', method)

    def test_status_update_still_uses_text_stats(self):
        method = app_method_source("update_title")
        self.assertIn("words, chars, lines = self.text_stats()", method)
        self.assertIn("words {words}", method)

    def test_document_statistics_is_canonical_for_numbered_lists(self):
        sample = (
            "1. scrivi testo nel documento\n"
            "2. apri Document Statistics\n"
            "3. verifica che il dialog appaia\n"
            "4. verifica che le statistiche siano plausibili\n"
            "5. verifica che il testo non cambi\n"
            "6. verifica che lo stato modificato resti invariato\n"
            "7. verifica nessun crash"
        )
        canonical_words = document_statistics(sample)["words"]
        alpha_only_words = len(re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)?", sample, flags=re.UNICODE))
        _legacy_words, chars, lines = calc_text_stats(sample)

        self.assertEqual(canonical_words, 41)
        self.assertEqual(alpha_only_words, 34)
        self.assertGreater(canonical_words, alpha_only_words)
        self.assertGreater(chars, 0)
        self.assertEqual(lines, 7)

    def test_no_new_command_layer_dispatches_added(self):
        source = BIN_CALAMUS.read_text(encoding="utf-8")
        self.assertEqual(source.count(".dispatch("), 1)
        self.assertIn('"writing.statistics"', source)

    def test_no_text_transform_wiring_added(self):
        source = BIN_CALAMUS.read_text(encoding="utf-8")
        forbidden = (
            '"edit.uppercase"', '"edit.lowercase"', '"writing.sort-lines"',
            '"writing.clean-pdf"', '"writing.remove-extra-spaces"',
            '"writing.remove-trailing-spaces"', '"writing.smart-typography"',
            '"writing.reflow-paragraph"', '"writing.join-lines"',
        )
        for command_id in forbidden:
            self.assertNotIn(command_id, source)

if __name__ == "__main__":
    unittest.main()
