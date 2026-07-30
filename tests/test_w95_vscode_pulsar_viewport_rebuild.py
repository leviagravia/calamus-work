import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
RUNTIME = ROOT / "calamus" / "calamus_history_runtime.py"
GATE = ROOT / "scripts" / "w95-true-gtk-app-gate.py"
GUIDE = ROOT / "share" / "doc" / "calamus" / "USER_GUIDE.md"
AUDIT = ROOT / "docs" / "canonical" / "CALAMUS_W95_EDITOR_HISTORY_MATURE_SOURCE_AUDIT.md"


def source(path):
    return path.read_text(encoding="utf-8")


def method(path, name):
    text = source(path)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(name)


class W95VSCodePulsarViewportRebuildTests(unittest.TestCase):
    def test_app_passes_the_real_scroller_to_history_runtime(self):
        launcher = source(LAUNCHER)
        self.assertIn(
            "SnapshotHistoryRuntime(self.history, self.text, self.scroller, GLib, log_nonfatal)",
            launcher,
        )

    def test_viewport_projection_is_direct_geometry_not_scroll_to_mark(self):
        runtime = source(RUNTIME)
        projection = method(RUNTIME, "compute_vertical_reveal")
        attempt = method(RUNTIME, "_reveal_insert_once")
        self.assertIn("center_if_outside", projection)
        self.assertIn("upper", projection)
        self.assertIn("page_size", projection)
        self.assertIn("self._adjustment.set_value(target)", attempt)
        self.assertIn("self._reveal_geometry_ready", attempt)
        self.assertNotIn("scroll_to_mark", runtime)
        self.assertNotIn("scroll_to_iter", runtime)

    def test_viewport_retry_is_geometry_event_driven_not_timeout_driven(self):
        runtime = source(RUNTIME)
        constructor = method(RUNTIME, "__init__")
        queue = method(RUNTIME, "queue_scroll_to_insert")
        geometry = method(RUNTIME, "_on_view_geometry_changed")
        self.assertIn('"changed", self._on_view_geometry_changed', constructor)
        self.assertIn('"size-allocate", self._on_view_geometry_changed', constructor)
        self.assertIn("self.reveal_pending = True", queue)
        self.assertIn("self._schedule_reveal_idle()", geometry)
        self.assertNotIn("timeout_add", queue)
        self.assertNotIn("usleep", runtime)

    def test_gate_waits_for_full_reveal_state_not_only_idle_exit(self):
        gate = method(GATE, "drain_history_scroll")
        self.assertIn("app.history_runtime.scroll_source is None", gate)
        self.assertIn("not app.history_runtime.reveal_pending", gate)

    def test_help_explains_geometry_owned_reveal(self):
        guide = source(GUIDE)
        self.assertIn("waits for valid GTK scroll geometry", guide)
        self.assertIn("vertical adjustment", guide)
        self.assertIn("not a chain of timeouts", guide)

    def test_audit_records_vscode_and_pulsar_direct_findings(self):
        audit = source(AUDIT)
        self.assertIn("Visual Studio Code 1.131.0", audit)
        self.assertIn("beforeCursorState", audit)
        self.assertIn("afterCursorState", audit)
        self.assertIn("Pulsar 1.132.0-dev", audit)
        self.assertIn("selectionsMarkerLayer", audit)
        self.assertIn("getLastSelection().autoscroll()", audit)


if __name__ == "__main__":
    unittest.main()
