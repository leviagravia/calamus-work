import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
SHORTCUTS = ROOT / "calamus" / "calamus_shortcuts.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"


def function_source(path, name):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"{name} not found")


class DocumentStructureCommandWiringTests(unittest.TestCase):
    def test_source_modules_are_present_and_provenance_tracked(self):
        for name in (
            "calamus_document_structure.py",
            "calamus_navigation_gateway.py",
            "calamus_navigation_view.py",
            "calamus_navigation_dialogs.py",
        ):
            self.assertTrue((ROOT / "calamus" / name).exists(), name)
            self.assertIn(name[:-3], PROVENANCE.read_text(encoding="utf-8"))

    def test_launcher_builds_one_controller_authority(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("from calamus_navigation_gateway import NavigationController", source)
        self.assertIn("from calamus_navigation_view import NavigationViewAdapter", source)
        self.assertEqual(source.count("NavigationController("), 1)
        self.assertIn("self.navigation_controller = NavigationController(", source)

    def test_buffer_change_invalidates_structure_without_parsing_inline(self):
        source = function_source(LAUNCHER, "on_changed")
        self.assertIn("self.navigation_controller.invalidate()", source)
        self.assertNotIn("build_document_structure", source)
        self.assertNotIn("re.", source)

    def test_callbacks_are_thin_and_non_mutating(self):
        go = function_source(LAUNCHER, "on_go_to_section")
        nxt = function_source(LAUNCHER, "on_next_heading")
        prev = function_source(LAUNCHER, "on_previous_heading")
        self.assertIn("run_go_to_line_dialog", function_source(LAUNCHER, "on_go_to_line"))
        self.assertIn("run_go_to_section_dialog", go)
        self.assertIn("self.navigation_controller.next_heading()", nxt)
        self.assertIn("self.navigation_controller.previous_heading()", prev)
        for block in (go, nxt, prev):
            self.assertNotIn("execute_command", block)
            self.assertNotIn("self.text.get_buffer().set_text", block)
            self.assertNotIn("begin_user_action", block)

    def test_navigation_dialogs_preserve_invalid_line_feedback_and_current_section(self):
        source = (ROOT / "calamus" / "calamus_navigation_dialogs.py").read_text(encoding="utf-8")
        self.assertIn('status.set_text("Invalid line number.")', source)
        self.assertIn("current = controller.current_heading()", source)
        self.assertIn("selection.select_path(selected_path if selected_path is not None else 0)", source)

    def test_navigate_menu_is_between_edit_and_revise(self):
        source = function_source(UI, "build_menu")
        edit = source.index('editm = top_menu(app, "Edit")')
        navigate = source.index('navigatem = top_menu(app, "Navigate")')
        revise = source.index('revisem = top_menu(app, "Revise")')
        self.assertLess(edit, navigate)
        self.assertLess(navigate, revise)

    def test_go_to_line_moves_to_navigate_and_new_commands_are_exposed(self):
        source = function_source(UI, "build_menu")
        edit_block = source[source.index('editm = top_menu(app, "Edit")'):source.index('navigatem = top_menu(app, "Navigate")')]
        navigate_block = source[source.index('navigatem = top_menu(app, "Navigate")'):source.index('revisem = top_menu(app, "Revise")')]
        self.assertNotIn("Go to Line", edit_block)
        self.assertIn('Go to Line…\\tCtrl+L', navigate_block)
        self.assertIn('Go to Section…\\tCtrl+Shift+L', navigate_block)
        self.assertIn('Next Heading\\tCtrl+PageDown', navigate_block)
        self.assertIn('Previous Heading\\tCtrl+PageUp', navigate_block)

    def test_bookmarks_are_not_recomposed_in_w70(self):
        source = function_source(UI, "build_menu")
        navigate_block = source[source.index('navigatem = top_menu(app, "Navigate")'):source.index('revisem = top_menu(app, "Revise")')]
        revise_block = source[source.index('revisem = top_menu(app, "Revise")'):source.index('viewm = top_menu(app, "View")')]
        self.assertNotIn("Bookmark", navigate_block)
        self.assertIn("Insert Bookmark Here", revise_block)
        self.assertIn("Manage Bookmarks", revise_block)

    def test_shortcuts_use_canonical_navigate_identity(self):
        source = SHORTCUTS.read_text(encoding="utf-8")
        self.assertIn('ShortcutSpec("Navigate", "Go to Line", "Ctrl+L")', source)
        self.assertIn('ShortcutSpec("Navigate", "Go to Section", "Ctrl+Shift+L")', source)
        self.assertIn('ShortcutSpec("Navigate", "Next Heading", "Ctrl+PageDown")', source)
        self.assertIn('ShortcutSpec("Navigate", "Previous Heading", "Ctrl+PageUp")', source)
        self.assertNotIn('ShortcutSpec("Edit", "Go to Line", "Ctrl+L")', source)

    def test_w71_reuses_w70_structure_without_structural_editing(self):
        source = LAUNCHER.read_text(encoding="utf-8") + UI.read_text(encoding="utf-8")
        self.assertIn("Navigator Panel", source)
        self.assertNotIn("Move Section", source)
        self.assertNotIn("Rename Header", source)
        self.assertNotIn("Refresh Section List", source)
        self.assertNotIn("Setext", source)


if __name__ == "__main__":
    unittest.main()
