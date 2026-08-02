"""Headless contract for historical/current GTK identity separation through W98."""
from __future__ import annotations
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class W98IdentityGateContractTests(unittest.TestCase):
    def test_w95_historical_gate_is_not_bound_to_current_identity(self):
        text=(ROOT/'scripts/w95-true-gtk-app-gate.py').read_text()
        self.assertNotIn('DEVELOPMENT_WORK_ITEM',text); self.assertNotIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION',text); self.assertNotIn('PUBLISHED_BASELINE',text)
        self.assertIn('W95_HISTORICAL_IDENTITY_INDEPENDENT=PASS',text)
    def test_w98_current_identity_gate_is_exact(self):
        text=(ROOT/'tests/test_w98_identity_app_desktop_e2e.py').read_text()
        for token in ("'W98'","'Research Panel Integral Closure'","'f7fd70b4ffc7c756b83b8bfa102d224823244092'",'W98_CURRENT_IDENTITY=PASS'):
            self.assertIn(token,text)
    def test_w98_identity_runs_before_w98_product_gate(self):
        text=(ROOT/'scripts/prove-w98-research-panel-gtk-lanes.sh').read_text()
        self.assertLess(text.index('w98-identity-smoke'),text.index('w98-product-smoke'))
        self.assertIn('W98_CURRENT_IDENTITY_TRUE_APP=PASS',text)
        self.assertIn('W98_RESEARCH_PANEL_INTEGRAL_CLOSURE_GTK_LANES=PASS',text)
    def test_w97_functional_product_gate_remains_historical(self):
        text=(ROOT/'tests/calamus_release_test_profiles.json').read_text()
        self.assertIn('historical-w97-product',text)
        self.assertIn('test_w97_bibliography_app_desktop_e2e',text)
    def test_w95extra_functional_gate_remains_present(self):
        text=(ROOT/'scripts/prove-w95extra-gtk-lanes.sh').read_text()
        self.assertIn('w95-true-gtk-app-gate.py',text); self.assertIn('w95extra-true-gtk-app-gate.py',text); self.assertIn('W95EXTRA_GTK_LANES=PASS',text)
if __name__=='__main__': unittest.main()
