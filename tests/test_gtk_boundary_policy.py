"""Static enforcement for the binding Calamus GTK boundary policy."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GtkBoundaryPolicyTests(unittest.TestCase):
    def test_policy_binds_versions_mature_sources_lifecycle_and_rollback(self):
        text = (ROOT / "docs/canonical/CALAMUS_GTK_BOUNDARY_POLICY.md").read_text(
            encoding="utf-8"
        )
        for token in (
            ">=3.10,<3.13",
            ">=3.42,<3.51",
            "GTK 3.24",
            "Gdk typelib: **3.0**",
            "Pango typelib: **1.0**",
            "GTK 4: **not a supported runtime**",
            "Xed 3.8.9",
            "Mousepad",
            "gedit 3.5.1",
            "G_DEBUG=fatal-criticals",
            "fresh subprocess",
            "pure/static regression",
            "Linux Mint XFCE",
            "1366×768",
            "request_application_close()",
            "no surviving working-copy process",
            "protected rollback",
        ):
            self.assertIn(token, text)

    def test_pure_w89_and_w90_modules_do_not_import_or_reference_gtk(self):
        paths = (
            "calamus/calamus_related_references.py",
            "calamus/calamus_reference_sets.py",
            "calamus/calamus_reference_set_store.py",
            "calamus/calamus_reference_set_controller.py",
            "calamus/calamus_reference_integrity.py",
            "calamus/calamus_research_integrity_controller.py",
            "calamus/calamus_modal_dialog.py",
            "calamus/calamus_runtime_identity.py",
            "calamus/calamus_pandoc.py",
            "calamus/calamus_pandoc_process.py",
            "calamus/calamus_pandoc_controller.py",
            "calamus/calamus_scratchpad.py",
            "calamus/calamus_scratchpad_store.py",
            "calamus/calamus_scratchpad_controller.py",
        )
        for relative in paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("from gi", text, relative)
            self.assertNotIn("import gi", text, relative)
            for symbol in ("Gtk.", "Gdk.", "GLib.", "Pango.", "PangoCairo."):
                self.assertNotIn(symbol, text, relative)

    def test_launcher_versions_every_direct_namespace_before_import(self):
        text = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        imported = "from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo"
        self.assertIn(imported, text)
        import_at = text.index(imported)
        for token in (
            'gi.require_version("Gtk", "3.0")',
            'gi.require_version("Gdk", "3.0")',
            'gi.require_version("Pango", "1.0")',
            'gi.require_version("PangoCairo", "1.0")',
        ):
            self.assertIn(token, text)
            self.assertLess(text.index(token), import_at)

    def test_modal_calls_are_confined_to_one_gtk_free_session_owner(self):
        adapter = (ROOT / "calamus/calamus_modal_dialog.py").read_text(
            encoding="utf-8"
        )
        for token in (
            "class ModalSession",
            "def register_source",
            "def run",
            "def close",
            "_hide_if_possible",
            "def run_modal",
            "def destroy_modal",
        ):
            self.assertIn(token, adapter)
        self.assertIn('runner = _callable_attribute(self.dialog, "run")', adapter)
        self.assertIn('destroyer = _callable_attribute(self.dialog, "destroy")', adapter)

        legacy_modal_files = (
            "calamus/calamus_reference_set_dialogs.py",
            "calamus/calamus_related_reference_dialogs.py",
            "calamus/calamus_research_integrity_dialogs.py",
            "calamus/calamus_reference_set_runtime.py",
            "calamus/calamus_reference_runtime.py",
        )
        for relative in legacy_modal_files:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("dialog.run()", text, relative)
            self.assertIn("run_modal(", text, relative)

        for relative in (
            "calamus/calamus_pandoc_dialogs.py",
            "calamus/calamus_pandoc_runtime.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("dialog.run()", text, relative)
            self.assertIn("ModalSession", text, relative)

    def test_modal_driver_is_bounded_semantic_and_cleanup_safe(self):
        helper = (ROOT / "tests/calamus_gtk_test_driver.py").read_text(
            encoding="utf-8"
        )
        research_e2e = (
            ROOT / "tests/test_w89_related_sets_app_desktop_e2e.py"
        ).read_text(encoding="utf-8")
        identity_e2e = (
            ROOT / "tests/test_w90_identity_app_desktop_e2e.py"
        ).read_text(encoding="utf-8")
        w85_e2e = (
            ROOT / "tests/test_research_export_app_desktop_e2e.py"
        ).read_text(encoding="utf-8")
        for token in (
            "class ModalDriver",
            "timeout_seconds",
            "named_widget",
            "label_texts",
            "close_visible_dialogs",
        ):
            self.assertIn(token, helper)
        self.assertGreaterEqual(research_e2e.count("finally:"), 3)
        self.assertGreaterEqual(research_e2e.count("close_visible_dialogs()"), 3)
        self.assertIn("W89_REAL_LIFECYCLE_DELETE=PASS", research_e2e)
        self.assertIn("W89_REAL_LIFECYCLE_QUIT=PASS", research_e2e)
        self.assertNotIn("values.extend(_visible_text(child))", research_e2e)
        self.assertIn('visible_dialog("About Calamus")', identity_e2e)
        self.assertIn('visible_dialog("System Info")', identity_e2e)
        self.assertIn('"calamus-about-text"', identity_e2e)
        self.assertIn('"calamus-system-info-text"', identity_e2e)
        self.assertNotIn("dialogs = visible_dialogs()", identity_e2e)
        self.assertNotIn("visible_dialogs()[0]", identity_e2e)
        self.assertNotIn("dialogs[0]", identity_e2e)
        self.assertIn("_run_single_cancel_proof", w85_e2e)
        self.assertIn("ModalSession", w85_e2e)
        self.assertNotIn("for kind in research_export_kinds():", w85_e2e)
        self.assertNotIn("chooser.set_active_id(kind)", w85_e2e)

    def test_identity_dialogs_are_owned_typed_and_non_deprecated(self):
        dialogs = (ROOT / "calamus/calamus_identity_dialogs.py").read_text(
            encoding="utf-8"
        )
        pure = (ROOT / "calamus/calamus_runtime_identity.py").read_text(
            encoding="utf-8"
        )
        component = (ROOT / "tests/test_identity_dialogs.py").read_text(
            encoding="utf-8"
        )
        for token in (
            "class AboutDialogWidgets",
            "class SystemInfoDialogWidgets",
            "def build_about_dialog",
            "def build_system_info_dialog",
            'dialog.set_name("calamus-about-dialog")',
            'dialog.set_name("calamus-system-info-dialog")',
            'view.set_name(name)',
            "run_modal(widgets.dialog)",
            "destroy_modal(widgets.dialog)",
        ):
            self.assertIn(token, dialogs)
        self.assertNotIn("Gtk.MessageDialog(", dialogs)
        self.assertNotIn("from gi", pure)
        self.assertNotIn("import gi", pure)
        self.assertIn("AboutDialogWidgets", component)
        self.assertIn("SystemInfoDialogWidgets", component)

    def test_w90_pandoc_boundary_is_pure_owned_and_lifecycle_safe(self):
        policy = (ROOT / "docs/canonical/CALAMUS_GTK_BOUNDARY_POLICY.md").read_text(encoding="utf-8")
        dialogs = (ROOT / "calamus/calamus_pandoc_dialogs.py").read_text(encoding="utf-8")
        runtime = (ROOT / "calamus/calamus_pandoc_runtime.py").read_text(encoding="utf-8")
        e2e = (ROOT / "tests/test_w90_pandoc_app_desktop_e2e.py").read_text(encoding="utf-8")
        for token in (
            "calamus_pandoc.py",
            "calamus_pandoc_process.py",
            "calamus_pandoc_controller.py",
            "external Pandoc child",
        ):
            self.assertIn(token, policy)
        self.assertNotIn("dialog.run()", dialogs)
        self.assertIn("with ModalSession", dialogs)
        self.assertNotIn("dialog.run()", runtime)
        self.assertIn("session.register_source", runtime)
        self.assertIn("session.close()", runtime)
        self.assertIn("self._controller.cancel_active()", runtime)
        self.assertIn("thread.join", runtime)
        for token in (
            "calamus-pandoc-product",
            "calamus-pandoc-preview-summary",
        ):
            self.assertIn(token, dialogs)
        for token in (
            "operation_executor=execute_operation",
            "win.pandoc_export_runtime = runtime",
            "runtime.last_outcome.succeeded",
            "W90_REAL_APP_TYPED_DIALOG_HANDOFF=PASS",
            "W90_REAL_APP_REFERENCE_SET_PROVIDER=PASS",
            "W90_REAL_PANDOC_BIBLIOGRAPHY_EXPORT=PASS",
            "W90_REAL_PANDOC_NORMAL_CLOSE=PASS",
            "W90_TRUE_APP_ACTIVE_PANDOC_CLOSE=PASS",
            "W90_TRUE_APP_NO_SURVIVING_PANDOC=PASS",
        ):
            self.assertIn(token, e2e)
        self.assertIn("class PandocWorkflowOutcome", runtime)
        self.assertIn("operation_executor=None", runtime)
        self.assertNotIn("ModalDriver", e2e)
        self.assertNotIn("visible_dialog(", e2e)

    def test_named_gtk_lane_runner_is_fresh_process_and_fatal_critical(self):
        path = ROOT / "scripts/prove-w90-gtk-lanes.sh"
        self.assertTrue(path.is_file())
        self.assertTrue(path.stat().st_mode & 0o111)
        text = path.read_text(encoding="utf-8")
        for token in (
            "G_DEBUG=fatal-criticals",
            "run_lane",
            "test_modal_dialog_gtk_session",
            "test_research_export_app_desktop_e2e",
            "test_pandoc_dialogs",
            "test_w90_identity_app_desktop_e2e",
            "test_w90_pandoc_app_desktop_e2e",
            "W90_GTK_LANES=PASS",
        ):
            self.assertIn(token, text)
        self.assertNotIn("unittest discover", text)

    def test_canonical_close_gateway_is_wired_and_tested(self):
        launcher = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        for token in (
            'self.connect("delete-event", self.on_close)',
            'self.connect("destroy", self.on_destroy)',
            "self.request_application_close()",
            "self.destroy()",
            "Gtk.main_level() > 0",
            "Gtk.main_quit()",
        ):
            self.assertIn(token, launcher)

    def test_boundary_proof_script_exists_and_is_executable(self):
        path = ROOT / "scripts/prove-gtk-boundary.sh"
        self.assertTrue(path.is_file())
        self.assertTrue(path.stat().st_mode & 0o111)
        text = path.read_text(encoding="utf-8")
        for token in (
            "GTK_BOUNDARY_W89_PURE_MODULES=PASS",
            "GTK_BOUNDARY_W90_PURE_MODULES=PASS",
            "GTK_BOUNDARY_W90_NO_NEW_DEPRECATED_API=PASS",
            "GTK_BOUNDARY_W90_PANDOC_DIALOG_LIFECYCLE=PASS",
            "GTK_BOUNDARY_W90_FRESH_PROCESS_LANES=PASS",
            "GTK_BOUNDARY_LAUNCHER_NAMESPACE_VERSIONS=PASS",
            "GTK_BOUNDARY_CHANGED_NAMESPACE_VERSIONS=PASS",
            "GTK_BOUNDARY_MODAL_ADAPTER=PASS",
            "GTK_BOUNDARY_IDENTITY_DIALOG_OWNERSHIP=PASS",
            "GTK_BOUNDARY_LIFECYCLE_GATEWAY=PASS",
            "GTK_BOUNDARY_RUNTIME_RANGE=PASS",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
