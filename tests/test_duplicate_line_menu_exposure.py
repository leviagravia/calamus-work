from pathlib import Path
import unittest

import calamus_shortcuts


ROOT = Path(__file__).resolve().parents[1]
UI_SOURCE = (ROOT / "calamus" / "calamus_ui.py").read_text(encoding="utf-8")
BIN_SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")


class DuplicateLineMenuExposureTests(unittest.TestCase):
    def test_duplicate_line_is_visible_in_edit_menu(self):
        self.assertIn(
            'add_item(editm, "Duplicate Line / Selection\\tCtrl+D", app.on_duplicate_line_or_selection)',
            UI_SOURCE,
        )

    def test_duplicate_line_menu_is_between_select_all_and_find_group(self):
        select_all = UI_SOURCE.index('add_item(editm, "Select All\\tCtrl+A", app.on_select_all)')
        duplicate = UI_SOURCE.index('add_item(editm, "Duplicate Line / Selection\\tCtrl+D", app.on_duplicate_line_or_selection)')
        find_replace = UI_SOURCE.index('add_item(editm, "Find / Replace…\\tCtrl+F", app.on_find_replace)')
        self.assertLess(select_all, duplicate)
        self.assertLess(duplicate, find_replace)

    def test_duplicate_line_shortcut_registry_row_exists(self):
        rows = calamus_shortcuts.shortcut_rows()
        self.assertIn(("Edit", "Duplicate Line / Selection", "Ctrl+D"), rows)

    def test_duplicate_line_accelerator_binding_already_exists(self):
        self.assertIn('("<Control>D", app.on_duplicate_line_or_selection)', UI_SOURCE)

    def test_duplicate_line_handler_still_exists(self):
        self.assertIn("def on_duplicate_line_or_selection", BIN_SOURCE)


if __name__ == "__main__":
    unittest.main()
