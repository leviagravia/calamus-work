import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class W106PreferencesApplicationStateContractTests(unittest.TestCase):
    def test_w106_core_modules_are_gtk_free(self):
        for rel in (
            "calamus/calamus_preferences.py",
            "calamus/calamus_application_state.py",
            "calamus/calamus_settings_repository.py",
            "calamus/calamus_preferences_controller.py",
            "calamus/calamus_persistent_collections.py",
            "calamus/calamus_preferences_composition.py",
        ):
            text = (ROOT / rel).read_text(encoding="utf-8")
            tree = ast.parse(text)
            imported = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.append(node.module)
            joined = "\n".join(imported)
            for forbidden in ("gi", "Gtk", "Gdk", "Pango"):
                self.assertNotIn(forbidden, joined, rel)

    def test_app_has_no_raw_settings_or_generic_save_settings_authority(self):
        text = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        self.assertNotIn("self.settings", text)
        self.assertNotIn("def save_settings(", text)
        self.assertNotIn("self.state", text)
        self.assertIn("build_preferences_application_state_components", text)
        self.assertIn("self.application_state.record_last_file", text)

    def test_core_composition_does_not_pass_raw_state_manager_or_settings_dict(self):
        text = (ROOT / "calamus/calamus_application_composition.py").read_text(encoding="utf-8")
        self.assertNotIn("app.settings", text)
        self.assertNotIn("app.state", text)
        self.assertNotIn("save_settings=", text)
        self.assertIn("recent_workspaces=inputs.recent_workspaces", text)
        self.assertIn("application_state=inputs.application_state", text)
        launcher = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        self.assertIn("recent_workspaces=self.recent_workspace_store", launcher)
        self.assertIn("application_state=self.application_state", launcher)

    def test_state_manager_is_explicit_compatibility_only(self):
        text = (ROOT / "calamus/calamus_state.py").read_text(encoding="utf-8")
        self.assertIn("Deprecated compatibility facade", text)
        self.assertIn("RecentFileStore", text)
        self.assertIn("SettingsRepository", text)

    def test_w105_ui_state_remains_distinct(self):
        prefs = (ROOT / "calamus/calamus_preferences.py").read_text(encoding="utf-8")
        appstate = (ROOT / "calamus/calamus_application_state.py").read_text(encoding="utf-8")
        self.assertNotIn("UiStateSnapshot", prefs)
        self.assertNotIn("UiStateSnapshot", appstate)
        self.assertTrue((ROOT / "calamus/calamus_ui_state.py").exists())


if __name__ == "__main__":
    unittest.main()
