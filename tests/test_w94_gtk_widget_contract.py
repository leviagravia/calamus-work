"""Headless contract for W94 real-GTK widget lookups.

This test prevents a desktop-only TypeError by validating the helper signature and
every W94 call site before a real display is required.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path
import unittest

from calamus_gtk_test_driver import named_widget


ROOT = Path(__file__).resolve().parents[1]
W94_GTK_TEST = ROOT / "tests/test_w94_tags_app_desktop_e2e.py"


class W94GtkWidgetContractTests(unittest.TestCase):
    def test_named_widget_helper_and_w94_calls_share_typed_three_argument_contract(self):
        parameters = tuple(inspect.signature(named_widget).parameters)
        self.assertEqual(parameters, ("widget", "name", "widget_type"))

        source = W94_GTK_TEST.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(W94_GTK_TEST))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "named_widget"
        ]
        self.assertTrue(calls, "W94 real-GTK test must use named_widget")
        for call in calls:
            self.assertEqual(
                len(call.args),
                3,
                f"named_widget must receive widget, semantic name and GTK type at line {call.lineno}",
            )
            self.assertFalse(call.keywords, "named_widget W94 calls use positional typed contract")

    def test_w94_panel_declares_all_semantic_names_with_expected_gtk_types(self):
        source = W94_GTK_TEST.read_text(encoding="utf-8")
        expected = (
            '("tags-search", Gtk.SearchEntry)',
            '("tags-show-all-az", Gtk.Button)',
            '("tags-scope", Gtk.ComboBoxText)',
            '("tags-sort", Gtk.ComboBoxText)',
            '("tags-issues-only", Gtk.CheckButton)',
            '("tags-list", Gtk.ListBox)',
            '("tag-uses-list", Gtk.ListBox)',
            '("tags-open", Gtk.Button)',
            '("tags-rename", Gtk.Button)',
            '("tags-refresh", Gtk.Button)',
            '("tags-remove", Gtk.Button)',
            '("tags-normalize", Gtk.Button)',
        )
        for declaration in expected:
            self.assertIn(declaration, source)


if __name__ == "__main__":
    unittest.main()
