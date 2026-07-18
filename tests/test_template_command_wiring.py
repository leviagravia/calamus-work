import ast
import copy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
TEMPLATES = ROOT / "calamus" / "calamus_templates.py"
WRITING = ROOT / "calamus" / "calamus_writing.py"


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

    def set_text(self, text):
        self.events.append(("buffer", text))
        if self.fail:
            raise RuntimeError("GTK buffer failure")


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


class _FakeApp:
    def __init__(self, *, buffer_fail=False):
        self.events = []
        self.document = _Document(self.events)
        self.current_file = self.document.file_path
        self.modified = self.document.modified
        self.loading = False
        self.text = _TextView(_Buffer(self.events, fail=buffer_fail))

    def reset_undo_history(self):
        self.events.append(("reset-undo",))

    def update_title(self):
        self.events.append(("title",))


class TemplateCommandWiringTests(unittest.TestCase):
    def test_visible_submenu_keeps_existing_location_and_callback(self):
        ui = UI.read_text(encoding="utf-8")
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('app.template_item = Gtk.MenuItem(label="New from Template")', ui)
        self.assertIn("filem.append(app.template_item)", ui)
        self.assertIn("self.on_new_from_template(p)", launcher)

    def test_template_domain_is_extracted_from_writing_module(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        writing = WRITING.read_text(encoding="utf-8")
        templates = TEMPLATES.read_text(encoding="utf-8")
        self.assertIn("from calamus_templates import", launcher)
        self.assertIn("class NewFromTemplatePlan", templates)
        self.assertIn("def list_templates", templates)
        self.assertIn("def read_template", templates)
        self.assertIn("def prepare_new_from_template_plan", templates)
        self.assertNotIn("def list_templates", writing)
        self.assertNotIn("def read_template", writing)
        self.assertNotIn("def ensure_templates_dir", writing)

    def test_template_module_has_no_gtk_or_command_layer_dependency(self):
        source = TEMPLATES.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports))
        self.assertNotIn("CommandLayer", source)

    def test_entrypoint_prompts_then_reads_plans_and_executes(self):
        method = _method_source("on_new_from_template")
        self.assertIn("if not self.may_continue():", method)
        self.assertIn("read_template(path)", method)
        self.assertIn("prepare_new_from_template_plan(path, read_template(path))", method)
        self.assertIn("self.execute_new_from_template_plan(plan)", method)
        self.assertLess(method.index("self.may_continue()"), method.index("read_template(path)"))
        self.assertNotIn("self.current_file =", method)
        self.assertNotIn("self.modified =", method)
        self.assertNotIn("self.set_buffer(", method)

    def test_cancel_stops_before_template_read_or_document_mutation(self):
        events = []
        on_new = _compiled_method(
            "on_new_from_template",
            {
                "read_template": lambda _path: events.append("read"),
                "prepare_new_from_template_plan": lambda *_args: events.append("plan"),
                "OSError": OSError,
                "UnicodeError": UnicodeError,
            },
        )

        class App:
            def may_continue(self):
                events.append("prompt")
                return False

            def execute_new_from_template_plan(self, _plan):
                events.append("execute")

            def error(self, _message):
                events.append("error")

        self.assertFalse(on_new(App(), "/tmp/note.txt"))
        self.assertEqual(events, ["prompt"])

    def test_read_failure_reports_error_and_preserves_old_identity(self):
        events = []

        def fail_read(_path):
            events.append("read")
            raise FileNotFoundError("missing template")

        on_new = _compiled_method(
            "on_new_from_template",
            {
                "read_template": fail_read,
                "prepare_new_from_template_plan": lambda *_args: events.append("plan"),
                "OSError": OSError,
                "UnicodeError": UnicodeError,
            },
        )

        class App:
            current_file = "/tmp/original.txt"
            modified = True

            def may_continue(self):
                events.append("prompt")
                return True

            def execute_new_from_template_plan(self, _plan):
                events.append("execute")

            def error(self, message):
                events.append(("error", message))

        app = App()
        self.assertFalse(on_new(app, "/tmp/missing.txt"))
        self.assertEqual(app.current_file, "/tmp/original.txt")
        self.assertTrue(app.modified)
        self.assertEqual(events, ["prompt", "read", ("error", "missing template")])

    def test_executor_commits_untitled_identity_only_after_buffer_accepts_text(self):
        method = _method_source("execute_new_from_template_plan")
        buffer_at = method.index("self.text.get_buffer().set_text(plan.text)")
        identity_at = method.index("self.document.file_path = plan.target_path")
        reset_at = method.index("self.reset_undo_history()")
        self.assertLess(buffer_at, identity_at)
        self.assertLess(identity_at, reset_at)
        self.assertIn("finally:", method)
        self.assertNotIn("add_recent_file", method)
        self.assertNotIn("save_settings", method)
        self.assertNotIn("save_favourites", method)

    def test_buffer_failure_preserves_previous_document_identity_and_side_effects(self):
        execute = _compiled_method("execute_new_from_template_plan")
        app = _FakeApp(buffer_fail=True)
        plan = type("Plan", (), {"text": "Template", "target_path": None, "modified": True})()
        with self.assertRaises(RuntimeError):
            execute(app, plan)
        self.assertFalse(app.loading)
        self.assertEqual(app.current_file, "/tmp/original.txt")
        self.assertEqual(app.document.file_path, "/tmp/original.txt")
        self.assertEqual(app.document.text, "old document")
        self.assertTrue(app.modified)
        self.assertEqual(app.events, [("buffer", "Template")])

    def test_success_creates_modified_untitled_document_and_resets_undo(self):
        execute = _compiled_method("execute_new_from_template_plan")
        app = _FakeApp()
        plan = type("Plan", (), {"text": "Template", "target_path": None, "modified": True})()
        self.assertTrue(execute(app, plan))
        self.assertFalse(app.loading)
        self.assertIsNone(app.current_file)
        self.assertIsNone(app.document.file_path)
        self.assertEqual(app.document.text, "Template")
        self.assertTrue(app.modified)
        self.assertEqual(
            app.events,
            [("buffer", "Template"), ("document", "Template", True), ("reset-undo",), ("title",)],
        )

    def test_entrypoint_returns_executor_result_after_successful_read_and_plan(self):
        events = []
        plan = object()
        on_new = _compiled_method(
            "on_new_from_template",
            {
                "read_template": lambda path: events.append(("read", path)) or "Body",
                "prepare_new_from_template_plan": lambda path, text: events.append(("plan", path, text)) or plan,
                "OSError": OSError,
                "UnicodeError": UnicodeError,
            },
        )

        class App:
            def may_continue(self):
                events.append("prompt")
                return True

            def execute_new_from_template_plan(self, actual):
                events.append(("execute", actual))
                return True

            def error(self, _message):
                events.append("error")

        self.assertTrue(on_new(App(), "/tmp/note.txt"))
        self.assertEqual(
            events,
            ["prompt", ("read", "/tmp/note.txt"), ("plan", "/tmp/note.txt", "Body"), ("execute", plan)],
        )


if __name__ == "__main__":
    unittest.main()
