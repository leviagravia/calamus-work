from __future__ import annotations
import unittest
from calamus_research_coordination import (
    BUILTIN_RESEARCH_CLIENT_IDS,
    ResearchClientSpec,
    ResearchInvalidationReason as R,
    ResearchPanelCoordinator,
)

class Scheduler:
    def __init__(self): self.items={}; self.next=1; self.cancelled=[]
    def schedule(self, delay, callback):
        ident=self.next; self.next+=1; self.items[ident]=(delay,callback); return ident
    def cancel(self, ident): self.cancelled.append(ident); self.items.pop(ident,None); return True
    def run_latest(self):
        ident=max(self.items); _,cb=self.items.pop(ident); return cb()

class W98ResearchPanelCoordinatorTests(unittest.TestCase):
    def make(self, active=lambda:'references'):
        self.scheduler=Scheduler(); self.calls={key:[] for key in BUILTIN_RESEARCH_CLIENT_IDS}
        c=ResearchPanelCoordinator(active_client_provider=active,schedule=self.scheduler.schedule,cancel=self.scheduler.cancel)
        for key in BUILTIN_RESEARCH_CLIENT_IDS:
            deps=frozenset(R)
            c.register(ResearchClientSpec(key,key,object(),lambda k=key:self.calls[k].append('activate'),deps,lambda reasons,k=key:self.calls[k].append(('invalidate',reasons)),lambda k=key:self.calls[k].append('shutdown')))
        c.assert_complete(); return c
    def test_active_refreshes_once_and_hidden_refreshes_once_on_activation(self):
        current={'id':'references'}; c=self.make(lambda:current['id'])
        c.publish(R.REFERENCES)
        self.assertEqual(1,len(self.calls['references']))
        self.assertEqual(frozenset({R.REFERENCES}),c.dirty_reasons('tags'))
        current['id']='tags'; c.activate('tags')
        self.assertEqual(['activate'],self.calls['tags'])
        self.assertFalse(c.dirty_reasons('tags'))
    def test_document_content_is_coalesced_and_identity_cancels_pending(self):
        c=self.make(); c.publish(R.DOCUMENT_CONTENT); first=c._content_source
        c.publish(R.DOCUMENT_CONTENT); self.assertIn(first,self.scheduler.cancelled)
        self.scheduler.run_latest(); self.assertFalse(c.pending_content)
        count=c.delivery_count; c.publish(R.DOCUMENT_CONTENT); pending=c._content_source
        c.publish(R.DOCUMENT_IDENTITY); self.assertIn(pending,self.scheduler.cancelled)
        self.assertGreater(c.delivery_count,count)
    def test_shutdown_is_idempotent_and_cancels_pending(self):
        c=self.make(); c.publish(R.DOCUMENT_CONTENT); source=c._content_source
        self.assertTrue(c.shutdown()); self.assertTrue(c.shutdown())
        self.assertIn(source,self.scheduler.cancelled)
        for key in BUILTIN_RESEARCH_CLIENT_IDS:
            self.assertEqual(1,self.calls[key].count('shutdown'))
        c.publish(R.REFERENCES); self.assertTrue(c.is_shutdown)
    def test_rejects_dynamic_or_incomplete_registration(self):
        s=Scheduler(); c=ResearchPanelCoordinator(active_client_provider=lambda:None,schedule=s.schedule,cancel=s.cancel)
        with self.assertRaises(ValueError):
            ResearchClientSpec('plugin','Plugin',object(),lambda:None,frozenset(),lambda _:None,lambda:None)
        with self.assertRaises(RuntimeError): c.assert_complete()
if __name__=='__main__': unittest.main()
