from __future__ import annotations
import ast
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'prove-w108-callback-shape-closure.py'

class W108CallbackShapeClosureTests(unittest.TestCase):
    def test_machine_callback_shape_closure_passes(self):
        cp=subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(cp.returncode,0, cp.stdout+cp.stderr)
        self.assertIn('W108_CALLBACK_SHAPE_CLOSURE=PASS',cp.stdout)
        self.assertIn('mismatches=0',cp.stdout)

    def test_navigator_payload_adapter_is_explicit_and_shape_compatible(self):
        components=(ROOT/'calamus/calamus_application_components.py').read_text(encoding='utf-8')
        composition=(ROOT/'calamus/calamus_application_composition.py').read_text(encoding='utf-8')
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        self.assertIn('on_navigator_visibility_changed: Callable[[bool], Any]', components)
        self.assertIn('on_visibility_changed=inputs.on_navigator_visibility_changed', composition)
        self.assertNotIn('on_visibility_changed=inputs.refresh_ui_state', composition)
        self.assertIn('on_navigator_visibility_changed=lambda _visible: self.refresh_ui_state()', launcher)
        self.assertNotIn('refresh_ui_state(self, *', launcher)

    def test_historical_w101_navigator_receipt_is_not_weakened(self):
        text=(ROOT/'tests/test_w101_core_composition_app_desktop_e2e.py').read_text(encoding='utf-8')
        self.assertIn('window.navigator_panel_runtime.set_visible(True)', text)

if __name__ == '__main__':
    unittest.main(verbosity=2)
