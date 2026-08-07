import ast
import os
import unittest
from pathlib import Path


from tests.w105_menu_test_support import legacy_menu_projection
from tests.w107_source_test_support import authoritative_method_source, app_method_source, research_composition_source, workspace_host_source

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
    return authoritative_method_source(name)


class RightPanelCommandWiringTests(unittest.TestCase):
    def test_startup_has_one_right_panel_host_authority(self):
        launcher = source(LAUNCHER)
        composition = source(ROOT / "calamus/calamus_clip_composition.py")
        root = source(ROOT / "calamus/calamus_application_composition.py")
        research = research_composition_source()
        self.assertEqual(composition.count("RightPanelHost("), 1)
        self.assertNotIn("RightPanelHost(", launcher)
        self.assertIn("app.right_panel_host = right_panel_host", root)
        self.assertIn('inputs.right_panel_host.register("research", panel_view.widget)', research)
        self.assertNotIn('register("clip-collection"', research)

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
        app_method = app_method_source("toggle_research_panel")
        runtime_method = method_source("toggle_research_panel")
        self.assertIn("self._research_components.runtime.toggle_research_panel", app_method)
        self.assertIn("self.components.panel_runtime.toggle()", runtime_method)
        self.assertNotIn("pack2", runtime_method)
        self.assertNotIn("set_position", runtime_method)
        self.assertLessEqual(len(app_method.splitlines()), 2)

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
        composition = research_composition_source()
        self.assertIn("self._sections", host)
        self.assertIn("self._paned.pack2(widget, False, True)", host)
        self.assertIn("self._detach_active(remember=True)", host)
        self.assertNotIn("references", host.lower())
        self.assertIn('self._host.show("research")', research)
        self.assertIn("register_client", research_view)
        self.assertIn("source-notes", composition)
        self.assertIn("scratchpad", composition)
        self.assertNotIn('"concepts"', composition)

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
        ui = legacy_menu_projection()
        self.assertIn('"Research Panel\\tCtrl+Alt+C"', ui)
        self.assertIn("command_shortcut_bindings()", ui)
        self.assertIn('add_item(researchm, "Clip Collection", app.show_clip_collection)', ui)
        self.assertIn('add_item(researchm, "Bibliography", app.show_references)', ui)
        self.assertIn('add_item(researchm, "Source Notes", app.show_source_notes)', ui)
        from tests.w104_command_test_support import actual_binding_has
        for i in range(1, 10):
            self.assertTrue(actual_binding_has("research.insert-clip-slot", f"<Control><Alt>{i}", number=i))
        view_block = ui[ui.index('viewm = top_menu(app, "View")'):ui.index('optm = top_menu(app, "Options")')]
        self.assertNotIn("Clip Collection", view_block)

    def test_app_preserves_document_mutation_gateway_for_insert(self):
        app_adapter = app_method_source("on_clip_insert")
        runtime_adapter = method_source("on_clip_insert")
        gateway = source(CLIP_RUNTIME)
        self.assertIn("self._research_components.runtime.on_clip_insert", app_adapter)
        self.assertIn("self.components.clip_collection_runtime.on_insert()", runtime_adapter)
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
