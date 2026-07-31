#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/calamus:$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -B - "$ROOT" <<'PY'
from __future__ import annotations
import ast
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
ui = (root / "calamus/calamus_ui.py").read_text(encoding="utf-8")
shortcuts = (root / "calamus/calamus_shortcuts.py").read_text(encoding="utf-8")
launcher = (root / "bin/calamus").read_text(encoding="utf-8")
label = "Export with Pandoc/citeproc…"
if ui.count(label) != 1:
    raise SystemExit("W90 must expose exactly one visible Pandoc command")
if 'ShortcutSpec("Research", "Export with Pandoc/citeproc", "menu")' not in shortcuts:
    raise SystemExit("W90 menu-only shortcut registry entry is missing")
if "return self.pandoc_export_runtime.export()" not in launcher:
    raise SystemExit("W90 thin App callback is missing")
print("W90_SCOPE_ONE_COMMAND=PASS")

modules = (
    "calamus_pandoc.py",
    "calamus_pandoc_process.py",
    "calamus_pandoc_controller.py",
    "calamus_pandoc_dialogs.py",
    "calamus_pandoc_runtime.py",
)
logical = 0
for name in modules:
    path = root / "calamus" / name
    if not path.is_file():
        raise SystemExit(f"missing W90 module: {name}")
    lines = path.read_text(encoding="utf-8").splitlines()
    logical += sum(1 for line in lines if line.strip() and not line.lstrip().startswith("#"))
if logical > 1800:
    raise SystemExit(f"W90 logical-line ceiling exceeded: {logical}")
print(f"W90_SCOPE_PRODUCTION_MODULES={len(modules)}")
print(f"W90_SCOPE_LOGICAL_LINES={logical}")
print("W90_SCOPE_BLOAT_CEILING=PASS")

for name in modules[:3]:
    path = root / "calamus" / name
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    if any(item == "gi" or item.startswith("gi.") for item in imports) or "Gtk." in text:
        raise SystemExit(f"GTK leaked into pure W90 module: {name}")
print("W90_SCOPE_PURE_GTK_FREE=PASS")

bibtex = (root / "calamus/calamus_bibtex.py").read_text(encoding="utf-8")
for required in (
    '_BIBLATEX_LITERAL_LIST_FIELDS = frozenset({"publisher", "location"})',
    "def _literal_list_atom_to_bib",
    "format == BIBLATEX and name in _BIBLATEX_LITERAL_LIST_FIELDS",
):
    if required not in bibtex:
        raise SystemExit(f"BibLaTeX scalar/literal-list boundary missing: {required}")
bibtex_test = (root / "tests/test_bibtex.py").read_text(encoding="utf-8")
for required in (
    "test_biblatex_literal_list_fields_preserve_one_scalar_item",
    "publisher = {{Herder and Herder}}",
    "location = {{Trinidad and Tobago}}",
):
    if required not in bibtex_test:
        raise SystemExit(f"BibLaTeX literal-list regression proof missing: {required}")
artifact_helper = (root / "tests/calamus_pandoc_artifact_assertions.py").read_text(encoding="utf-8")
for required in (
    "def normalize_rendered_text",
    'unicodedata.normalize("NFC", value)',
    '" ".join(normalized.split())',
    "def contains_semantic_text",
):
    if required not in artifact_helper:
        raise SystemExit(f"semantic artifact normalizer missing: {required}")
controller_test = (root / "tests/test_pandoc_controller.py").read_text(encoding="utf-8")
true_app_test = (root / "tests/test_w90_pandoc_app_desktop_e2e.py").read_text(encoding="utf-8")
for source_name, source in (("controller", controller_test), ("true-App", true_app_test)):
    for required in (
        "contains_semantic_text",
        '"Herder and Herder"',
        '"Herder; Herder"',
    ):
        if required not in source:
            raise SystemExit(f"{source_name} semantic artifact proof missing: {required}")
    if 'assertIn("Herder and Herder", rendered)' in source:
        raise SystemExit(f"{source_name} still uses a line-wrap-sensitive publisher assertion")
print("W90_SCOPE_SHARED_PURE_BOUNDARY_MODULES=1")
print("W90_SCOPE_BIBLATEX_LITERAL_LIST_BOUNDARY=PASS")
print("W90_SCOPE_SEMANTIC_ARTIFACT_NORMALIZATION=PASS")

implementation = "\n".join((root / "calamus" / name).read_text(encoding="utf-8") for name in modules)
folded = implementation.casefold()
for forbidden in (
    "shell=true",
    "--pdf-engine",
    "--template",
    "--lua-filter",
    "plugin_registry",
    "export_profiles",
    "user_args",
):
    if forbidden in folded:
        raise SystemExit(f"forbidden W90 surface: {forbidden}")
model = (root / "calamus/calamus_pandoc.py").read_text(encoding="utf-8")
if 'FORMAT_PDF' in model or '"pdf"' in model.casefold():
    raise SystemExit("PDF entered the W90 format registry")
process = (root / "calamus/calamus_pandoc_process.py").read_text(encoding="utf-8")
for required in ("shell=False", "start_new_session", "cancel_active", "TemporaryFile"):
    if required not in process:
        raise SystemExit(f"process boundary missing: {required}")
print("W90_SCOPE_CLOSED_PROCESS_SURFACE=PASS")

adapter = (root / "calamus/calamus_modal_dialog.py").read_text(encoding="utf-8")
for required in (
    "class ModalSession",
    "def register_source",
    "_hide_if_possible",
    "def close",
):
    if required not in adapter:
        raise SystemExit(f"modal lifecycle owner missing: {required}")
for script_name in (
    "prove-w90-headless-regression.sh",
    "prove-w90-gtk-lanes.sh",
):
    script = root / "scripts" / script_name
    if not script.is_file() or not (script.stat().st_mode & 0o111):
        raise SystemExit(f"W90 test-lane script missing or not executable: {script_name}")
historical_identity = (
    root / "tests/test_w89_identity_app_desktop_e2e.py"
).read_text(encoding="utf-8")
for stale in (
    "Work item: W89",
    "569dd742abd607bb55a1e6bf9efbad1fdba1684c",
):
    if stale in historical_identity:
        raise SystemExit(
            f"historical W89 identity test owns stale current metadata: {stale}"
        )
current_identity = (
    root / "tests/test_w90_identity_app_desktop_e2e.py"
).read_text(encoding="utf-8")
for required in (
    "DEVELOPMENT_BUILD_LABEL",
    "DEVELOPMENT_WORK_ITEM",
    "DEVELOPMENT_WORK_ITEM_DESCRIPTION",
    "PUBLISHED_BASELINE",
):
    if required not in current_identity:
        raise SystemExit(
            f"current identity true-App test does not project authority: {required}"
        )
lanes = (root / "scripts/prove-w90-gtk-lanes.sh").read_text(encoding="utf-8")
if "W89_IDENTITY_TRUE_APP" in lanes:
    raise SystemExit("W90 runner still executes mutually exclusive W89 current identity")
if "W89_STABLE_IDENTITY_TRUE_APP" not in lanes:
    raise SystemExit("historical stable identity lane is missing")
guide = (root / "share/doc/calamus/USER_GUIDE.md").read_text(encoding="utf-8")
for required in (
    "Tutorial completo: esportare con Pandoc passo per passo",
    "References cited in the current document",
    "All References",
    "One Reference Set",
    "Use Pandoc Default",
    "Local CSL file",
    "Esempio F — Sorgente LaTeX per un progetto esterno",
    "Se il file non si trova, non dichiarare l'export riuscito",
):
    if required not in guide:
        raise SystemExit(f"W90 Help tutorial missing: {required}")
if "FAIL skipped-test" not in lanes or "W90_PANDOC_PREFLIGHT=PASS" not in lanes:
    raise SystemExit("W90 GTK lanes do not forbid skips or require Pandoc preflight")
true_app = (root / "tests/test_w90_pandoc_app_desktop_e2e.py").read_text(encoding="utf-8")
for required in (
    "operation_executor=execute_operation",
    "win.pandoc_export_runtime = runtime",
    "win.on_export_with_pandoc()",
    "runtime.last_outcome.succeeded",
    'observed["set_names"]',
):
    if required not in true_app:
        raise SystemExit(f"W90 true-App typed-handoff proof missing: {required}")
for forbidden in (
    "ModalDriver",
    "visible_dialog(",
    "GLib.timeout_add",
    "def checking_progress()",
    "def preview_progress()",
    "def export_progress()",
):
    if forbidden in true_app:
        raise SystemExit(f"W90 true-App proof still automates transient toolkit state: {forbidden}")
runtime = (root / "calamus/calamus_pandoc_runtime.py").read_text(encoding="utf-8")
for required in (
    "class PandocWorkflowOutcome",
    "def last_outcome",
    "operation_executor=None",
    "def _execute_operation",
):
    if required not in runtime:
        raise SystemExit(f"W90 runtime stable semantic seam missing: {required}")
print("W90_SCOPE_HELP_TUTORIAL_COMPLETE=PASS")
print("W90_SCOPE_PANDOC_PREFLIGHT_AND_NO_SKIPS=PASS")
print("W90_SCOPE_IDENTITY_SINGLE_CURRENT_AUTHORITY=PASS")
print("W90_SCOPE_HISTORICAL_IDENTITY_STABLE_ONLY=PASS")
print("W90_SCOPE_MODAL_SESSION_OWNER=PASS")
print("W90_SCOPE_TYPED_HANDOFF_AND_TERMINAL_OUTCOME=PASS")
print("W90_SCOPE_FRESH_PROCESS_GTK_LANES=PASS")
print("W90_SCOPE_GATE=PASS")
PY
