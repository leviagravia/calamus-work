import ast
from pathlib import Path
import unittest

from tests.w107_source_test_support import authoritative_method_source, app_method_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
SEARCH_SOURCE = (ROOT / "calamus" / "calamus_search.py").read_text(encoding="utf-8")
GATEWAY_SOURCE = (ROOT / "calamus" / "calamus_search_gateway.py").read_text(encoding="utf-8")




class ReplaceAllWiringTests(unittest.TestCase):
    def test_replace_all_plan_is_owned_by_search_controller(self):
        app_method = app_method_source("replace_all_literal")
        method = authoritative_method_source("replace_all_literal")
        self.assertIn("self._w107_subsystems.search.replace_all_literal", app_method)
        self.assertLessEqual(len(app_method.splitlines()), 2)
        self.assertIn("replaced, count = self.controller.prepare_replace_all(replacement)", method)
        self.assertIn("return prepare_replace_all_plan(", GATEWAY_SOURCE)
        self.assertNotIn("prepare_replace_all_plan", method)

    def test_replace_all_still_uses_canonical_app_mutation_gateway(self):
        method = authoritative_method_source("replace_all_literal")
        self.assertIn("buffer.delete(start, end)", method)
        self.assertIn("buffer.insert(buffer.get_start_iter(), replaced)", method)
        self.assertIn('self._execute("Replace All", edit)', method)
        self.assertIn("self.controller.clear_current_match()", method)
        self.assertIn("return count", method)

    def test_replace_current_remains_a_separate_plan(self):
        method = authoritative_method_source("replace_current_match")
        self.assertIn("self.controller.prepare_current_replacement", method)
        self.assertNotIn("prepare_replace_all", method)

    def test_pure_search_model_does_not_mutate_gtk(self):
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
