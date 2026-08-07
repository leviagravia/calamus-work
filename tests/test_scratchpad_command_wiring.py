import ast
import unittest
from tests.w104_command_test_support import guide_has
from pathlib import Path

from tests.w105_menu_test_support import legacy_menu_projection
from tests.w107_source_test_support import authoritative_method_source, app_method_source, research_composition_source, workspace_host_source

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"


def source(path):
    return path.read_text(encoding="utf-8")


def method_source(name):
    return authoritative_method_source(name)


class ScratchpadCommandWiringTests(unittest.TestCase):
    def test_modules_exist_and_are_provenance_tracked(self):
        modules = (
            "calamus_managed_sidecars",
            "calamus_scratchpad",
            "calamus_scratchpad_store",
            "calamus_scratchpad_controller",
            "calamus_scratchpad_panel",
            "calamus_scratchpad_dialogs",
            "calamus_scratchpad_runtime",
            "calamus_scratchpad_gateway",
        )
        provenance = source(PROVENANCE)
        for module in modules:
            self.assertTrue((ROOT / "calamus" / f"{module}.py").exists())
            self.assertIn(f'"{module}"', provenance)

    def test_basic_contract_is_visible_without_concept_or_question_types(self):
        model = source(ROOT / "calamus/calamus_scratchpad.py")
        self.assertIn('_TYPES = ("note", "idea", "draft", "task")', model)
        self.assertNotIn('"concept"', model)
        self.assertNotIn('"question"', model)
        ui = legacy_menu_projection()
        for command in (
            'add_item(researchm, "Scratchpad\\tCtrl+Alt+S", app.show_scratchpad)',
            '"Capture Selection in Scratchpad…\\tCtrl+Alt+Shift+S"',
            '"New Scratchpad Entry for Current Section…"',
            '"Show Scratchpad for Current Section"',
        ):
            self.assertIn(command, ui)

    def test_research_shell_registers_one_real_scratchpad_client(self):
        composition = research_composition_source()
        self.assertEqual(composition.count('"scratchpad", "Scratchpad"'), 1)
        self.assertIn("ScratchpadRuntime(", composition)
        self.assertIn("scratchpad_runtime.activate", composition)
        clip_composition = source(ROOT / "calamus/calamus_clip_composition.py")
        self.assertEqual(clip_composition.count("RightPanelHost("), 1)
        self.assertNotIn("RightPanelHost(", source(LAUNCHER))

    def test_document_mutation_and_clipboard_use_app_gateways(self):
        insert = method_source("insert_scratchpad_body")
        copy_method = method_source("copy_scratchpad_body")
        clipboard = source(ROOT / "calamus/calamus_clipboard_gtk.py")
        self.assertIn('self.ports.execute_command("Insert Scratchpad Body", edit)', insert)
        self.assertIn("self.ports.copy_text(body)", copy_method)
        self.assertIn("clipboard.set_text", clipboard)
        self.assertTrue(guide_has("Research", "Scratchpad", "Ctrl+Alt+S"))
        self.assertTrue(guide_has("Research", "Capture Selection in Scratchpad", "Ctrl+Alt+Shift+S"))
        self.assertNotIn("open(", insert)

    def test_model_store_controller_are_gtk_free(self):
        for relative in (
            "calamus/calamus_scratchpad.py",
            "calamus/calamus_scratchpad_store.py",
            "calamus/calamus_scratchpad_controller.py",
        ):
            text = source(ROOT / relative)
            self.assertNotIn("from gi", text, relative)
            self.assertNotIn("import gi", text, relative)
            for symbol in ("Gtk.", "Gdk.", "GLib.", "Pango."):
                self.assertNotIn(symbol, text, relative)

    def test_full_phase_authorities_are_not_implemented_in_basic(self):
        combined = "\n".join(source(ROOT / f"calamus/calamus_scratchpad_{name}.py") for name in ("store", "controller", "panel", "dialogs", "runtime"))
        for forbidden in ("Reference key", "Source Note", "Related Entries", "knowledge graph", "SQLite"):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
