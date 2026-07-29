"""Headless contract for the post-R5 Tags GTK lifecycle architecture."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "calamus/calamus_tags_panel.py"
CONTROLLER = ROOT / "calamus/calamus_tags_controller.py"
RUNTIME = ROOT / "calamus/calamus_tags_runtime.py"


class W94TagsViewLifecycleContractTests(unittest.TestCase):
    def test_tags_surface_uses_listboxes_and_no_treeview_or_viewport_calls(self):
        source = PANEL.read_text(encoding="utf-8")
        self.assertIn("Gtk.ListBox()", source)
        self.assertIn('set_name("tags-list")', source)
        self.assertIn('set_name("tag-uses-list")', source)
        for forbidden in (
            "Gtk.TreeView", "Gtk.ListStore", "scroll_to_cell",
            "get_vadjustment", "get_hadjustment", "get_adjustment",
        ):
            self.assertNotIn(forbidden, source)

    def test_render_methods_are_viewport_and_selection_free_by_ast(self):
        tree = ast.parse(PANEL.read_text(encoding="utf-8"), filename=str(PANEL))
        methods = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in ("render_tags", "render_uses"):
            method = methods[name]
            calls = {
                node.func.attr
                for node in ast.walk(method)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            }
            self.assertTrue({"add", "remove", "unselect_all"} & calls)
            self.assertNotIn("select_row", calls)
            self.assertFalse(
                calls & {
                    "scroll_to_cell", "get_vadjustment",
                    "get_hadjustment", "get_adjustment", "grab_focus",
                }
            )

    def test_tags_layout_is_width_bounded_and_exposes_all_tags_az(self):
        source = PANEL.read_text(encoding="utf-8")
        self.assertIn('set_name("tags-show-all-az")', source)
        self.assertIn('label="All tags A–Z"', source)
        self.assertIn('sort.append(TAG_SORT_NAME, "Name (A–Z)")', source)
        self.assertIn("set_propagate_natural_width(False)", source)
        self.assertIn("set_min_content_width(1)", source)
        self.assertIn("orientation=Gtk.Orientation.VERTICAL", source)
        self.assertNotIn("filter_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL", source)
        self.assertNotIn("primary = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL", source)
        self.assertNotIn("secondary = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL", source)

    def test_visual_selection_is_post_map_idle_and_cancellable(self):
        panel = PANEL.read_text(encoding="utf-8")
        runtime = RUNTIME.read_text(encoding="utf-8")
        self.assertIn('"map", self._on_map_for_selection', panel)
        self.assertIn('self.widget.connect("unmap", self._on_unmap)', panel)
        self.assertIn('self.widget.connect("destroy", self._on_destroy)', panel)
        self.assertIn("GLib.idle_add(self._run_deferred_selection)", panel)
        self.assertIn("GLib.source_remove(self._selection_source_id)", panel)
        self.assertIn("self.tags_list.select_row(tag_row)", panel)
        self.assertIn("self.uses_list.select_row(self._use_rows[index])", panel)
        self.assertNotIn("grab_focus", panel)
        self.assertNotIn("queue_activation_focus", panel)
        self.assertNotIn("queue_activation_focus", runtime)
        self.assertNotIn("grab_focus", runtime)

    def test_controller_view_protocol_is_consumer_driven_and_lifecycle_free(self):
        controller_source = CONTROLLER.read_text(encoding="utf-8")
        tree = ast.parse(controller_source, filename=str(CONTROLLER))
        protocol = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "TagsView"
        )
        protocol_members = {
            node.name for node in protocol.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertEqual(
            protocol_members,
            {
                "widget", "render_tags", "render_uses",
                "selected_tag_identity", "selected_use",
                "set_query", "set_scope", "set_issues_only", "set_sort",
            },
        )
        self.assertNotIn("focus_search", protocol_members)

        controller_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "TagsController"
        )
        consumed = set()
        for node in ast.walk(controller_class):
            if not isinstance(node, ast.Attribute):
                continue
            value = node.value
            if (
                isinstance(value, ast.Attribute)
                and isinstance(value.value, ast.Name)
                and value.value.id == "self"
                and value.attr == "_view"
            ):
                consumed.add(node.attr)
        self.assertEqual(consumed, protocol_members)

    def test_concrete_adapter_satisfies_controller_surface_without_focus_alias(self):
        panel_tree = ast.parse(PANEL.read_text(encoding="utf-8"), filename=str(PANEL))
        adapter = next(
            node for node in panel_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "TagsPanelViewAdapter"
        )
        methods = {
            node.name for node in adapter.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertTrue(
            {
                "render_tags", "render_uses", "selected_tag_identity",
                "selected_use", "set_query", "set_scope",
                "set_issues_only", "set_sort",
            }.issubset(methods)
        )
        init = next(
            node for node in adapter.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        )
        assigns_widget = any(
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Attribute)
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
                and target.attr == "widget"
                for target in node.targets
            )
            for node in ast.walk(init)
        )
        self.assertTrue(assigns_widget)
        self.assertNotIn("focus_search", methods)
        self.assertNotIn("queue_activation_focus", methods)
        self.assertIn("_queue_selection_sync", methods)
        self.assertIn("_run_deferred_selection", methods)


if __name__ == "__main__":
    unittest.main()
