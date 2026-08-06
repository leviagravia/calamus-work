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
RESEARCH = ROOT / "calamus" / "calamus_research_panel.py"
RESEARCH_VIEW = ROOT / "calamus" / "calamus_research_panel_view.py"
UI = ROOT / "calamus" / "calamus_ui.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"
CLIP_RUNTIME = ROOT / "calamus" / "calamus_clip_runtime.py"


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
        composition = source(ROOT / "calamus/calamus_clip_composition.py")
        root = source(ROOT / "calamus/calamus_application_composition.py")
        self.assertEqual(composition.count("RightPanelHost("), 1)
        self.assertNotIn("RightPanelHost(", launcher)
        self.assertIn("app.right_panel_host = right_panel_host", root)
        self.assertIn('self.right_panel_host.register("research", self.research_panel_view.widget)', launcher)
        self.assertNotIn('self.right_panel_host.register("clip-collection"', launcher)

    def test_launcher_no_longer_owns_raw_clip_or_reference_widgets(self):
        launcher = source(LAUNCHER)
        for forbidden in (
            "self.clips =",
            "self.clip_panel =",
            "self.clip_list =",
            "self.reference_list =",
            "self.reference_records =",
            "self.clip_panel_attached",
            "Gdk.EventType._2BUTTON_PRESS",
            "get_row_at_y",
        ):
            self.assertNotIn(forbidden, launcher)

    def test_toggle_is_a_thin_research_runtime_adapter(self):
        method = method_source("toggle_research_panel")
        self.assertIn("self.research_panel_runtime.toggle()", method)
        self.assertNotIn("pack2", method)
        self.assertNotIn("set_position", method)
        self.assertLessEqual(len(method.splitlines()), 3)

    def test_clip_controller_owns_persist_first_mutations(self):
        controller = source(CONTROLLER)
        self.assertIn("snapshot = self._store.save_snapshot", controller)
        self.assertIn("self._clips = committed", controller)
        self.assertLess(
            controller.index("snapshot = self._store.save_snapshot"),
            controller.index("self._clips = committed"),
        )
        self.assertIn("expected_revision=self._revision", controller)

    def test_view_adapter_owns_double_click_and_list_selection(self):
        panel = source(PANEL)
        self.assertIn("class ClipCollectionViewAdapter", panel)
        self.assertIn("def on_button_press", panel)
        self.assertIn("get_selected_row", panel)
        self.assertIn("get_row_at_index", panel)
        self.assertIn('clip_list.connect("button-press-event", adapter.on_button_press)', panel)
        self.assertIn('clip_list.connect("row-activated"', panel)
        self.assertIn("def selected_id", panel)

    def test_host_remains_generic_and_research_shell_owns_real_clients(self):
        host = source(HOST)
        research = source(RESEARCH)
        research_view = source(RESEARCH_VIEW)
        self.assertIn("self._sections", host)
        self.assertIn("self._paned.pack2(widget, False, True)", host)
        self.assertIn("self._detach_active(remember=True)", host)
        self.assertNotIn("references", host.lower())
        self.assertIn('self._host.show("research")', research)
        self.assertIn("register_client", research_view)
        launcher = source(LAUNCHER).lower()
        self.assertIn("source-notes", launcher)
        self.assertIn("scratchpad", launcher)
        self.assertNotIn("concepts", research_view.lower())

    def test_clip_store_is_markdown_primary_with_legacy_json_fallback(self):
        clips = source(CLIPS)
        self.assertIn('return os.path.join(config_dir, "clips.md")', clips)
        self.assertIn('return os.path.join(config_dir, "clips.json")', clips)
        self.assertIn("class MarkdownClipStore", clips)
        self.assertIn("def load_snapshot", clips)
        self.assertIn("def save_snapshot", clips)
        self.assertIn("legacy_clips_path", clips)
        self.assertNotIn("save_json_file", clips)

    def test_visible_command_moves_coherently_to_research_without_duplication(self):
        ui = source(UI)
        self.assertIn('"Research Panel\\tCtrl+Alt+C"', ui)
        self.assertIn('(\"<Control><Alt>C\", app.toggle_research_panel)', ui)
        self.assertIn('add_item(researchm, "Clip Collection", app.show_clip_collection)', ui)
        self.assertIn('add_item(researchm, "Bibliography", app.show_references)', ui)
        self.assertIn('add_item(researchm, "Source Notes", app.show_source_notes)', ui)
        self.assertIn('f"<Control><Alt>{i}"', ui)
        view_block = ui[ui.index('viewm = top_menu(app, "View")'):ui.index('optm = top_menu(app, "Options")')]
        self.assertNotIn("Clip Collection", view_block)

    def test_app_preserves_document_mutation_gateway_for_insert(self):
        adapter = method_source("on_clip_insert")
        gateway = source(CLIP_RUNTIME)
        self.assertIn("self.clip_collection_runtime.on_insert()", adapter)
        self.assertIn("def insert_clip_expansion_through_gateway", gateway)
        self.assertIn("def insert_clip_expansion(app", gateway)
        self.assertIn('execute_command("Insert Clip", edit)', gateway)
        self.assertIn("set_cursor_offset(caret)", gateway)
        self.assertIn('queue_insert_scroll(margin=0.15)', gateway)
        self.assertNotIn("select_range=(caret, caret)", gateway)
        self.assertNotIn("save_clips", gateway)

    def test_source_provenance_includes_new_boundaries(self):
        provenance = source(PROVENANCE)
        for module in (
            "calamus_clips",
            "calamus_clip_collection",
            "calamus_clip_search",
            "calamus_clip_expansion",
            "calamus_clip_panel",
            "calamus_clip_dialogs",
            "calamus_clip_runtime",
            "calamus_right_panel",
            "calamus_references",
            "calamus_reference_store",
            "calamus_reference_controller",
            "calamus_reference_panel",
            "calamus_reference_runtime",
            "calamus_research_file",
            "calamus_source_notes",
            "calamus_source_note_store",
            "calamus_source_note_controller",
            "calamus_source_note_panel",
            "calamus_source_note_dialogs",
            "calamus_source_note_runtime",
            "calamus_research_panel",
            "calamus_research_panel_view",
        ):
            self.assertIn(f'"{module}"', provenance)


if __name__ == "__main__":
    unittest.main()
