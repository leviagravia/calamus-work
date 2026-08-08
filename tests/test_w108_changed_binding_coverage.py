from __future__ import annotations
import csv
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
INV=ROOT/'docs/canonical/CALAMUS_W108_CHANGED_BINDING_INVENTORY.tsv'

class W108ChangedBindingCoverageTests(unittest.TestCase):
    def rows(self):
        rows=list(csv.DictReader(INV.read_text(encoding='utf-8').splitlines(),delimiter='\t'))
        self.assertTrue(rows)
        return rows
    def test_inventory_is_unique_complete_and_has_exact_117_changed_commands(self):
        rows=self.rows(); keys=[(r['kind'],r['binding_id']) for r in rows]
        self.assertEqual(len(keys),len(set(keys)))
        commands={r['binding_id'] for r in rows if r['kind']=='COMMAND'}
        self.assertEqual(len(commands),117)
        for r in rows:
            for field in ('baseline','package','payload','owner','adapter','primary_authority','receipt'):
                self.assertTrue(r[field].strip(),(r['binding_id'],field))
    def test_navigator_changed_binding_has_current_and_historical_exact_receipts(self):
        rows=self.rows(); by={(r['kind'],r['binding_id']):r for r in rows}
        cmd=by[('COMMAND','navigate.navigator-panel')]
        comp=by[('COMPOSITION','NavigatorCompositionInput.on_visibility_changed')]
        self.assertEqual(cmd['primary_authority'],'BEHAVIORAL-GTK')
        self.assertIn('W108_NAVIGATOR_PANEL_TRUE_GTK',cmd['receipt'])
        self.assertEqual(comp['primary_authority'],'BEHAVIORAL-GTK')
        e2e=(ROOT/'tests/test_w108_thin_gtk_shell_app_desktop_e2e.py').read_text(encoding='utf-8')
        self.assertGreaterEqual(e2e.count('window.invoke_command("navigate.navigator-panel"'),2)
        self.assertIn('W108_NAVIGATOR_PANEL_TRUE_GTK=PASS',e2e)
        w101=(ROOT/'tests/test_w101_core_composition_app_desktop_e2e.py').read_text(encoding='utf-8')
        self.assertIn('window.navigator_panel_runtime.set_visible(True)',w101)
    def test_character_map_signal_is_explicitly_classified(self):
        rows=self.rows()
        matched=[r for r in rows if r['kind']=='GTK_SIGNAL' and r['binding_id']=='CharacterMapDialog.character-button.clicked']
        self.assertEqual(len(matched),1)
        self.assertEqual(matched[0]['primary_authority'],'BEHAVIORAL-GTK')

if __name__=='__main__': unittest.main(verbosity=2)
