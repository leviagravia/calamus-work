import ast
from pathlib import Path
import unittest

from tests.w107_source_test_support import authoritative_method_source, app_method_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")




class FindPreviousWiringTests(unittest.TestCase):
    def test_find_previous_reuses_canonical_search_session(self):
        method = authoritative_method_source("on_find_previous")
        self.assertIn("on_find_previous=search_runtime.on_find_previous", SOURCE)
        self.assertNotIn("def on_find_previous", SOURCE)
        self.assertIn("if not self.controller.has_query():", method)
        self.assertIn("self.on_find_replace()", method)
        self.assertIn("self.controller.repeat(backwards=True)", method)
        self.assertIn('self.ports.show_info("No previous match found.")', method)
        self.assertNotIn("self.last_search", method)
        self.assertNotIn("self.last_match", method)

    def test_find_previous_remains_non_mutating_wrapper(self):
        method = authoritative_method_source("on_find_previous")
        for token in (
            "execute_command",
            "finalize_command_edit",
            "save_file",
            "open_path",
            ".delete(",
            ".insert(",
            "set_text(",
            "replace_all_literal",
            "get_buffer",
        ):
            self.assertNotIn(token, method)

    def test_find_text_is_a_thin_search_controller_adapter(self):
        method = authoritative_method_source("find_text")
        self.assertNotIn("def find_text", SOURCE)
        self.assertIn("return self.controller.find(", method)
        self.assertLessEqual(len(method.splitlines()), 10)
        for token in (
            "get_buffer",
            "get_selection_bounds",
            "get_iter_at_mark",
            "choose_search_match",
            "select_range",
            "last_search",
            "last_match",
        ):
            self.assertNotIn(token, method)

    def test_replace_paths_do_not_use_repeat_navigation(self):
        for name in ["replace_all_literal", "replace_current_match"]:
            self.assertNotIn(".repeat(", authoritative_method_source(name))


if __name__ == "__main__":
    unittest.main()
