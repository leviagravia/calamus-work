import ast
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
HOST = ROOT / "calamus" / "calamus_right_panel.py"
CONTROLLER = ROOT / "calamus" / "calamus_clip_collection.py"
PANEL = ROOT / "calamus" / "calamus_clip_panel.py"
CLIPS = ROOT / "calamus" / "calamus_clips.py"
UI = ROOT / "calamus" / "calamus_ui.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"


def source(path):
    return path.read_text(encoding="utf-8")


def method_source(name):
    text = source(LAUNCHER)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(text, node)
    raise AssertionError(f"method not found: {name}")


class RightPanelCommandWiringTests(unittest.TestCase):
    def test_startup_has_one_right_panel_host_authority(self):
        launcher = source(LAUNCHER)
        self.assertEqual(launcher.count("RightPanelHost("), 1)
        self.assertIn("self.right_panel_host = RightPanelHost", launcher)
        self.assertIn('self.right_panel_host.register(', launcher)

    def test_launcher_no_longer_owns_raw_clip_widgets_or_list_state(self):
        launcher = source(LAUNCHER)
        for forbidden in (
            "self.clips =",
            "self.clip_panel =",
            "self.clip_list =",
            "self.clip_panel_attached",
            "Gdk.EventType._2BUTTON_PRESS",
            "get_row_at_y",
        ):
            self.assertNotIn(forbidden, launcher)

    def test_toggle_is_a_thin_host_adapter(self):
        method = method_source("toggle_clip_collection")
        self.assertIn('self.right_panel_host.toggle("clip-collection")', method)
        self.assertNotIn("pack2", method)
        self.assertNotIn("set_position", method)
        self.assertLessEqual(len(method.splitlines()), 3)

    def test_clip_controller_owns_persist_first_mutations(self):
        controller = source(CONTROLLER)
        self.assertIn("if not self._store.save_clips(candidate, self._limit):", controller)
        self.assertIn("self._clips = candidate", controller)
        self.assertLess(
            controller.index("if not self._store.save_clips(candidate, self._limit):"),
            controller.index("self._clips = candidate"),
        )

    def test_view_adapter_owns_double_click_and_list_selection(self):
        panel = source(PANEL)
        self.assertIn("class ClipCollectionViewAdapter", panel)
        self.assertIn("def on_button_press", panel)
        self.assertIn("get_selected_row", panel)
        self.assertIn("get_row_at_index", panel)
        self.assertIn('clip_list.connect("button-press-event", adapter.on_button_press)', panel)
        self.assertNotIn("row-activated", panel)

    def test_host_is_generic_single_slot_without_research_placeholders(self):
        host = source(HOST)
        self.assertIn("self._sections", host)
        self.assertIn("self._paned.pack2(widget, False, False)", host)
        self.assertIn("self._detach_active()", host)
        for future in ("references", "tags", "source-notes", "scratchpad", "concepts"):
            self.assertNotIn(future, host.lower())

    def test_clip_store_is_markdown_primary_with_legacy_json_fallback(self):
        clips = source(CLIPS)
        self.assertIn('return os.path.join(config_dir, "clips.md")', clips)
        self.assertIn('return os.path.join(config_dir, "clips.json")', clips)
        self.assertIn("if os.path.exists(path):", clips)
        self.assertIn("save_clips(config_dir, legacy, limit)", clips)
        self.assertNotIn("save_json_file", clips)

    def test_visible_command_and_shortcuts_are_unchanged(self):
        ui = source(UI)
        self.assertIn('"Clip Collection\\tCtrl+Alt+C"', ui)
        self.assertIn('(\"<Control><Alt>C\", app.toggle_clip_collection)', ui)
        self.assertIn('f"<Control><Alt>{i}"', ui)

    def test_app_preserves_document_mutation_gateway_for_insert(self):
        method = method_source("on_clip_insert")
        self.assertIn('self.execute_command("Insert Clip", edit)', method)
        self.assertIn("self.clip_collection.selected_text()", method)
        self.assertNotIn("save_clips", method)

    def test_source_provenance_includes_new_boundaries(self):
        provenance = source(PROVENANCE)
        for module in (
            "calamus_clips",
            "calamus_clip_collection",
            "calamus_clip_panel",
            "calamus_right_panel",
        ):
            self.assertIn(f'"{module}"', provenance)


if __name__ == "__main__":
    unittest.main()
