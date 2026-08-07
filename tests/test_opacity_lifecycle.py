import unittest
from calamus_opacity_gateway import execute_opacity_preference_request, sync_transparent_control


class _WidgetAPI:
    @staticmethod
    def set_opacity(host, fraction):
        host.events.append(("apply-opacity", fraction, host.opacity_percent))
        if host.fail_apply_for == fraction: raise RuntimeError("adapter failed")


class _App:
    def __init__(self, percent=100, save_results=None, fail_apply_for=None):
        self.opacity_percent=percent; self._opacity_widget_api=_WidgetAPI
        self.save_results=list(save_results if save_results is not None else [True]); self.fail_apply_for=fail_apply_for
        self.events=[]; self.errors=[]
    def apply_opacity_percent(self, percent): _WidgetAPI.set_opacity(self, percent/100.0)
    def save_settings(self, overrides=None): self.events.append(("save-settings", dict(overrides or {}), self.opacity_percent)); return self.save_results.pop(0) if self.save_results else True
    def refresh_ui_state(self): self.events.append(("refresh-ui-state", self.opacity_percent))
    def update_title(self): self.events.append(("update-title", self.opacity_percent))
    def error(self, message): self.errors.append(message)


class OpacityLifecycleTests(unittest.TestCase):
    def test_success_persists_applies_commits_then_projects(self):
        a=_App(100,[True]); self.assertTrue(execute_opacity_preference_request(a,88)); self.assertEqual(a.opacity_percent,88)
        self.assertEqual(a.events,[('save-settings',{'opacity':88},100),('apply-opacity',0.88,100),('refresh-ui-state',88),('update-title',88)])

    def test_noop_only_reprojects(self):
        a=_App(88); self.assertFalse(execute_opacity_preference_request(a,88)); self.assertEqual(a.events,[('refresh-ui-state',88)])

    def test_persistence_failure_keeps_runtime_and_reprojects(self):
        a=_App(100,[False]); self.assertFalse(execute_opacity_preference_request(a,88)); self.assertEqual(a.opacity_percent,100)
        self.assertEqual(a.events,[('save-settings',{'opacity':88},100),('refresh-ui-state',100)]); self.assertTrue(a.errors)

    def test_adapter_failure_restores_persistence_runtime_and_projects(self):
        a=_App(100,[True,True],fail_apply_for=0.88); self.assertFalse(execute_opacity_preference_request(a,88)); self.assertEqual(a.opacity_percent,100)
        self.assertEqual(a.events,[('save-settings',{'opacity':88},100),('apply-opacity',0.88,100),('save-settings',{'opacity':100},100),('apply-opacity',1.0,100),('refresh-ui-state',100)])
        self.assertEqual(a.errors,["Could not apply the Opacity preference: adapter failed"])

    def test_invalid_request_reprojects_and_reports(self):
        a=_App(100); self.assertFalse(execute_opacity_preference_request(a,10)); self.assertEqual(a.events,[('refresh-ui-state',100)]); self.assertTrue(a.errors)

    def test_sync_transparent_control_is_projection_only(self):
        a=_App(70); sync_transparent_control(a); self.assertEqual(a.events,[('refresh-ui-state',70)])


if __name__ == "__main__": unittest.main()
