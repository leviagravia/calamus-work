"""True-App W98 proof for document context, coalescing and Research shutdown."""
from __future__ import annotations
import importlib.machinery, importlib.util, os, sys, tempfile, time, unittest, uuid
from pathlib import Path
from unittest.mock import patch
from calamus_reference_store import MarkdownReferenceStore, default_references_path
from calamus_reference_set_store import MarkdownReferenceSetStore, default_reference_sets_path
from calamus_references import ReferenceRecord
from calamus_reference_sets import ReferenceSet
from calamus_research_file import FileToken
from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
from calamus_source_notes import SourceNote
from calamus_scratchpad_store import MarkdownScratchpadStore, scratchpad_path
from calamus_scratchpad import ScratchpadEntry
from tests.calamus_gtk_test_driver import HAVE_GTK, Gtk, display_ready, pump
ROOT=Path(__file__).resolve().parents[1]
RUN=os.environ.get('CALAMUS_W98_RUN_REAL_GTK')=='1'
def load_app():
 os.environ['CALAMUS_LIB_DIR']=str(ROOT/'calamus'); os.environ['CALAMUS_SOURCE_ROOT']=str(ROOT)
 if str(ROOT/'calamus') not in sys.path: sys.path.insert(0,str(ROOT/'calamus'))
 name='w98app_'+uuid.uuid4().hex; loader=importlib.machinery.SourceFileLoader(name,str(ROOT/'bin/calamus')); spec=importlib.util.spec_from_loader(name,loader); mod=importlib.util.module_from_spec(spec); loader.exec_module(mod); return mod
def config(root):
 import calamus_config
 p=root/'config'/'calamus'; calamus_config.CONFIG_DIR=str(p); calamus_config.SETTINGS_FILE=str(p/'settings.json'); calamus_config.RECENT_FILE=str(p/'recent.json'); calamus_config.FAVOURITES_FILE=str(p/'favourites.json')
def save(store,items):
 r=store.save(tuple(items),FileToken(False)); assert r.saved,r.message
def fixture(root):
 a=root/'A.md'; b=root/'B.md'; a.write_text('# A {#a}\nA [@alpha].\n'); b.write_text('# B {#b}\nB [@beta].\n')
 save(MarkdownReferenceStore(default_references_path()),(ReferenceRecord(key='alpha',title='Alpha',tags=('global',)),ReferenceRecord(key='beta',title='Beta',tags=('global',))))
 save(MarkdownReferenceSetStore(default_reference_sets_path()),(ReferenceSet('Set A',members=('alpha',)),))
 save(MarkdownSourceNoteStore(source_notes_path(str(a))),(SourceNote(id='sn-a',kind='comment',text='A',reference_key='alpha',tags=('doc-a',),target='#a'),))
 save(MarkdownSourceNoteStore(source_notes_path(str(b))),(SourceNote(id='sn-b',kind='comment',text='B',reference_key='beta',tags=('doc-b',),target='#b'),))
 save(MarkdownScratchpadStore(scratchpad_path(str(a))),(ScratchpadEntry(id='sp-a',type='idea',title='A',body='A',tags=('scratch-a',),sections=('#a',)),))
 save(MarkdownScratchpadStore(scratchpad_path(str(b))),(ScratchpadEntry(id='sp-b',type='idea',title='B',body='B',tags=('scratch-b',),sections=('#b',)),))
 return a,b
def env(root): return {'HOME':str(root),'XDG_DATA_HOME':str(root/'data'),'XDG_CONFIG_HOME':str(root/'config'),'XDG_CACHE_HOME':str(root/'cache')}
def wait(predicate,timeout=2.0):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  pump()
  if predicate(): return True
  time.sleep(.01)
 pump(); return bool(predicate())
@unittest.skipUnless(RUN and HAVE_GTK and display_ready(),'real W98 GTK lane')
class W98ResearchPanelAppDesktopE2E(unittest.TestCase):
 def test_document_switch_edit_hidden_dirty_and_normal_close(self):
  with tempfile.TemporaryDirectory(prefix='w98-app-') as td:
   root=Path(td)
   with patch.dict(os.environ,env(root),clear=False):
    config(root); a,b=fixture(root); win=load_app().App(); win.show_all(); pump()
    try:
     self.assertTrue(win.open_path(str(a)))
     checks=(
      ('source-notes',lambda:tuple(win.source_note_panel_runtime.controller.ids),('sn-b',)),
      ('scratchpad',lambda:tuple(win.scratchpad_runtime.controller.ids),('sp-b',)),
      ('references',lambda:tuple(sorted(win.reference_panel_runtime.controller.context.cited_keys)),('beta',)),
      ('authoring-bridge',lambda:win.authoring_bridge_runtime.controller.projection.document_text,None),
      ('tags',lambda:tuple(sorted(i.identity for i in win.tags_runtime.controller.inventory.items)),None),
     )
     for client,observe,expected in checks:
      self.assertTrue(win.open_path(str(a))); self.assertTrue(win.research_panel_runtime.show(client)); pump(); self.assertTrue(win.open_path(str(b))); pump()
      value=observe()
      if client=='authoring-bridge': self.assertIn('[@beta]',value)
      elif client=='tags': self.assertIn('doc-b',value); self.assertNotIn('doc-a',value)
      else: self.assertEqual(expected,value)
     self.assertTrue(win.open_path(str(a))); self.assertTrue(win.research_panel_runtime.show('references')); pump()
     before=win.research_coordinator.delivery_count
     win.text.get_buffer().set_text('# A {#a}\nChanged [@beta].\n')
     self.assertTrue(wait(lambda: tuple(sorted(win.reference_panel_runtime.controller.context.cited_keys))==('beta',)))
     self.assertEqual(before+1,win.research_coordinator.delivery_count)
     self.assertTrue(win.research_panel_runtime.show('authoring-bridge')); pump()
     win.text.get_buffer().set_text('# A2 {#a2}\nAgain [@alpha].\n')
     self.assertTrue(wait(lambda:'[@alpha]' in win.authoring_bridge_runtime.controller.projection.document_text))
     self.assertTrue(win.research_panel_runtime.show('references')); pump(); win._research_components.runtime.publish_research_invalidation(__import__('calamus_research_coordination').ResearchInvalidationReason.SOURCE_NOTES)
     self.assertTrue(win.research_coordinator.dirty_reasons('tags'))
     self.assertTrue(win.research_panel_runtime.show('tags')); pump(); self.assertFalse(win.research_coordinator.dirty_reasons('tags'))
     for client in ('clip-collection','scratchpad','references','tags','reference-sets','source-notes','authoring-bridge'):
      self.assertTrue(win.research_panel_runtime.show(client)); pump()
     win.research_panel_runtime.show('references'); win.reference_panel_runtime._view.search.set_text('alp'); win.research_panel_runtime.show('tags'); pump()
     win.document_session.mark_clean(); self.assertTrue(win.request_application_close()); pump(); self.assertTrue(win.research_coordinator.is_shutdown); self.assertFalse(win.research_coordinator.pending_content)
     self.assertIsNone(win.reference_panel_runtime._view._search_dispatcher); self.assertFalse(getattr(win.tags_runtime._view,'_selection_source_id',0)); win=None
     print('W98_REAL_DOCUMENT_SWITCH_ALL_CLIENTS=PASS'); print('W98_REAL_DOCUMENT_CONTENT_COALESCING=PASS'); print('W98_REAL_HIDDEN_DIRTY_ACTIVATION=PASS'); print('W98_REAL_RESEARCH_NORMAL_CLOSE=PASS')
    finally:
     if win is not None:
      win.document_session.mark_clean(); win.destroy(); pump()
if __name__=='__main__': unittest.main(verbosity=2)
