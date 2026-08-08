import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest

from calamus_document_session import DocumentSession
from calamus_document_session_controller import DocumentSessionController, DocumentSessionPorts
from calamus_file_lifecycle import SavePlan
from calamus_model import Document

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"


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
    scope = {"OSError": OSError, "ValueError": ValueError}
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return scope[name]


class _ApplicationState:
    def __init__(self, events): self.events = events
    def record_last_file(self, path): self.events.append(("application-state", path)); return True


class _App:
    def __init__(self, fail=False):
        self.events=[]; self._research_components=SimpleNamespace(runtime=SimpleNamespace(research_document_context_changed=lambda:None, publish_research_invalidation=lambda *_:None)); self.document_overview_runtime=SimpleNamespace(refresh_if_open=lambda:False); self.application_state=_ApplicationState(self.events); self.buffer="Body"
        session=DocumentSession(Document("Body", "/tmp/original.txt", True))
        def write(path,text):
            self.events.append(("write",path,text))
            if fail: raise OSError("write failed")
        self.document_session=session
        self.document_session_controller=DocumentSessionController(session, DocumentSessionPorts(
            read_buffer_text=lambda:self.buffer,
            replace_buffer_text=lambda text: self.events.append(("buffer",text)),
            reset_undo_history=lambda:None,
            read_text_file=lambda _p:"",
            write_text_file=write,
            is_large_text_file=lambda _p:False,
        ))
    @property
    def current_file(self): return self.document_session.file_path
    @property
    def modified(self): return self.document_session.modified
    @property
    def document(self): return self.document_session.document
    def add_recent_file(self,path): self.events.append(("recent",path))
    def update_title(self): self.events.append(("title",))
    def save_settings(self): self.events.append(("application-state",)); return True
    def error(self,msg): self.events.append(("error",msg))


class SaveAsCommandWiringTests(unittest.TestCase):
    def test_regular_save_and_save_as_share_executor(self):
        self.assertIn("return self.execute_save_plan(plan)", _method_source("save_file"))
        self.assertIn("return self.execute_save_plan(plan)", _method_source("save_as"))

    def test_executor_delegates_physical_write_and_identity_commit(self):
        source=_method_source("execute_save_plan")
        self.assertIn("self.document_session_controller.execute_save(plan)",source)
        for token in ("self.current_file =","self.modified =","self.loading =","self.document.save"):
            self.assertNotIn(token,source)

    def test_failed_save_preserves_identity_and_dirty_state(self):
        execute=_compiled_method("execute_save_plan")
        app=_App(fail=True)
        plan=SavePlan(False,"/tmp/new.txt","Body","Body")
        self.assertFalse(execute(app,plan))
        self.assertEqual(app.current_file,"/tmp/original.txt")
        self.assertTrue(app.modified)
        self.assertEqual([e[0] for e in app.events],["write","error"])

    def test_successful_save_commits_then_runs_post_effects(self):
        execute=_compiled_method("execute_save_plan")
        app=_App()
        plan=SavePlan(False,"/tmp/new.txt","Body","Body")
        self.assertTrue(execute(app,plan))
        self.assertEqual(app.current_file,"/tmp/new.txt")
        self.assertFalse(app.modified)
        self.assertEqual([e[0] for e in app.events],["write","recent","title","application-state"])

    def test_save_as_cancel_is_mutation_free(self):
        self.assertIn("if plan is None:", _method_source("save_as"))
        self.assertIn("return False", _method_source("save_as"))


if __name__ == "__main__":
    unittest.main()
