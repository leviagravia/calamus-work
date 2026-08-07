import ast
import copy
from pathlib import Path
import unittest

from calamus_document_session import DocumentSession
from calamus_document_session_controller import DocumentSessionController, DocumentSessionPorts
from calamus_file_lifecycle import NewPlan
from calamus_model import Document

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"


def _method_node(name):
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return source, node
    raise AssertionError(name)


def _method_source(name):
    source, node = _method_node(name)
    return ast.get_source_segment(source, node) or ""


def _compiled_method(name, namespace=None):
    _source, node = _method_node(name)
    module = ast.Module(body=[copy.deepcopy(node)], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = dict(namespace or {})
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return scope[name]


class _App:
    def __init__(self, fail=False):
        self.events = []
        self.buffer = "old buffer"
        session = DocumentSession(Document("old document", "/tmp/original.txt", True))
        def replace(text):
            self.events.append(("buffer", text))
            if fail:
                raise RuntimeError("GTK buffer failure")
            self.buffer = text
        self.document_session = session
        self.document_session_controller = DocumentSessionController(
            session,
            DocumentSessionPorts(
                read_buffer_text=lambda: self.buffer,
                replace_buffer_text=replace,
                reset_undo_history=lambda: self.events.append(("reset-undo",)),
                read_text_file=lambda _p: "",
                write_text_file=lambda _p, _t: None,
                is_large_text_file=lambda _p: False,
            ),
        )
    @property
    def current_file(self): return self.document_session.file_path
    @property
    def modified(self): return self.document_session.modified
    @property
    def loading(self): return self.document_session.loading
    @property
    def document(self): return self.document_session.document
    def update_title(self): self.events.append(("title",))


class NewCommandWiringTests(unittest.TestCase):
    def test_visible_new_command_and_shortcut_keep_named_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(filem, "New\\tCtrl+N", app.on_new)', ui)
        self.assertIn('("<Control>N", app.on_new)', ui)

    def test_on_new_preserves_prompt_then_delegates(self):
        method = _method_source("on_new")
        self.assertLess(method.index("self.may_continue()"), method.index("prepare_new_plan()"))
        self.assertIn("self.execute_new_plan(prepare_new_plan())", method)

    def test_cancelled_new_stops_before_plan(self):
        events = []
        on_new = _compiled_method("on_new", {"prepare_new_plan": lambda: events.append("plan")})
        class App:
            def may_continue(self): events.append("prompt"); return False
            def execute_new_plan(self, _plan): events.append("execute")
        self.assertIsNone(on_new(App()))
        self.assertEqual(events, ["prompt"])

    def test_executor_delegates_to_authoritative_session_controller(self):
        method = _method_source("execute_new_plan")
        self.assertIn("self.document_session_controller.execute_new(plan)", method)
        self.assertNotIn("self.current_file =", method)
        self.assertNotIn("self.modified =", method)
        self.assertNotIn("self.loading =", method)

    def test_buffer_failure_preserves_previous_session(self):
        execute = _compiled_method("execute_new_plan")
        app = _App(fail=True)
        before = app.document_session.snapshot()
        with self.assertRaises(RuntimeError):
            execute(app, NewPlan())
        self.assertEqual(app.document_session.snapshot(), before)
        self.assertFalse(app.loading)
        self.assertEqual(app.events, [("buffer", "")])

    def test_successful_new_commits_clean_untitled_and_resets_undo(self):
        execute = _compiled_method("execute_new_plan")
        app = _App()
        self.assertTrue(execute(app, NewPlan()))
        self.assertIsNone(app.current_file)
        self.assertEqual(app.document.text, "")
        self.assertFalse(app.modified)
        self.assertEqual(app.events, [("buffer", ""), ("reset-undo",), ("title",)])


if __name__ == "__main__":
    unittest.main()
