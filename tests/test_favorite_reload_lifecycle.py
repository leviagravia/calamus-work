import ast
import copy
from pathlib import Path
import unittest

from calamus_menu_model import DynamicMenuRow, favourite_rows

ROOT=Path(__file__).resolve().parents[1]
LAUNCHER=ROOT/'bin/calamus'


def _method(name):
    source=LAUNCHER.read_text(encoding='utf-8'); tree=ast.parse(source)
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
    module=ast.Module(body=[copy.deepcopy(node)],type_ignores=[]); ast.fix_missing_locations(module)
    scope={'favourite_rows':favourite_rows}; exec(compile(module,str(LAUNCHER),'exec'),scope); return scope[name]

POPULATE=_method('populate_favourites_menu')
RELOAD=_method('on_reload_favourites')

class _Adapter:
    def __init__(self): self.calls=[]
    def render_dynamic(self,slot,rows): self.calls.append((slot,tuple(rows))); return tuple(rows)

class _App:
    def __init__(self, snapshots, adapter=True):
        self._snapshots=[list(x) for x in snapshots]; self.menu_ui_adapter=_Adapter() if adapter else None
    def load_favourites(self):
        if not self._snapshots: raise AssertionError('extra load')
        return self._snapshots.pop(0)
    def populate_favourites_menu(self): return POPULATE(self)
    def save_favourites(self,_): raise AssertionError('reload must not persist')

class FavoriteReloadLifecycleTests(unittest.TestCase):
    def test_empty_projection_is_one_disabled_placeholder(self):
        rows=favourite_rows(())
        self.assertEqual(rows,(DynamicMenuRow('No favourites',enabled=False),))

    def test_projection_uses_stable_command_payload_and_tooltip(self):
        rows=favourite_rows(('/tmp/a.txt','/tmp/b.txt'))
        self.assertEqual([r.label for r in rows],['a.txt','b.txt'])
        self.assertEqual([r.command_id for r in rows],['file.favourite.open','file.favourite.open'])
        self.assertEqual(rows[0].data(),{'path':'/tmp/a.txt'})
        self.assertEqual(rows[0].tooltip,'/tmp/a.txt')

    def test_population_delegates_one_complete_snapshot_to_owned_adapter_slot(self):
        app=_App([['/tmp/a.txt','/tmp/b.txt']])
        result=POPULATE(app)
        self.assertEqual(result,('/tmp/a.txt','/tmp/b.txt'))
        self.assertEqual(len(app.menu_ui_adapter.calls),1)
        slot,rows=app.menu_ui_adapter.calls[0]
        self.assertEqual(slot,'favourites')
        self.assertEqual([r.label for r in rows],['a.txt','b.txt'])

    def test_repeated_population_replaces_by_slot_without_app_owned_widget_list(self):
        app=_App([['/tmp/a.txt'],['/tmp/b.txt']])
        POPULATE(app); POPULATE(app)
        self.assertEqual(len(app.menu_ui_adapter.calls),2)
        self.assertEqual([r.label for r in app.menu_ui_adapter.calls[-1][1]],['b.txt'])
        source=LAUNCHER.read_text(encoding='utf-8')
        self.assertNotIn('_favourite_dynamic_items',source)

    def test_population_without_adapter_still_returns_current_data(self):
        app=_App([['/tmp/a.txt']],adapter=False)
        self.assertEqual(POPULATE(app),('/tmp/a.txt',))

    def test_visible_reload_delegates_once_and_returns_true(self):
        class App:
            def __init__(self): self.calls=0
            def populate_favourites_menu(self): self.calls+=1
        app=App(); self.assertTrue(RELOAD(app)); self.assertEqual(app.calls,1)

    def test_reload_does_not_touch_document_undo_or_persistence(self):
        source=ast.get_source_segment(LAUNCHER.read_text(encoding='utf-8'), next(n for n in ast.walk(ast.parse(LAUNCHER.read_text(encoding='utf-8'))) if isinstance(n,ast.FunctionDef) and n.name=='on_reload_favourites'))
        for token in ('save_favourites','current_file','history','document_session','Gtk.'):
            self.assertNotIn(token,source)

if __name__=='__main__': unittest.main()
