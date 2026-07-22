import os
import sys
import unittest

import calamus_audit as audit


class ShortcutAuditTests(unittest.TestCase):
    def test_full_shortcut_table_has_no_duplicates(self):
        self.assertEqual(audit.shortcut_conflicts(), {})

    def test_normalizes_ctrl_aliases(self):
        specs = (
            audit.ShortcutSpec("A", "<Ctrl>N"),
            audit.ShortcutSpec("B", "<Control>N"),
        )
        self.assertEqual(audit.shortcut_conflicts(specs), {"<Control>N": ["A", "B"]})

    def test_requested_shortcuts_exist(self):
        by_name = {spec.command: spec.shortcut for spec in audit.SHORTCUTS}
        self.assertEqual(by_name["Character Map"], "<Control><Alt>F10")
        self.assertEqual(by_name["Research Panel"], "<Control><Alt>C")

    def test_research_panel_avoids_alt_f10_window_manager_shortcut(self):
        by_name = {spec.command: spec.shortcut for spec in audit.SHORTCUTS}
        self.assertNotEqual(by_name["Research Panel"], "<Alt>F10")
        self.assertEqual(by_name["Research Panel"], "<Control><Alt>C")


class PackageAuditTests(unittest.TestCase):
    def _package_paths(self):
        # Installed layout: audit only Calamus, never the whole /usr tree.
        # Development/unpacked layout: use the package root if present.
        test_dir = os.path.abspath(os.path.dirname(__file__))
        maybe_pkg_root = os.path.abspath(os.path.join(test_dir, "..", "..", ".."))
        dev_paths = audit.dev_package_paths(maybe_pkg_root)
        return dev_paths or audit.default_package_paths()

    def test_python_sources_compile(self):
        failures = audit.compile_python_paths(self._package_paths())
        self.assertEqual(failures, [])

    def test_no_pycache_dirs_in_package_tree(self):
        hits = audit.find_pycache_dirs_in_paths(self._package_paths())
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
