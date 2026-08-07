from tests.w105_menu_test_support import legacy_menu_projection
import ast
import copy
from pathlib import Path
import unittest

from calamus_document_session import DocumentSession
from calamus_document_session_controller import DocumentSessionController, DocumentSessionPorts
from calamus_model import Document
from calamus_file_lifecycle import NewPlan

ROOT=Path(__file__).resolve().parents[1]
LAUNCHER=ROOT/"bin"/"calamus"
UI=ROOT/"calamus"/"calamus_ui.py"
TEMPLATES=ROOT/"calamus"/"calamus_templates.py"


def _method_node(name):
    source=LAUNCHER.read_text(encoding="utf-8"); tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,ast.FunctionDef) and node.name==name:return source,node
    raise AssertionError(name)

def _method_source(name):
    source,node=_method_node(name); return ast.get_source_segment(source,node) or ""

def _compiled_method(name):
    _source,node=_method_node(name); module=ast.Module(body=[copy.deepcopy(node)],type_ignores=[]); ast.fix_missing_locations(module)
    scope={"NewPlan":NewPlan};exec(compile(module,str(LAUNCHER),"exec"),scope);return scope[name]

class _App:
    def __init__(self, fail=False):
        self.events=[];self.buffer="old"
        session=DocumentSession(Document("old","/tmp/original.txt",True))
        def replace(text):
            self.events.append(("buffer",text))
            if fail:raise RuntimeError("GTK buffer failure")
            self.buffer=text
        self.document_session=session
        self.document_session_controller=DocumentSessionController(session,DocumentSessionPorts(
            read_buffer_text=lambda:self.buffer,replace_buffer_text=replace,
            reset_undo_history=lambda:self.events.append(("reset-undo",)),
            read_text_file=lambda _p:"",write_text_file=lambda _p,_t:None,is_large_text_file=lambda _p:False))
    @property
    def current_file(self):return self.document_session.file_path
    @property
    def modified(self):return self.document_session.modified
    @property
    def loading(self):return self.document_session.loading
    def update_title(self):self.events.append(("title",))

class TemplateCommandWiringTests(unittest.TestCase):
    def test_visible_submenu_keeps_existing_location_and_callback(self):
        ui=legacy_menu_projection();launcher=LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('app.template_item = Gtk.MenuItem(label="New from Template")',ui)
        self.assertIn('self.invoke_command("file.template.open", source="dynamic-menu", data={"path": p})',ui)
        self.assertIn('adapter.render_dynamic("templates", template_rows(templates))',launcher)

    def test_template_domain_remains_gtk_free(self):
        source=TEMPLATES.read_text(encoding="utf-8")
        self.assertNotIn("gi.repository",source)
        self.assertIn("class NewFromTemplatePlan",source)

    def test_executor_uses_session_controller_without_mutable_aliases(self):
        method=_method_source("execute_new_from_template_plan")
        self.assertIn("self.document_session_controller.execute_new",method)
        self.assertIn("NewPlan(",method)
        self.assertNotIn("self.document_session.rebind_path",method)
        for token in ("self.current_file =","self.modified =","self.loading ="):
            self.assertNotIn(token,method)

    def test_buffer_failure_preserves_previous_session(self):
        execute=_compiled_method("execute_new_from_template_plan");app=_App(fail=True)
        before=app.document_session.snapshot();plan=type("Plan",(),{"text":"Template","target_path":None,"modified":True})()
        with self.assertRaises(RuntimeError):execute(app,plan)
        self.assertEqual(app.document_session.snapshot(),before)
        self.assertEqual(app.events,[("buffer","Template")])

    def test_success_creates_modified_untitled_document(self):
        execute=_compiled_method("execute_new_from_template_plan");app=_App();plan=type("Plan",(),{"text":"Template","target_path":None,"modified":True})()
        self.assertTrue(execute(app,plan));self.assertIsNone(app.current_file);self.assertTrue(app.modified)
        self.assertEqual(app.document_session.text,"Template")
        self.assertEqual(app.events,[("buffer","Template"),("reset-undo",),("title",)])

if __name__=="__main__":unittest.main()
