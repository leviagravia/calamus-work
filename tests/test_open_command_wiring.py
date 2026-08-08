import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest

from calamus_document_session import DocumentSession
from calamus_document_session_controller import DocumentSessionController, DocumentSessionPorts
from calamus_file_lifecycle import OpenPlan
from calamus_model import Document

from tests.w105_menu_test_support import legacy_menu_projection
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


def _compiled_method(name):
    _source, node = _method_node(name)
    module = ast.Module(body=[copy.deepcopy(node)], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = {"LARGE_FILE_BYTES": 1_000_000}
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return scope[name]


class _ApplicationState:
    def __init__(self, events): self.events = events
    def record_last_file(self, path): self.events.append(("application-state", path)); return True


class _App:
    def __init__(self, fail=False):
        self.events = []
        self._research_components = SimpleNamespace(runtime=SimpleNamespace(research_document_context_changed=lambda: None, publish_research_invalidation=lambda *_: None))
        self.document_overview_runtime = SimpleNamespace(refresh_if_open=lambda: False)
        self.application_state = _ApplicationState(self.events)
        self.buffer = "old buffer"
        session = DocumentSession(Document("old document", "/tmp/original.txt", True))
        def replace(text):
            self.events.append(("buffer", text))
            if fail: raise RuntimeError("GTK buffer failure")
            self.buffer = text
        self.document_session = session
        self.document_session_controller = DocumentSessionController(
            session,
            DocumentSessionPorts(
                read_buffer_text=lambda: self.buffer,
                replace_buffer_text=replace,
                reset_undo_history=lambda: self.events.append(("reset-undo",)),
                read_text_file=lambda path: self.events.append(("read", path)) or "loaded",
                write_text_file=lambda _p, _t: None,
                is_large_text_file=lambda path: self.events.append(("large", path)) or False,
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
    def add_recent_file(self, path): self.events.append(("recent", path))
    def update_title(self): self.events.append(("title",))
    def save_settings(self): self.events.append(("application-state",)); return True
    def info(self, *args): self.events.append(("info",)+args)


class OpenCommandWiringTests(unittest.TestCase):
    def test_visible_open_command_and_shortcut_keep_named_entrypoint(self):
        ui = legacy_menu_projection()
        self.assertIn('add_item(filem, "Open…\\tCtrl+O", app.on_open)', ui)
        self.assertIn("command_shortcut_bindings()", ui)

    def test_open_path_delegates_read_and_commit_to_controller(self):
        method = _method_source("open_path")
        self.assertIn("self.document_session_controller.open_path(path)", method)
        self.assertNotIn("read_text_file(path)", method)
        self.assertNotIn("self.document.load", method)

    def test_executor_has_no_mutable_app_session_mirrors(self):
        method = _method_source("execute_open_plan")
        self.assertIn("self.document_session_controller.execute_open(plan)", method)
        for token in ("self.current_file =", "self.modified =", "self.loading ="):
            self.assertNotIn(token, method)

    def test_buffer_failure_preserves_previous_session(self):
        execute = _compiled_method("execute_open_plan")
        app = _App(fail=True)
        before = app.document_session.snapshot()
        with self.assertRaises(RuntimeError):
            execute(app, OpenPlan("/tmp/new.txt", "loaded"), silent=False)
        self.assertEqual(app.document_session.snapshot(), before)
        self.assertFalse(app.loading)
        self.assertEqual(app.events, [("buffer", "loaded")])

    def test_successful_open_commits_then_runs_post_effects(self):
        execute = _compiled_method("execute_open_plan")
        finalize = _compiled_method("finalize_open_transition")
        app = _App()
        app.finalize_open_transition = finalize.__get__(app, _App)
        plan = OpenPlan("/tmp/new.txt", "loaded")
        self.assertTrue(execute(app, plan, silent=False))
        self.assertEqual(app.current_file, "/tmp/new.txt")
        self.assertEqual(app.document.text, "loaded")
        self.assertFalse(app.modified)
        self.assertEqual([e[0] for e in app.events], ["buffer", "reset-undo", "recent", "title", "application-state"])

    def test_open_path_reads_before_post_open_effects(self):
        open_path = _compiled_method("open_path")
        finalize = _compiled_method("finalize_open_transition")
        app = _App()
        app.finalize_open_transition = finalize.__get__(app, _App)
        app.error = lambda msg: app.events.append(("error", msg))
        self.assertTrue(open_path(app, "/tmp/new.txt", silent=False))
        names = [e[0] for e in app.events]
        self.assertLess(names.index("read"), names.index("buffer"))
        self.assertLess(names.index("buffer"), names.index("recent"))


if __name__ == "__main__":
    unittest.main()
