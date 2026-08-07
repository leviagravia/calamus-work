import unittest
from calamus_appearance_gateway import execute_appearance_preference_request, sync_appearance_controls
from calamus_appearance_preferences import APPEARANCE_DARK, APPEARANCE_LIGHT, APPEARANCE_SYSTEM


class _App:
    def __init__(self, mode=APPEARANCE_LIGHT, persist=True):
        self.appearance_mode=mode; self.persist=persist; self.events=[]; self.errors=[]
    def save_settings(self, overrides=None): self.events.append(("save-settings",dict(overrides or {}),self.appearance_mode)); return self.persist
    def refresh_ui_state(self): self.events.append(("refresh-ui-state",self.appearance_mode))
    def apply_font(self): self.events.append(("apply-font",self.appearance_mode))
    def error(self,message): self.errors.append(message)


class AppearanceLifecycleTests(unittest.TestCase):
    def test_success_persists_commits_projects_then_applies(self):
        a=_App(APPEARANCE_LIGHT,True); self.assertTrue(execute_appearance_preference_request(a,APPEARANCE_DARK)); self.assertEqual(a.appearance_mode,APPEARANCE_DARK)
        self.assertEqual(a.events,[('save-settings',{'appearance_mode':APPEARANCE_DARK,'white_background':False,'dark_mode':True},APPEARANCE_LIGHT),('refresh-ui-state',APPEARANCE_DARK),('apply-font',APPEARANCE_DARK)])

    def test_persistence_failure_keeps_runtime_and_reprojects(self):
        a=_App(APPEARANCE_LIGHT,False); self.assertFalse(execute_appearance_preference_request(a,APPEARANCE_DARK)); self.assertEqual(a.appearance_mode,APPEARANCE_LIGHT)
        self.assertEqual(a.events,[('save-settings',{'appearance_mode':APPEARANCE_DARK,'white_background':False,'dark_mode':True},APPEARANCE_LIGHT),('refresh-ui-state',APPEARANCE_LIGHT)])
        self.assertTrue(a.errors)

    def test_noop_only_reprojects(self):
        a=_App(APPEARANCE_DARK,True); self.assertFalse(execute_appearance_preference_request(a,APPEARANCE_DARK)); self.assertEqual(a.events,[('refresh-ui-state',APPEARANCE_DARK)])

    def test_sync_controls_projects_all_modes_without_widgets(self):
        for mode in (APPEARANCE_LIGHT,APPEARANCE_DARK,APPEARANCE_SYSTEM):
            a=_App(mode); sync_appearance_controls(a); self.assertEqual(a.events,[('refresh-ui-state',mode)])

    def test_invalid_request_reprojects_and_reports(self):
        a=_App(APPEARANCE_LIGHT); self.assertFalse(execute_appearance_preference_request(a,'sepia')); self.assertEqual(a.appearance_mode,APPEARANCE_LIGHT)
        self.assertEqual(a.events,[('refresh-ui-state',APPEARANCE_LIGHT)]); self.assertEqual(a.errors,['requested appearance mode is invalid'])


if __name__ == "__main__": unittest.main()
