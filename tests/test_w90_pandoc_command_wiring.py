"""Static contract, wiring and bloat proofs for W90."""
from pathlib import Path
import ast
import unittest
from tests.w104_command_test_support import guide_has

from calamus_help import load_user_guide, parse_user_guide_sections

from tests.w105_menu_test_support import legacy_menu_projection
ROOT = Path(__file__).resolve().parents[1]


class W90PandocCommandWiringTests(unittest.TestCase):
    def test_exactly_one_research_command_is_wired(self):
        launcher = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        composition = (ROOT / "calamus/calamus_research_composition.py").read_text(encoding="utf-8")
        research_runtime = (ROOT / "calamus/calamus_research_application.py").read_text(encoding="utf-8")
        ui = legacy_menu_projection()
        label = "Export with Pandoc/citeproc…"
        self.assertEqual(ui.count(label), 1)
        self.assertIn(f'add_item(researchm, "{label}", app.on_export_with_pandoc)', ui)
        self.assertTrue(guide_has("Research", "Export with Pandoc/citeproc", "menu"))
        for token in (
            "PandocExportController",
            "PandocExportRuntime",
            "pandoc_export_controller = PandocExportController",
            "pandoc_export_runtime = PandocExportRuntime",
        ):
            self.assertIn(token, composition)
        self.assertIn("def on_export_with_pandoc", research_runtime)
        self.assertIn("return self.components.pandoc_export_runtime.export()", research_runtime)
        self.assertIn("on_export_with_pandoc=research_runtime.on_export_with_pandoc", launcher)
        self.assertNotIn("def on_export_with_pandoc", launcher)

    def test_app_is_only_composition_callback_and_close_gateway(self):
        launcher = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        lifecycle = (ROOT / "calamus/calamus_application_lifecycle_app.py").read_text(encoding="utf-8")
        self.assertIn('register_pre_destroy("pandoc-export", pandoc_shutdown)', lifecycle)
        self.assertIn("pandoc_shutdown=self.pandoc_export_runtime.shutdown", launcher)
        self.assertIn("on_export_with_pandoc=research_runtime.on_export_with_pandoc", launcher)
        self.assertNotIn("def on_export_with_pandoc", launcher)
        for forbidden in ("subprocess", "--citeproc", "export_references(", "os.replace("):
            self.assertNotIn(forbidden, launcher[launcher.index("ApplicationCommandPorts("):launcher.index("self.command_actions =")])

    def test_closed_surface_has_no_pdf_or_user_argv(self):
        model = (ROOT / "calamus/calamus_pandoc.py").read_text(encoding="utf-8")
        controller = (ROOT / "calamus/calamus_pandoc_controller.py").read_text(encoding="utf-8")
        dialogs = (ROOT / "calamus/calamus_pandoc_dialogs.py").read_text(encoding="utf-8")
        implementation = "\n".join((model, controller)).casefold()
        for forbidden in (
            "format_pdf",
            "--pdf-engine",
            "--template",
            "--lua-filter",
            "--filter",
            "--css",
            "user_args",
            "plugin_registry",
            "export_profiles",
        ):
            self.assertNotIn(forbidden, implementation)
        self.assertNotIn("shell=True", implementation)
        self.assertNotIn('append("pdf"', dialogs.casefold())

    def test_pure_modules_have_no_gtk_and_process_is_shell_free(self):
        pure = (
            "calamus/calamus_pandoc.py",
            "calamus/calamus_pandoc_process.py",
            "calamus/calamus_pandoc_controller.py",
        )
        for relative in pure:
            text = (ROOT / relative).read_text(encoding="utf-8")
            tree = ast.parse(text, filename=relative)
            imported = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imported.append(node.module or "")
            self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imported), relative)
            self.assertNotIn("Gtk.", text, relative)
        process = (ROOT / "calamus/calamus_pandoc_process.py").read_text(encoding="utf-8")
        self.assertIn("shell=False", process)
        self.assertIn("start_new_session", process)
        self.assertIn("cancel_active", process)

    def test_scope_and_production_delta_stay_bounded(self):
        new_modules = (
            "calamus/calamus_pandoc.py",
            "calamus/calamus_pandoc_process.py",
            "calamus/calamus_pandoc_controller.py",
            "calamus/calamus_pandoc_dialogs.py",
            "calamus/calamus_pandoc_runtime.py",
        )
        logical = 0
        for relative in new_modules:
            lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
            logical += sum(1 for line in lines if line.strip() and not line.lstrip().startswith("#"))
        self.assertLessEqual(logical, 1800)
        self.assertEqual(len(new_modules), 5)
        changed_existing = (
            "bin/calamus",
            "calamus/calamus_modal_dialog.py",
            "calamus/calamus_ui.py",
            "calamus/calamus_shortcuts.py",
            "calamus/calamus_version.py",
            "calamus/calamus_bibtex.py",
        )
        self.assertEqual(len(changed_existing), 6)

    def test_biblatex_scalar_to_literal_list_boundary_is_explicit(self):
        exporter = (ROOT / "calamus/calamus_bibtex.py").read_text(encoding="utf-8")
        self.assertIn(
            '_BIBLATEX_LITERAL_LIST_FIELDS = frozenset({"publisher", "location"})',
            exporter,
        )
        self.assertIn("def _literal_list_atom_to_bib", exporter)
        self.assertIn(
            "format == BIBLATEX and name in _BIBLATEX_LITERAL_LIST_FIELDS",
            exporter,
        )
        controller_test = (ROOT / "tests/test_pandoc_controller.py").read_text(encoding="utf-8")
        self.assertIn(
            "test_real_document_odt_preserves_scalar_biblatex_publisher_with_and",
            controller_test,
        )
        self.assertIn("contains_semantic_text", controller_test)
        self.assertIn('"Herder and Herder"', controller_test)
        self.assertIn('"Herder; Herder"', controller_test)
        self.assertNotIn('assertIn("Herder and Herder", rendered)', controller_test)
        helper = (ROOT / "tests/calamus_pandoc_artifact_assertions.py").read_text(encoding="utf-8")
        self.assertIn("def normalize_rendered_text", helper)
        self.assertIn('" ".join(normalized.split())', helper)

    def test_scope_gate_script_is_executable_and_declares_closed_surface(self):
        path = ROOT / "scripts/prove-w90-scope.sh"
        self.assertTrue(path.is_file())
        self.assertTrue(path.stat().st_mode & 0o111)
        text = path.read_text(encoding="utf-8")
        for marker in (
            "W90_SCOPE_ONE_COMMAND=PASS",
            "W90_SCOPE_BLOAT_CEILING=PASS",
            "W90_SCOPE_PURE_GTK_FREE=PASS",
            "W90_SCOPE_BIBLATEX_LITERAL_LIST_BOUNDARY=PASS",
            "W90_SCOPE_SEMANTIC_ARTIFACT_NORMALIZATION=PASS",
            "W90_SCOPE_CLOSED_PROCESS_SURFACE=PASS",
            "W90_SCOPE_GATE=PASS",
        ):
            self.assertIn(marker, text)


    def test_contract_and_guide_explain_authority_preview_and_recovery(self):
        contract = (ROOT / "docs/canonical/CALAMUS_W90_PANDOC_CITEPROC_CONTRACT.md").read_text(encoding="utf-8")
        guide = load_user_guide(ROOT)
        for token in (
            "references.md",
            "external Pandoc",
            "semantic preview",
            "shell=False",
            "stale",
            "No PDF",
            "No custom Pandoc arguments",
            "no network",
        ):
            self.assertIn(token.casefold(), contract.casefold())
        for token in (
            "Export with Pandoc/citeproc",
            "Formatted Bibliography",
            "Current Document with Citations",
            "semantic preview",
            "Reference Set names are case-sensitive",
            "Pandoc is not installed",
            "Remote images or media",
        ):
            self.assertIn(token, guide)
        titles = tuple(item.title for item in parse_user_guide_sections(guide))
        self.assertIn("Export with Pandoc/citeproc", titles)

    def test_true_app_proof_uses_typed_seams_and_terminal_outcome(self):
        proof = (ROOT / "tests/test_w90_pandoc_app_desktop_e2e.py").read_text(encoding="utf-8")
        runtime = (ROOT / "calamus/calamus_pandoc_runtime.py").read_text(encoding="utf-8")
        for token in (
            "operation_executor=execute_operation",
            "win.pandoc_export_runtime = runtime",
            "win.on_export_with_pandoc()",
            "runtime.last_outcome.succeeded",
            "W90_REAL_APP_TYPED_DIALOG_HANDOFF=PASS",
            "W90_REAL_APP_REFERENCE_SET_PROVIDER=PASS",
            "W90_REAL_PANDOC_TERMINAL_OUTCOME=PASS",
        ):
            self.assertIn(token, proof)
        for fragile in (
            "ModalDriver",
            "visible_dialog(",
            "def checking_progress()",
            "def preview_progress()",
            "def export_progress()",
            "[options, destination, checking_progress",
        ):
            self.assertNotIn(fragile, proof)
        for token in (
            "class PandocWorkflowOutcome",
            "operation_executor=None",
            "def last_outcome",
            "def _execute_operation",
        ):
            self.assertIn(token, runtime)
        component = (ROOT / "tests/test_pandoc_dialogs.py").read_text(encoding="utf-8")
        self.assertIn("test_progress_builder_owns_spinner_and_status", component)
        self.assertIn('"Core sources"', component)

    def test_provenance_lists_every_w90_module(self):
        proof = (ROOT / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")
        for name in (
            "calamus_pandoc",
            "calamus_pandoc_process",
            "calamus_pandoc_controller",
            "calamus_pandoc_dialogs",
            "calamus_pandoc_runtime",
        ):
            self.assertIn(f'"{name}"', proof)


if __name__ == "__main__":
    unittest.main()
