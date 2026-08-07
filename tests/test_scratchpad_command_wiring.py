import ast
import unittest
from tests.w104_command_test_support import guide_has
from pathlib import Path

from tests.w105_menu_test_support import legacy_menu_projection
ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"


def source(path):
    return path.read_text(encoding="utf-8")


def method_source(name):
    text = source(LAUNCHER)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(name)


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
        block = method_source("build_research_panel")
        self.assertEqual(block.count('"scratchpad"'), 1)
        self.assertIn("ScratchpadRuntime(", block)
        self.assertIn("self.scratchpad_runtime.activate", block)
        composition = source(ROOT / "calamus/calamus_clip_composition.py")
        self.assertEqual(composition.count("RightPanelHost("), 1)
        self.assertNotIn("RightPanelHost(", source(LAUNCHER))

    def test_document_mutation_and_clipboard_use_app_gateways(self):
        gateway = source(ROOT / "calamus/calamus_scratchpad_gateway.py")
        self.assertIn('app.execute_command("Insert Scratchpad Body"', gateway)
        self.assertTrue(guide_has("Research", "Scratchpad", "Ctrl+Alt+S"))
        self.assertTrue(guide_has("Research", "Capture Selection in Scratchpad", "Ctrl+Alt+Shift+S"))
        self.assertIn("app.text.grab_focus()", gateway)
        self.assertIn("clipboard.set_text", gateway)
        self.assertNotIn("open(", gateway)
        block = method_source("build_research_panel")
        self.assertIn("scratchpad_insert_body(self, body)", block)
        self.assertIn("scratchpad_copy_body(self, body)", block)

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
