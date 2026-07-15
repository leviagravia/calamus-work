import ast
import copy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
LIFECYCLE = ROOT / "calamus" / "calamus_file_lifecycle.py"


def _method_node(name: str):
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return source, node
    raise AssertionError(f"method {name!r} not found")


def _method_source(name: str) -> str:
    source, node = _method_node(name)
    return ast.get_source_segment(source, node) or ""


def _compiled_method(name: str, namespace=None):
    _source, node = _method_node(name)
    isolated = copy.deepcopy(node)
    module = ast.Module(body=[isolated], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = dict(namespace or {})
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return scope[name]


class _Buffer:
    def __init__(self, events, *, fail=False):
        self.events = events
        self.fail = fail
        self.text = "old buffer"

    def set_text(self, text):
        self.events.append(("buffer", text))
        if self.fail:
            raise RuntimeError("GTK buffer failure")
        self.text = text


class _TextView:
    def __init__(self, buffer):
        self.buffer = buffer

    def get_buffer(self):
        return self.buffer


class _Document:
    def __init__(self, events):
        self.events = events
        self.file_path = "/tmp/original.txt"
        self.text = "old document"
        self.modified = True

    def set_text(self, text, *, modified=True):
        self.events.append(("document", text, modified))
        self.text = text
        self.modified = bool(modified)

    def clear(self):
        raise AssertionError("W49 visible New must not clear identity before Gtk accepts text")


class _FakeApp:
    def __init__(self, *, buffer_fail=False):
        self.events = []
        self.document = _Document(self.events)
        self.current_file = self.document.file_path
        self.modified = True
        self.loading = False
        self.text = _TextView(_Buffer(self.events, fail=buffer_fail))

    def reset_undo_history(self):
        self.events.append(("reset-undo",))

    def update_title(self):
        self.events.append(("title",))


class NewCommandWiringTests(unittest.TestCase):
    def test_visible_new_command_and_shortcut_keep_named_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(filem, "New\\tCtrl+N", app.on_new)', ui)
        self.assertIn('("<Control>N", app.on_new)', ui)

    def test_on_new_preserves_save_prompt_then_delegates_to_plan_executor(self):
        method = _method_source("on_new")
        self.assertIn("if not self.may_continue():", method)
        self.assertIn("self.execute_new_plan(prepare_new_plan())", method)
        self.assertLess(method.index("self.may_continue()"), method.index("prepare_new_plan()"))
        self.assertNotIn("self.document.clear()", method)
        self.assertNotIn("self.set_buffer(", method)
        self.assertNotIn("self.current_file =", method)
        self.assertNotIn("self.modified =", method)

    def test_cancelled_new_stops_before_plan_and_executor(self):
        events = []

        def prepare():
            events.append("plan")
            return object()

        on_new = _compiled_method("on_new", {"prepare_new_plan": prepare})

        class App:
            def may_continue(self):
                events.append("prompt")
                return False

            def execute_new_plan(self, _plan):
                events.append("execute")

        self.assertIsNone(on_new(App()))
        self.assertEqual(events, ["prompt"])

    def test_new_plan_module_is_pure_and_has_no_gtk_io_or_command_layer(self):
        source = LIFECYCLE.read_text(encoding="utf-8")
        self.assertIn("class NewPlan", source)
        self.assertIn("def prepare_new_plan()", source)
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports))
        self.assertNotIn("CommandLayer", source)
        self.assertNotIn("open(", _method_source_from_file(LIFECYCLE, "prepare_new_plan"))

    def test_executor_commits_empty_identity_only_after_buffer_accepts_text(self):
        method = _method_source("execute_new_plan")
        buffer_at = method.index("self.text.get_buffer().set_text(plan.text)")
        identity_at = method.index("self.document.file_path = plan.target_path")
        reset_at = method.index("self.reset_undo_history()")
        self.assertLess(buffer_at, identity_at)
        self.assertLess(identity_at, reset_at)
        self.assertIn("finally:", method)
        self.assertIn("self.loading = False", method)
        self.assertNotIn("add_recent_file", method)
        self.assertNotIn("save_settings", method)

    def test_buffer_failure_preserves_previous_document_identity_and_side_effects(self):
        execute = _compiled_method("execute_new_plan")
        app = _FakeApp(buffer_fail=True)
        plan = type("Plan", (), {"text": "", "target_path": None, "modified": False})()
        with self.assertRaises(RuntimeError):
            execute(app, plan)
        self.assertFalse(app.loading)
        self.assertEqual(app.current_file, "/tmp/original.txt")
        self.assertEqual(app.document.file_path, "/tmp/original.txt")
        self.assertEqual(app.document.text, "old document")
        self.assertTrue(app.modified)
        self.assertEqual(app.events, [("buffer", "")])

    def test_successful_new_commits_clean_untitled_identity_and_resets_undo(self):
        execute = _compiled_method("execute_new_plan")
        app = _FakeApp()
        plan = type("Plan", (), {"text": "", "target_path": None, "modified": False})()
        self.assertTrue(execute(app, plan))
        self.assertFalse(app.loading)
        self.assertIsNone(app.current_file)
        self.assertIsNone(app.document.file_path)
        self.assertEqual(app.document.text, "")
        self.assertFalse(app.modified)
        self.assertEqual(
            app.events,
            [("buffer", ""), ("document", "", False), ("reset-undo",), ("title",)],
        )

    def test_open_save_recent_favorites_and_template_are_not_batched_into_w49(self):
        for name in (
            "on_open", "open_path", "save_file", "save_as",
            "open_recent_path", "on_add_favourite", "on_new_from_template",
        ):
            method = _method_source(name)
            self.assertNotIn("prepare_new_plan", method)
            self.assertNotIn("execute_new_plan", method)


def _method_source_from_file(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"function {name!r} not found in {path}")


if __name__ == "__main__":
    unittest.main()
