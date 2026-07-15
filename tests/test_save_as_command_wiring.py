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


def _compiled_method(name: str):
    _source, node = _method_node(name)
    isolated = copy.deepcopy(node)
    module = ast.Module(body=[isolated], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, str(LAUNCHER), "exec"), namespace)
    return namespace[name]


class _Buffer:
    def __init__(self):
        self.text = None

    def set_text(self, text):
        self.text = text


class _TextView:
    def __init__(self):
        self.buffer = _Buffer()

    def get_buffer(self):
        return self.buffer


class _Document:
    def __init__(self, *, file_path="/tmp/original.txt", fail=False):
        self.file_path = file_path
        self.modified = True
        self.fail = fail

    def save(self, path, text):
        if self.fail:
            raise OSError("write failed")
        self.file_path = path
        self.modified = False


class _FakeApp:
    def __init__(self, *, fail=False):
        self.loading = False
        self.text = _TextView()
        self.document = _Document(fail=fail)
        self.current_file = "/tmp/original.txt"
        self.modified = True
        self.events = []

    def add_recent_file(self, path):
        self.events.append(("recent", path))

    def update_title(self):
        self.events.append(("title", None))

    def save_settings(self):
        self.events.append(("settings", None))

    def error(self, message):
        self.events.append(("error", message))


class SaveAsCommandWiringTests(unittest.TestCase):
    def test_visible_save_as_command_keeps_named_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(r'add_item(filem, "Save As…\tCtrl+Shift+S", app.on_save_as)', ui)

    def test_on_save_as_delegates_to_save_as(self):
        method = _method_source("on_save_as")
        self.assertIn("self.save_as()", method)

    def test_save_as_uses_pure_destination_plan_and_shared_executor(self):
        method = _method_source("save_as")
        self.assertIn("prepare_save_as_plan(", method)
        self.assertIn("choose_save_file(self)", method)
        self.assertIn("if plan is None:", method)
        self.assertIn("return self.execute_save_plan(plan)", method)

    def test_save_as_does_not_precommit_application_or_document_identity(self):
        _source, node = _method_node("save_as")
        forbidden = []
        for child in ast.walk(node):
            if isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                for target in targets:
                    text = ast.unparse(target)
                    if text in {"self.current_file", "self.document.file_path"}:
                        forbidden.append(text)
        self.assertEqual(forbidden, [])

    def test_shared_executor_commits_identity_only_after_document_save(self):
        source = _method_source("execute_save_plan")
        write_at = source.index("self.document.save(plan.target_path, plan.text_to_write)")
        app_identity_at = source.index("self.current_file = self.document.file_path")
        self.assertLess(write_at, app_identity_at)

    def test_failed_save_as_write_preserves_previous_identity_and_side_effects(self):
        execute = _compiled_method("execute_save_plan")
        app = _FakeApp(fail=True)
        plan = type("Plan", (), {
            "replaces_buffer_text": False,
            "text_to_write": "Body",
            "target_path": "/tmp/new-name.txt",
        })()
        self.assertFalse(execute(app, plan))
        self.assertEqual(app.current_file, "/tmp/original.txt")
        self.assertEqual(app.document.file_path, "/tmp/original.txt")
        self.assertTrue(app.modified)
        self.assertEqual([event[0] for event in app.events], ["error"])

    def test_successful_save_as_write_commits_identity_and_post_save_state(self):
        execute = _compiled_method("execute_save_plan")
        app = _FakeApp(fail=False)
        plan = type("Plan", (), {
            "replaces_buffer_text": False,
            "text_to_write": "Body",
            "target_path": "/tmp/new-name.txt",
        })()
        self.assertTrue(execute(app, plan))
        self.assertEqual(app.current_file, "/tmp/new-name.txt")
        self.assertEqual(app.document.file_path, "/tmp/new-name.txt")
        self.assertFalse(app.modified)
        self.assertEqual(
            [event[0] for event in app.events],
            ["recent", "title", "settings"],
        )

    def test_regular_save_and_save_as_share_one_execution_boundary(self):
        self.assertIn("return self.execute_save_plan(plan)", _method_source("save_file"))
        self.assertIn("return self.execute_save_plan(plan)", _method_source("save_as"))

    def test_save_as_plan_remains_pure_and_outside_command_layer(self):
        lifecycle = LIFECYCLE.read_text(encoding="utf-8")
        self.assertIn("def prepare_save_as_plan(", lifecycle)
        self.assertNotIn("CommandLayer", lifecycle)
        self.assertNotIn("CommandContext", lifecycle)
        self.assertNotIn("choose_save_file", lifecycle)
        self.assertNotIn("write_text_file", lifecycle)
        self.assertNotIn("open(", lifecycle)

    def test_other_phase1_commands_are_not_rewired_by_w47(self):
        for name in ("on_open", "on_new", "open_path", "on_quit"):
            method = _method_source(name)
            self.assertNotIn("prepare_save_as_plan", method)
            self.assertNotIn("execute_save_plan", method)


if __name__ == "__main__":
    unittest.main()
