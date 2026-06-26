from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RuntimeIdentityWorkingCopyTests(unittest.TestCase):
    def test_working_copy_window_title_identity(self):
        source = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
        self.assertIn('APP_TITLE = "Calamus Copy"', source)
        self.assertIn('self.set_title(f"{APP_TITLE} - {name} ({status})")', source)
        self.assertNotIn('APP_TITLE = "Calamus"\n', source)

    def test_working_copy_about_identity_is_display_only(self):
        source = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
        self.assertIn('RUNTIME_ABOUT_NAME = "Calamus-Working-Copy"', source)
        self.assertIn('show_about(self, VERSION, RUNTIME_ABOUT_NAME)', source)
        self.assertIn('from calamus_version import APP_VERSION as VERSION', source)

    def test_about_dialog_supports_display_name_without_rewriting_version(self):
        dialogs = (ROOT / "calamus" / "calamus_dialogs.py").read_text(encoding="utf-8")
        self.assertIn('def show_about(parent, version, display_name=None):', dialogs)
        self.assertIn('about_header = display_name or f"Calamus {version}"', dialogs)
        self.assertIn('about_body = f"""{about_header}', dialogs)

    def test_formal_package_version_is_preserved(self):
        version = (ROOT / "calamus" / "calamus_version.py").read_text(encoding="utf-8")
        self.assertIn('APP_VERSION = "1.7.0-rc3-stable4.3"', version)
        self.assertNotIn("Calamus-Working-Copy", version)
        self.assertNotIn("Calamus Copy", version)

    def test_icon_desktop_and_package_identity_are_not_renamed(self):
        source = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
        self.assertIn('APP_ICON = "calamus"', source)
        for relative in [
            "debian/control",
            "debian/changelog",
            "data/calamus.desktop",
            "calamus.desktop",
            "usr/share/applications/calamus.desktop",
        ]:
            path = ROOT / relative
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn("Calamus Copy", text)
            self.assertNotIn("Calamus-Working-Copy", text)


if __name__ == "__main__":
    unittest.main()
