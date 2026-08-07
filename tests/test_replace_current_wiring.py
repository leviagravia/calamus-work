import ast
from pathlib import Path
import unittest

from tests.w107_source_test_support import authoritative_method_source, app_method_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
SEARCH_SOURCE = (ROOT / "calamus" / "calamus_search.py").read_text(encoding="utf-8")
GATEWAY_SOURCE = (ROOT / "calamus" / "calamus_search_gateway.py").read_text(encoding="utf-8")
SEARCH_DIALOGS_SOURCE = (ROOT / "calamus" / "calamus_search_dialogs.py").read_text(encoding="utf-8")




class ReplaceCurrentWiringTests(unittest.TestCase):
    def test_replace_current_preflight_is_owned_by_search_controller(self):
        app_method = app_method_source("replace_current_match")
        method = authoritative_method_source("replace_current_match")
        self.assertIn("self._w107_subsystems.search.replace_current_match", app_method)
        self.assertLessEqual(len(app_method.splitlines()), 2)
        self.assertIn("plan = self.controller.prepare_current_replacement(replacement)", method)
        self.assertIn("return prepare_current_replacement(", GATEWAY_SOURCE)
        self.assertNotIn("self.buffer_text()", method)
        self.assertNotIn("self.last_match", method)

    def test_replace_current_keeps_document_mutation_in_app_gateway(self):
        method = authoritative_method_source("replace_current_match")
        self.assertIn("start, end, replacement_text, next_match = plan", method)
        self.assertIn("buffer.delete(it1, it2)", method)
        self.assertIn("self._execute(", method)
        self.assertIn("self.controller.commit_current_replacement(next_match)", method)
        self.assertIn("return changed", method)

    def test_replace_current_has_no_inline_search_validation(self):
        method = authoritative_method_source("replace_current_match")
        for token in (
            "current = text[start:end]",
            "current.lower()",
            "needle.lower()",
            "re.match(",
            "before =",
            "after =",
            "start < 0",
            "end > len(text)",
        ):
            self.assertNotIn(token, method)

    def test_replace_buffer_range_still_owns_execute_command_boundary(self):
        app_method = app_method_source("replace_buffer_range")
        method = authoritative_method_source("replace_buffer_range")
        self.assertIn("self._w107_subsystems.spellcheck.replace_buffer_range", app_method)
        self.assertIn("buffer.delete(it1, it2)", method)
        self.assertIn("buffer.insert(buffer.get_iter_at_offset(start), replacement)", method)
        self.assertIn('self._execute(', method)
        self.assertIn('"Replace Selection"', method)


    def test_visible_replace_command_keeps_replaced_match_selected(self):
        self.assertIn('"Replace", 20', SEARCH_DIALOGS_SOURCE)
        self.assertNotIn('"Replace Current"', SEARCH_DIALOGS_SOURCE)
        tree = ast.parse(SEARCH_DIALOGS_SOURCE)
        do_replace = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "do_replace"
        )
        source = ast.get_source_segment(SEARCH_DIALOGS_SOURCE, do_replace) or ""
        self.assertIn("replace_current(replacement)", source)
        self.assertIn("controller.highlight()", source)
        self.assertNotIn("controller.find()", source)
        self.assertIn("Replaced selected match.", source)

    def test_search_model_is_pure(self):
        for token in (
            "Gtk",
            "Gdk",
            "GLib",
            "TextBuffer",
            "execute_command",
            "replace_buffer_range",
            "scroll_to",
            ".delete(",
            ".insert(",
            "set_text(",
        ):
            self.assertNotIn(token, SEARCH_SOURCE)


if __name__ == "__main__":
    unittest.main()
