import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
LIFECYCLE = ROOT / "calamus" / "calamus_file_lifecycle.py"


def _method_source(name: str) -> str:
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"method {name!r} not found")


class SaveCommandWiringTests(unittest.TestCase):
    def test_visible_save_command_keeps_named_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(filem, "Save\\tCtrl+S", app.on_save)', ui)

    def test_on_save_delegates_to_save_file(self):
        method = _method_source("on_save")
        self.assertIn("self.save_file()", method)

    def test_save_file_delegates_preflight_to_lifecycle_plan(self):
        method = _method_source("save_file")
        self.assertIn("prepare_save_plan(", method)
        self.assertIn("trim_trailing_on_save=getattr(", method)
        self.assertIn("if plan.requires_destination:", method)
        self.assertIn("return self.save_as()", method)
        self.assertIn("self.document.save(plan.target_path, plan.text_to_write)", method)

    def test_save_file_no_longer_computes_trailing_cleanup_inline(self):
        method = _method_source("save_file")
        self.assertNotIn("remove_trailing_spaces(", method)
        self.assertNotIn("trimmed =", method)

    def test_save_file_keeps_gtk_and_io_boundaries_in_app(self):
        method = _method_source("save_file")
        self.assertIn("self.text.get_buffer().set_text(plan.text_to_write)", method)
        self.assertIn("self.document.save(", method)
        self.assertIn("self.error(str(e))", method)
        lifecycle = LIFECYCLE.read_text(encoding="utf-8")
        lifecycle_tree = ast.parse(lifecycle)
        imported_modules = []
        for node in ast.walk(lifecycle_tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)
        self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imported_modules))
        self.assertNotIn("write_text_file", lifecycle)
        self.assertNotIn("open(", lifecycle)

    def test_save_as_open_new_and_quit_are_not_rewired_by_phase1_save(self):
        self.assertNotIn("prepare_save_plan", _method_source("save_as"))
        self.assertNotIn("prepare_save_plan", _method_source("on_open"))
        self.assertNotIn("prepare_save_plan", _method_source("on_new"))
        self.assertNotIn("prepare_save_plan", _method_source("on_quit"))

    def test_no_command_layer_identity_is_added_for_file_save(self):
        lifecycle = LIFECYCLE.read_text(encoding="utf-8")
        self.assertNotIn("CommandLayer", lifecycle)
        self.assertNotIn("CommandContext", lifecycle)
        self.assertNotIn("file.save", lifecycle)


if __name__ == "__main__":
    unittest.main()
