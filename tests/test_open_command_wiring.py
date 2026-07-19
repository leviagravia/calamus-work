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
    namespace = {"LARGE_FILE_BYTES": 1_000_000}
    exec(compile(module, str(LAUNCHER), "exec"), namespace)
    return namespace[name]


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

    def load(self, _path):
        raise AssertionError("W48 visible Open must not call mutating Document.load")


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

    def add_recent_file(self, path):
        self.events.append(("recent", path))

    def update_title(self):
        self.events.append(("title",))

    def save_settings(self):
        self.events.append(("settings",))

    def info(self, title, message):
        self.events.append(("info", title, message))


class OpenCommandWiringTests(unittest.TestCase):
    def test_visible_open_command_and_shortcut_keep_named_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(filem, "Open…\\tCtrl+O", app.on_open)', ui)
        self.assertIn('("<Control>O", app.on_open)', ui)

    def test_on_open_preserves_save_prompt_and_chooser_boundaries(self):
        method = _method_source("on_open")
        self.assertIn("if not self.may_continue():", method)
        self.assertIn("path = choose_open_file(self)", method)
        self.assertIn("self.open_path(path)", method)
        self.assertLess(method.index("self.may_continue()"), method.index("choose_open_file(self)"))

    def test_open_path_reads_before_building_plan_and_never_calls_document_load(self):
        method = _method_source("open_path")
        self.assertIn("prepare_open_plan(", method)
        self.assertIn("read_text_file(path)", method)
        self.assertIn("large_file=is_large_text_file(path)", method)
        self.assertIn("self.execute_open_plan(plan, silent=silent)", method)
        self.assertNotIn("self.document.load(", method)
        self.assertNotIn("self.set_buffer(", method)

    def test_open_plan_module_is_pure_and_has_no_gtk_or_io(self):
        source = LIFECYCLE.read_text(encoding="utf-8")
        self.assertIn("class OpenPlan", source)
        self.assertIn("def prepare_open_plan(", source)
        self.assertNotIn("choose_open_file", source)
        self.assertNotIn("read_text_file", source)
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports))
        self.assertNotIn("CommandLayer", source)
        self.assertNotIn("open(", source)

    def test_executor_commits_document_identity_only_after_buffer_accepts_text(self):
        method = _method_source("execute_open_plan")
        buffer_at = method.index("self.text.get_buffer().set_text(plan.text)")
        identity_at = method.index("self.document.file_path = plan.target_path")
        recent_at = method.index("self.add_recent_file(self.current_file)")
        self.assertLess(buffer_at, identity_at)
        self.assertLess(identity_at, recent_at)
        self.assertIn("finally:", method)
        self.assertIn("self.loading = False", method)

    def test_buffer_failure_preserves_previous_document_identity_and_side_effects(self):
        execute = _compiled_method("execute_open_plan")
        app = _FakeApp(buffer_fail=True)
        plan = type("Plan", (), {
            "target_path": "/tmp/new.txt",
            "text": "new text",
            "large_file": False,
        })()
        with self.assertRaises(RuntimeError):
            execute(app, plan, silent=False)
        self.assertFalse(app.loading)
        self.assertEqual(app.current_file, "/tmp/original.txt")
        self.assertEqual(app.document.file_path, "/tmp/original.txt")
        self.assertEqual(app.document.text, "old document")
        self.assertTrue(app.modified)
        self.assertEqual(app.events, [("buffer", "new text")])

    def test_successful_open_commits_identity_then_post_open_state(self):
        execute = _compiled_method("execute_open_plan")
        app = _FakeApp()
        plan = type("Plan", (), {
            "target_path": "/tmp/new.txt",
            "text": "new text",
            "large_file": False,
        })()
        self.assertTrue(execute(app, plan, silent=False))
        self.assertFalse(app.loading)
        self.assertEqual(app.current_file, "/tmp/new.txt")
        self.assertEqual(app.document.file_path, "/tmp/new.txt")
        self.assertEqual(app.document.text, "new text")
        self.assertFalse(app.modified)
        self.assertEqual(
            [event[0] for event in app.events],
            ["buffer", "document", "reset-undo", "recent", "title", "settings"],
        )

    def test_large_file_notification_respects_silent_boundary(self):
        execute = _compiled_method("execute_open_plan")
        plan = type("Plan", (), {
            "target_path": "/tmp/large.txt",
            "text": "new text",
            "large_file": True,
        })()
        visible = _FakeApp()
        self.assertTrue(execute(visible, plan, silent=False))
        self.assertIn("info", [event[0] for event in visible.events])
        silent = _FakeApp()
        self.assertTrue(execute(silent, plan, silent=True))
        self.assertNotIn("info", [event[0] for event in silent.events])

    def test_recent_caller_remains_on_existing_open_path_gateway(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertNotIn("def on_restore_session", launcher)
        recent = _method_source("open_recent_path")
        self.assertIn("self.open_path(path)", recent)
        self.assertNotIn("prepare_open_plan", recent)

    def test_save_new_recent_and_favorites_are_not_batched_into_w48(self):
        for name in ("save_file", "save_as", "on_new", "open_recent_path", "on_add_favourite"):
            method = _method_source(name)
            self.assertNotIn("prepare_open_plan", method)
            self.assertNotIn("execute_open_plan", method)


if __name__ == "__main__":
    unittest.main()
