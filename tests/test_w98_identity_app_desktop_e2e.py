from __future__ import annotations
import importlib.machinery, importlib.util, os, sys, tempfile, unittest, uuid
from pathlib import Path
from unittest.mock import patch
from calamus_version import DEVELOPMENT_BUILD_LABEL, DEVELOPMENT_WORK_ITEM, DEVELOPMENT_WORK_ITEM_DESCRIPTION, PUBLISHED_BASELINE
from tests.calamus_gtk_test_driver import HAVE_GTK, Gtk, ModalDriver, close_visible_dialogs, display_ready, named_widget, pump, visible_dialog
ROOT=Path(__file__).resolve().parents[1]
RUN=os.environ.get('CALAMUS_W98_RUN_REAL_GTK')=='1'
EXPECTED=('Development build','W98','Research Panel Integral Closure','f7fd70b4ffc7c756b83b8bfa102d224823244092')
def load_app():
 os.environ['CALAMUS_LIB_DIR']=str(ROOT/'calamus'); os.environ['CALAMUS_SOURCE_ROOT']=str(ROOT); sys.path.insert(0,str(ROOT/'calamus'))
 name='w98id_'+uuid.uuid4().hex; loader=importlib.machinery.SourceFileLoader(name,str(ROOT/'bin/calamus')); spec=importlib.util.spec_from_loader(name,loader); mod=importlib.util.module_from_spec(spec); loader.exec_module(mod); return mod
def txt(v):
 b=v.get_buffer(); s,e=b.get_bounds(); return b.get_text(s,e,True)
@unittest.skipUnless(RUN and HAVE_GTK and display_ready(),'real W98 GTK lane')
class W98IdentityRealAppE2E(unittest.TestCase):
 def test_exact_current_identity_and_stable_about(self):
  self.assertEqual(EXPECTED,(DEVELOPMENT_BUILD_LABEL,DEVELOPMENT_WORK_ITEM,DEVELOPMENT_WORK_ITEM_DESCRIPTION,PUBLISHED_BASELINE))
  with tempfile.TemporaryDirectory() as td, patch.dict(os.environ,{'HOME':td,'XDG_CONFIG_HOME':td+'/config','XDG_DATA_HOME':td+'/data'},clear=False):
   win=load_app().App(); win.show_all(); pump()
   try:
    def about():
     d=visible_dialog('About Calamus');
     if d is None:return False
     body=txt(named_widget(d,'calamus-about-text',Gtk.TextView)); self.assertEqual('Calamus',body.splitlines()[0]); self.assertNotIn(EXPECTED[2],body); d.response(Gtk.ResponseType.CLOSE); return True
    dr=ModalDriver([about]); dr.start(); win.on_about(); pump(); dr.assert_complete()
    def info():
     d=visible_dialog('System Info');
     if d is None:return False
     body=txt(named_widget(d,'calamus-system-info-text',Gtk.TextView));
     for line in (f'Calamus: {EXPECTED[0]}',f'Work item: {EXPECTED[1]}',f'Work item description: {EXPECTED[2]}',f'Published baseline: {EXPECTED[3]}'): self.assertIn(line,body)
     d.response(Gtk.ResponseType.CLOSE); return True
    dr=ModalDriver([info]); dr.start(); win.on_system_info(); pump(); dr.assert_complete(); print('W98_CURRENT_IDENTITY=PASS')
   finally: close_visible_dialogs(); win.destroy(); pump()
if __name__=='__main__': unittest.main(verbosity=2)
