import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
RUNTIME = ROOT / "calamus" / "calamus_history_runtime.py"
VIEWPORT_RUNTIME = ROOT / "calamus" / "calamus_viewport_runtime.py"
VIEWPORT_POLICY = ROOT / "calamus" / "calamus_viewport.py"
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
        composition = source(ROOT / "calamus/calamus_editor_composition.py")
        self.assertEqual(composition.count("EditorViewportRuntime("), 1)
        self.assertIn(
            "inputs.text_view,\n        inputs.scroller,\n        GLib,\n        log_nonfatal",
            composition,
        )
        self.assertIn("viewport_runtime=viewport_runtime", composition)

    def test_viewport_projection_is_direct_geometry_not_scroll_to_mark(self):
        policy = source(VIEWPORT_POLICY)
        owner = source(VIEWPORT_RUNTIME)
        self.assertIn("def compute_vertical_reveal", policy)
        self.assertIn("get_iter_location", owner)
        self.assertIn("get_visible_rect", owner)
        self.assertIn("self._adjustment.set_value", owner)
        self.assertNotIn("scroll_to_mark", owner)
        self.assertNotIn("scroll_to_iter", owner)

    def test_viewport_retry_is_geometry_event_driven_not_timeout_driven(self):
        owner = source(VIEWPORT_RUNTIME)
        constructor = method(VIEWPORT_RUNTIME, "__init__")
        geometry = method(VIEWPORT_RUNTIME, "_on_geometry_changed")
        queue = method(VIEWPORT_RUNTIME, "_replace_request")
        self.assertIn('"changed", self._on_geometry_changed', constructor)
        self.assertIn('"size-allocate", self._on_geometry_changed', constructor)
        self.assertIn("self.reveal_pending = True", queue)
        self.assertIn("self._schedule_idle()", geometry)
        self.assertNotIn("timeout_add", owner)
        self.assertNotIn("usleep", owner)

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
