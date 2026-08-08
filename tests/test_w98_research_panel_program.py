from __future__ import annotations
from pathlib import Path
import unittest
from calamus_commands import RESEARCH_COMMANDS
from calamus_research_coordination import BUILTIN_RESEARCH_CLIENT_IDS, ResearchInvalidationReason
ROOT=Path(__file__).resolve().parents[1]
class W98ResearchPanelProgramTests(unittest.TestCase):
    def test_contract_freezes_core_only_coordinator_and_seven_clients(self):
        text=(ROOT/'docs/canonical/CALAMUS_W98_RESEARCH_PANEL_INTEGRAL_CLOSURE_CONTRACT.md').read_text()
        for token in ('seven existing built-in Research clients','150 ms','hidden dependent projections become dirty','All Full variants remain frozen','No Full feature'):
            self.assertIn(token,text)
        self.assertEqual(7,len(BUILTIN_RESEARCH_CLIENT_IDS)); self.assertEqual(7,len(ResearchInvalidationReason))
    def test_command_catalog_is_complete_and_uses_bibliography_taxonomy(self):
        self.assertEqual(26,len(RESEARCH_COMMANDS)); self.assertEqual(26,len({x.command_id for x in RESEARCH_COMMANDS}))
        labels={x.label for x in RESEARCH_COMMANDS}; self.assertIn('Bibliography',labels); self.assertNotIn('References',labels)
        from calamus_shortcuts import SHORTCUTS; labels={(x.command, x.shortcut) for x in SHORTCUTS}; self.assertIn(('Bibliography','menu'), labels); self.assertNotIn(('References','menu'), labels)
    def test_coordinator_is_gtk_free_and_app_uses_one_context_gateway(self):
        coord=(ROOT/'calamus/calamus_research_coordination.py').read_text(); app=(ROOT/'bin/calamus').read_text(); composition=(ROOT/'calamus/calamus_research_composition.py').read_text(); runtime=(ROOT/'calamus/calamus_research_application.py').read_text(); workspace=(ROOT/'calamus/calamus_workspace_host_runtime.py').read_text()
        lifecycle=(ROOT/'calamus/calamus_application_lifecycle_app.py').read_text()
        self.assertNotIn('import gi',coord); self.assertNotIn('gi.repository',coord)
        for token in ('ResearchPanelCoordinator(','ResearchClientSpec('):
            self.assertIn(token,composition)
        self.assertIn('research_document_context_changed', runtime)
        self.assertIn('register_final("research-coordinator", research_coordinator_shutdown)', lifecycle)
        self.assertIn('research_coordinator_shutdown=self.research_coordinator.shutdown', app)
        for name in ('execute_new_plan','finalize_open_transition','execute_new_from_template_plan'):
            start=app.index('    def '+name); end=app.find('\n    def ',start+5); body=app[start:end if end!=-1 else None]
            self.assertIn('research_document_context_changed', body)
            self.assertIn('self._research_components.runtime.research_document_context_changed()', body)
            self.assertNotIn('getattr(self, "research_document_context_changed"', body)
            self.assertNotIn('sync_source_notes_document(',body)
        for name in ('reconcile_workspace_rename','reconcile_workspace_trash'):
            start=workspace.index('    def '+name); end=workspace.find('\n    def ',start+5); body=workspace[start:end if end!=-1 else None]
            self.assertIn('self._ports.research_context_changed()', body)
            self.assertNotIn('sync_source_notes_document(', body)
    def test_program_removes_old_full_before_w98_gate(self):
        text=(ROOT/'docs/canonical/CALAMUS_W97_BIBLIOGRAPHY_MANAGER_CORE_FULL_PROGRAM.md').read_text()
        self.assertIn('No Full variant blocks W98',text); self.assertNotIn('W98 Research Panel Integral Closure is prohibited',text)
    def test_forbidden_infrastructure_absent(self):
        text=(ROOT/'calamus/calamus_research_coordination.py').read_text().casefold()
        for token in ('sqlite','watchdog','threading','plugin discovery','service locator'):
            self.assertNotIn(token,text)
if __name__=='__main__': unittest.main()
