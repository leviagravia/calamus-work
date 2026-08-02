from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClipW95ContractTests(unittest.TestCase):
    def test_core_is_gtk_free_and_gtk_is_confined(self):
        for relative in (
            "calamus/calamus_clips.py",
            "calamus/calamus_clip_search.py",
            "calamus/calamus_clip_expansion.py",
            "calamus/calamus_clip_collection.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("gi.repository", text, relative)
            self.assertNotIn("import gi", text, relative)
        for relative in (
            "calamus/calamus_clip_panel.py",
            "calamus/calamus_clip_dialogs.py",
            "calamus/calamus_clip_runtime.py",
        ):
            self.assertTrue((ROOT / relative).is_file())

    def test_menu_shortcut_and_runtime_wiring_are_present(self):
        ui = (ROOT / "calamus/calamus_ui.py").read_text(encoding="utf-8")
        app = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        shortcuts = (ROOT / "calamus/calamus_shortcuts.py").read_text(encoding="utf-8")
        self.assertIn('"Insert Clip…\\tCtrl+Alt+K", app.on_insert_clip', ui)
        self.assertIn('("<Control><Alt>K", app.on_insert_clip)', ui)
        self.assertIn("def on_insert_clip", app)
        self.assertIn("ClipCollectionRuntime", app)
        self.assertIn("MarkdownClipStore", app)
        self.assertIn('ShortcutSpec("Research", "Insert Clip", "Ctrl+Alt+K")', shortcuts)

    def test_panel_does_not_restore_w94_width_regression(self):
        panel = (ROOT / "calamus/calamus_clip_panel.py").read_text(encoding="utf-8")
        self.assertNotIn("RIGHT_PANEL_DEFAULT_WIDTH", panel)
        self.assertNotIn("panel.set_size_request", panel)
        self.assertIn('Gtk.MenuButton(label="Manage")', panel)
        self.assertIn('Search shortcut, title or body', panel)

    def test_rejected_scope_is_absent(self):
        combined = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in (
                "calamus/calamus_clips.py",
                "calamus/calamus_clip_collection.py",
                "calamus/calamus_clip_runtime.py",
                "calamus/calamus_clip_panel.py",
            )
        ).casefold()
        for forbidden in (
            "clipboard watcher",
            "clipboard history",
            "sqlite",
            "cloud sync",
            "nested clip",
            "scratchpadentry",
        ):
            self.assertNotIn(forbidden, combined)

    def test_canonical_contract_audit_and_true_gtk_gate_are_present(self):
        contract = ROOT / "docs/canonical/CALAMUS_W95_CLIP_COLLECTION_CONTRACT.md"
        audit = ROOT / "docs/canonical/CALAMUS_W95_CLIP_COLLECTION_MATURE_SOURCE_AUDIT.md"
        gate = ROOT / "scripts/w95-true-gtk-app-gate.py"
        for path in (contract, audit, gate):
            self.assertTrue(path.is_file(), path)
        contract_text = contract.read_text(encoding="utf-8")
        self.assertIn("Ctrl+Alt+K", contract_text)
        self.assertIn("not a tag", contract_text)
        self.assertIn("W93 Scratchpad Full remains frozen", contract_text)
        gate_text = gate.read_text(encoding="utf-8")
        self.assertIn("launcher.App()", gate_text)
        self.assertIn('emit("row-activated", row)', gate_text)
        self.assertIn("app.on_undo()", gate_text)

    def test_w95extra_identity_points_to_published_w95(self):
        version = (ROOT / "calamus/calamus_version.py").read_text(encoding="utf-8")
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W98"', version)
        self.assertIn(
            'DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Research Panel Integral Closure"',
            version,
        )
        self.assertIn('PUBLISHED_BASELINE = "f7fd70b4ffc7c756b83b8bfa102d224823244092"', version)


if __name__ == "__main__":
    unittest.main()
