import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
HISTORY = ROOT / "calamus" / "calamus_history.py"
RUNTIME = ROOT / "calamus" / "calamus_history_runtime.py"
CLIP_RUNTIME = ROOT / "calamus" / "calamus_clip_runtime.py"
VIEWPORT_RUNTIME = ROOT / "calamus" / "calamus_viewport_runtime.py"
GATE = ROOT / "scripts" / "w95-true-gtk-app-gate.py"
GUIDE = ROOT / "share" / "doc" / "calamus" / "USER_GUIDE.md"


def text(path):
    return path.read_text(encoding="utf-8")


def method(path, name):
    source = text(path)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(name)


class W95MatureHistoryRebuildTests(unittest.TestCase):
    def test_history_state_owns_insert_and_selection_bound(self):
        source = text(HISTORY)
        self.assertIn("class HistoryState", source)
        self.assertIn("insert_offset", source)
        self.assertIn("selection_bound_offset", source)
        self.assertIn("replace_current_view_state", source)
        self.assertNotIn("undo_stack: list[str]", source)

    def test_runtime_preserves_mark_direction_and_geometry_owned_reveal(self):
        history_source = text(RUNTIME)
        owner_source = text(VIEWPORT_RUNTIME)
        restore = method(RUNTIME, "restore_buffer_state")
        self.assertIn("buffer.select_range(insert, bound)", restore)
        self.assertNotIn("buffer.get_selection_bounds", restore)
        queue = method(VIEWPORT_RUNTIME, "queue_visible_to_insert")
        schedule = method(VIEWPORT_RUNTIME, "_schedule_idle")
        attempt = method(VIEWPORT_RUNTIME, "_apply_once")
        self.assertIn("self._replace_request", queue)
        self.assertIn("priority=self.glib.PRIORITY_LOW", schedule)
        self.assertIn("compute_vertical_reveal", attempt)
        self.assertIn("self._adjustment.set_value(target)", attempt)
        self.assertIn("self._measure()", attempt)
        self.assertNotIn("scroll_to_mark", history_source + owner_source)
        self.assertNotIn("GLib.usleep", history_source + owner_source)

    def test_launcher_eliminates_diff_estimation_and_uses_real_undo_state(self):
        source = text(LAUNCHER)
        transaction = text(ROOT / "calamus/calamus_editor_transaction.py")
        adapter = text(ROOT / "calamus/calamus_editor_buffer_adapter.py")
        self.assertNotIn("estimate_history_cursor", source + transaction)
        self.assertIn("self.editor_transaction.undo()", source)
        self.assertIn("self.editor_transaction.redo()", source)
        self.assertIn("self.history_runtime.undo_target()", transaction)
        self.assertIn("self.history_runtime.redo_target()", transaction)
        self.assertIn("self.buffer_adapter.restore(state)", transaction)
        self.assertIn("buffer.select_range(insert, bound)", adapter)
        composition = text(ROOT / "calamus/calamus_editor_composition.py")
        self.assertIn('_connect(buffer, "begin-user-action"', composition)
        self.assertIn('_connect(buffer, "end-user-action"', composition)

    def test_clip_marker_updates_the_committed_post_edit_caret(self):
        source = method(CLIP_RUNTIME, "insert_clip_expansion_through_gateway")
        self.assertLess(source.index("set_cursor_offset(caret)"), source.index("sync_history_view_state()"))
        self.assertIn("sync_history_view_state", source)

    def test_true_gate_runs_on_undo_and_checks_caret_selection_and_viewport(self):
        source = text(GATE)
        self.assertIn("app.on_undo()", source)
        self.assertIn("exercise_undo_selection_state", source)
        self.assertNotIn("app.set_text_from_history(long_text", source)
        self.assertIn("W95_TRUE_UNDO_SELECTION=PASS", source)
        self.assertIn("W95_TRUE_REDO_STATE=PASS", source)
        self.assertIn("app.on_redo()", source)
        self.assertIn("drain_history_scroll(app)", source)
        self.assertIn("app.history_runtime.scroll_source is None", source)
        self.assertNotIn("time.sleep(", source)

    def test_ui_callbacks_keep_none_contract_and_gate_checks_effect(self):
        undo = method(LAUNCHER, "on_undo")
        redo = method(LAUNCHER, "on_redo")
        gate = text(GATE)
        self.assertNotIn("return True", undo)
        self.assertNotIn("return False", undo)
        self.assertNotIn("return True", redo)
        self.assertNotIn("return False", redo)
        self.assertIn("def invoke_undo", gate)
        self.assertIn("def invoke_redo", gate)
        self.assertIn("app.history.can_undo", gate)
        self.assertIn("app.history.can_redo", gate)
        self.assertNotIn("require(app.on_undo()", gate)
        self.assertNotIn("require(app.on_redo()", gate)

    def test_help_explains_exact_caret_selection_restore(self):
        source = text(GUIDE)
        self.assertIn("exact caret and selection", source)
        self.assertIn("does not guess the edit position from a text diff", source)


if __name__ == "__main__":
    unittest.main()
