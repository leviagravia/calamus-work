from pathlib import Path
import unittest

from calamus_runtime_identity import (
    PRODUCT_NAME,
    SystemInfoSnapshot,
    build_about_body,
    build_runtime_identity,
    render_system_info,
)
from calamus_version import (
    APP_VERSION,
    DEVELOPMENT_BUILD_LABEL,
    DEVELOPMENT_WORK_ITEM,
    PUBLISHED_BASELINE,
)


ROOT = Path(__file__).resolve().parents[1]


class RuntimeIdentityWorkingCopyTests(unittest.TestCase):
    def setUp(self):
        self.identity = build_runtime_identity(
            DEVELOPMENT_BUILD_LABEL,
            DEVELOPMENT_WORK_ITEM,
            PUBLISHED_BASELINE,
        )

    def test_working_copy_window_title_identity_remains_distinct(self):
        source = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
        self.assertIn('APP_TITLE = "Calamus Copy"', source)
        self.assertIn('self.set_title(f"{APP_TITLE} - {name} ({status})")', source)

    def test_about_visible_identity_is_only_calamus(self):
        self.assertEqual(PRODUCT_NAME, "Calamus")
        self.assertEqual(self.identity.product_name, "Calamus")
        body = build_about_body(self.identity)
        self.assertEqual(body.splitlines()[0], "Calamus")
        self.assertNotIn("Calamus-Working-Copy", body)
        self.assertNotIn(APP_VERSION, body)

    def test_system_info_is_rendered_from_gtk_free_snapshot(self):
        snapshot = SystemInfoSnapshot(
            identity=self.identity,
            python_version="3.12.3",
            pygobject_version="3.48.2",
            gtk_version="3.24.41",
            operating_system="Linux",
            desktop="XFCE",
            session="x11",
            config_path="/tmp/config",
            hunspell_dictionaries="it_IT, en_US",
        )
        rendered = render_system_info(snapshot)
        self.assertEqual(
            rendered.splitlines()[:3],
            [
                f"Calamus: {DEVELOPMENT_BUILD_LABEL}",
                f"Work item: {DEVELOPMENT_WORK_ITEM}",
                f"Published baseline: {PUBLISHED_BASELINE}",
            ],
        )
        for token in (
            "Python: 3.12.3",
            "PyGObject: 3.48.2",
            "GTK: 3.24.41",
            "OS: Linux",
            "Desktop: XFCE",
            "Session: x11",
            "Config path: /tmp/config",
            "Hunspell dictionaries: it_IT, en_US",
        ):
            self.assertIn(token, rendered)
        self.assertNotIn("Calamus: 1.7.0", rendered)

    def test_development_identity_constants_are_exact(self):
        self.assertEqual(DEVELOPMENT_BUILD_LABEL, "Development build")
        self.assertEqual(DEVELOPMENT_WORK_ITEM, "W90")
        self.assertEqual(
            PUBLISHED_BASELINE,
            "673c17aa3239bf189f11c93af36e4ea137df2f6d",
        )

    def test_historical_package_version_is_preserved_but_not_runtime_label(self):
        self.assertEqual(APP_VERSION, "1.7.0-rc3-stable4.3")
        self.assertNotIn("Calamus-Working-Copy", APP_VERSION)

    def test_launcher_uses_owned_identity_presenters(self):
        source = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
        self.assertIn("present_about_dialog(self, self.runtime_identity())", source)
        self.assertIn("render_system_info(self.system_info_snapshot())", source)
        self.assertIn("present_system_info_dialog(", source)
        self.assertNotIn("RUNTIME_ABOUT_NAME", source)
        self.assertNotIn('self.large_info("System Info"', source)

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
