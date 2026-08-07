import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
CLIP_RUNTIME = ROOT / "calamus" / "calamus_clip_runtime.py"
RESEARCH_VIEW = ROOT / "calamus" / "calamus_research_panel_view.py"
GATE = ROOT / "scripts" / "w95-true-gtk-app-gate.py"
GUIDE = ROOT / "share" / "doc" / "calamus" / "USER_GUIDE.md"


def source(path):
    return path.read_text(encoding="utf-8")


def method_source(path, name):
    text = source(path)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(name)


class W95R4DesktopRepairTests(unittest.TestCase):
    def test_clip_gateway_places_caret_explicitly_after_grouped_edit(self):
        runtime = source(CLIP_RUNTIME)
        method = method_source(CLIP_RUNTIME, "insert_clip_expansion_through_gateway")
        self.assertLess(method.index('execute_command("Insert Clip", edit)'), method.index("set_cursor_offset(caret)"))
        self.assertIn('queue_insert_scroll(margin=0.15)', method)
        self.assertNotIn("select_range=(caret, caret)", method)

    def test_programmatic_cursor_and_history_use_one_bounded_viewport_repair(self):
        method = method_source(LAUNCHER, "set_cursor_offset")
        self.assertIn("buf.place_cursor(it)", method)
        self.assertNotIn("self.text.scroll_to_iter", method)
        self.assertIn("self.queue_insert_scroll(margin=0.15)", method)
        history = method_source(LAUNCHER, "set_text_from_history")
        projection = method_source(LAUNCHER, "_project_history_restore")
        transaction = source(ROOT / "calamus/calamus_editor_transaction.py")
        self.assertIn("self.editor_transaction.restore_history_state", history)
        self.assertIn("self.buffer_adapter.restore(state)", transaction)
        self.assertIn("self.typewriter_runtime.on_history()", projection)
        self.assertIn("self.viewport_runtime.queue_visible_to_insert", projection)
        self.assertIn("center_if_outside=True", projection)

    def test_research_selector_is_downward_popover_not_aligning_combo(self):
        view = source(RESEARCH_VIEW)
        self.assertIn("class ResearchClientSelector", view)
        self.assertIn("Gtk.MenuButton", view)
        self.assertIn("Gtk.Popover", view)
        self.assertIn("Gtk.PositionType.BOTTOM", view)
        self.assertIn("adjustment.set_value(adjustment.get_lower())", view)
        self.assertNotIn("Gtk.ComboBoxText", view)
        self.assertIn("def get_active_id", view)
        self.assertIn("def set_active_id", view)

    def test_true_gate_covers_all_cursor_extremes_and_callback_failures(self):
        gate = source(GATE)
        for body in (
            "{{cursor}}TESTO",
            "TESTO{{cursor}}",
            "PRIMA {{cursor}} DOPO",
        ):
            self.assertIn(body, gate)
        self.assertIn("class AsyncDialogDriver", gate)
        self.assertIn("driver.raise_if_failed()", gate)
        self.assertIn("W95_TRUE_CURSOR_EXTREMES=PASS", gate)
        self.assertIn("W95_TRUE_RESEARCH_SELECTOR_DOWNWARD=PASS", gate)

    def test_help_documents_visible_repairs(self):
        guide = source(GUIDE)
        self.assertIn("selector opens **below** the control", guide)
        self.assertIn("return the viewport to the restored caret position", guide)
        self.assertIn("if the marker is first, last or in the middle", guide)


if __name__ == "__main__":
    unittest.main()
