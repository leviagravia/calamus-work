import ast
import unittest
from tests.w104_command_test_support import guide_has
from pathlib import Path


from tests.w105_menu_test_support import legacy_menu_projection
ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
SHORTCUTS = ROOT / "calamus" / "calamus_shortcuts.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"
GUIDE = ROOT / "share" / "doc" / "calamus" / "USER_GUIDE.md"


def source(path):
    return path.read_text(encoding="utf-8")


def method_source(name):
    text = source(LAUNCHER)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(name)


class AuthoringBridgeCommandWiringTests(unittest.TestCase):
    def test_modules_exist_and_are_source_provenance_tracked(self):
        modules = (
            "calamus_authoring_bridge",
            "calamus_authoring_bridge_controller",
            "calamus_authoring_bridge_view",
            "calamus_authoring_bridge_dialogs",
            "calamus_authoring_bridge_runtime",
        )
        provenance = source(PROVENANCE)
        for module in modules:
            self.assertTrue((ROOT / "calamus" / f"{module}.py").exists())
            self.assertIn(f'"{module}"', provenance)

    def test_research_menu_and_single_panel_expose_exact_w88_actions(self):
        ui = legacy_menu_projection()
        build = method_source("build_research_panel")
        self.assertIn('"Authoring Bridge", app.show_authoring_bridge', ui)
        self.assertIn('"Create Source Note from Selection…"', ui)
        self.assertIn('"Insert Link to Heading…"', ui)
        self.assertIn('"authoring-bridge"', build)
        self.assertIn('"Authoring Bridge"', build)
        self.assertIn("AuthoringBridgeRuntime(", build)
        self.assertEqual(source(ROOT / "calamus" / "calamus_research_panel_view.py").count("Gtk.Stack()"), 1)

    def test_document_mutation_uses_execute_command_and_source_note_uses_existing_runtime(self):
        apply_method = method_source("apply_heading_link_plan")
        menu_method = method_source("on_create_source_note_from_selection")
        persist_method = method_source("create_source_note_from_authoring_snapshot")
        snapshot_method = method_source("authoring_selection_snapshot")
        self.assertIn('self.execute_command(', apply_method)
        self.assertIn('"Insert Link to Heading"', apply_method)
        self.assertIn('self.buffer_text() != plan.document_before', apply_method)
        self.assertIn('self.authoring_bridge_runtime.on_create_source_note()', menu_method)
        self.assertIn('self.source_note_panel_runtime.add_from_selection(', persist_method)
        self.assertIn('EditorSelectionSnapshot(', snapshot_method)
        self.assertNotIn("open(", apply_method)
        self.assertNotIn("MarkdownSourceNoteStore", persist_method)

    def test_app_remains_composition_and_thin_navigation_gateway(self):
        self.assertLessEqual(len(method_source("show_authoring_bridge").splitlines()), 2)
        self.assertLessEqual(len(method_source("show_source_note_id").splitlines()), 3)
        self.assertLessEqual(len(method_source("source_notes_snapshot").splitlines()), 3)
        self.assertLessEqual(
            len(method_source("on_create_source_note_from_selection").splitlines()), 2
        )
        self.assertNotIn("parse_markdown_heading_links", source(LAUNCHER))
        self.assertNotIn("build_authoring_bridge_projection", source(LAUNCHER))
        self.assertNotIn("unique_heading_identifier_at_offset", source(LAUNCHER))


    def test_modal_dialog_fields_are_semantically_named_and_undo_is_effect_checked(self):
        source_note_dialog = source(ROOT / "calamus" / "calamus_source_note_dialogs.py")
        heading_dialog = source(ROOT / "calamus" / "calamus_authoring_bridge_dialogs.py")
        desktop_test = source(ROOT / "tests" / "test_authoring_bridge_app_desktop_e2e.py")
        for name in (
            "calamus-source-note-dialog",
            "source-note-text",
            "source-note-comment",
            "source-note-reference",
            "source-note-target",
        ):
            self.assertIn(f'"{name}"', source_note_dialog)
        for name in (
            "calamus-heading-link-dialog",
            "heading-link-target",
            "heading-link-label",
            "heading-link-preview",
        ):
            self.assertIn(f'"{name}"', heading_dialog)
        self.assertNotIn("_descendants(dialog, Gtk.TextView)", desktop_test)
        self.assertNotIn("assertTrue(win.on_undo())", desktop_test)
        self.assertIn("undo_result = win.on_undo()", desktop_test)
        self.assertIn("self.assertEqual(win.buffer_text(), original_document)", desktop_test)

    def test_no_forbidden_persistence_or_dynamic_w89_w90_scope(self):
        combined = "\n".join(
            source(ROOT / "calamus" / name)
            for name in (
                "calamus_authoring_bridge.py",
                "calamus_authoring_bridge_controller.py",
                "calamus_authoring_bridge_view.py",
                "calamus_authoring_bridge_dialogs.py",
                "calamus_authoring_bridge_runtime.py",
            )
        ).casefold()
        for forbidden in (
            "sqlite",
            "watchdog",
            "lsp",
            "subprocess",
            "named set",
            "citeproc",
        ):
            self.assertNotIn(forbidden, combined)

    def test_shortcut_registry_and_user_guide_cover_visible_commands(self):
        guide = source(GUIDE)
        for command in (
            "Authoring Bridge",
            "Create Source Note from Selection",
            "Insert Link to Heading",
        ):
            self.assertTrue(guide_has("Research", command, "menu"))
            self.assertIn(command, guide)
        self.assertIn("Refresh after document", guide)
        self.assertIn("one Undo unit", guide)
        self.assertIn("creates no database", guide)


if __name__ == "__main__":
    unittest.main()
