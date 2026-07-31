import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "calamus" / "calamus_research_panel_view.py"
GATE = ROOT / "scripts" / "w95-true-gtk-app-gate.py"


def source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def function_source(path: Path, name: str) -> str:
    text = source(path)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(name)


class W95ResearchSelectorRepairTests(unittest.TestCase):
    def test_child_hierarchy_is_explicitly_visible_before_popup(self):
        view = source(VIEW)
        init = function_source(VIEW, "__init__")
        popup = function_source(VIEW, "popup")
        ensure = function_source(VIEW, "_ensure_popup_children_visible")
        show = function_source(VIEW, "_on_popover_show")

        self.assertIn("self._scroll.show_all()", init)
        self.assertLess(init.index("self._scroll.show_all()"), init.index("self.widget.set_popover"))
        self.assertIn("self._ensure_popup_children_visible()", popup)
        self.assertLess(popup.index("self._ensure_popup_children_visible()"), popup.index("self.popover.popup()"))
        self.assertIn("self._scroll.show_all()", ensure)
        self.assertIn("set_min_content_width", ensure)
        self.assertIn("self._ensure_popup_children_visible()", show)
        self.assertNotIn("Gtk.ComboBoxText", view)

    def test_true_gtk_gate_requires_real_mapping_allocation_and_activation(self):
        gate = source(GATE)
        exercise = function_source(GATE, "exercise_research_selector")
        desktop = function_source(GATE, "require_desktop_widget")

        self.assertIn("selector.widget.set_active(True)", exercise)
        self.assertIn("desktop_widget_ready(selector.popover)", exercise)
        self.assertIn("desktop_widget_ready(selector._scroll)", exercise)
        self.assertIn("desktop_widget_ready(selector.listbox)", exercise)
        self.assertIn("require_desktop_widget(selector.popover", exercise)
        self.assertIn("require_desktop_widget(selector._scroll", exercise)
        self.assertIn("require_desktop_widget(selector.listbox", exercise)
        self.assertIn('selector.listbox.emit("row-activated", target)', exercise)
        self.assertIn("app.research_panel_runtime.active_client == target_id", exercise)
        self.assertIn("not selector.popover.get_mapped()", exercise)
        self.assertIn("desktop_widget_ready(widget)", desktop)
        self.assertIn("W95_TRUE_RESEARCH_SELECTOR_VISIBLE_ACTIVATION=PASS", gate)


if __name__ == "__main__":
    unittest.main()
