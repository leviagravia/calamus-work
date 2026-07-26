#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$ROOT/calamus:$ROOT/tests:$ROOT"

python3 -B - "$ROOT" <<'PY'
from __future__ import annotations

import ast
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
policy = root / "docs/canonical/CALAMUS_GTK_BOUNDARY_POLICY.md"
if not policy.is_file():
    raise SystemExit("GTK boundary policy is missing")

pure_modules = (
    "calamus/calamus_related_references.py",
    "calamus/calamus_reference_sets.py",
    "calamus/calamus_reference_set_store.py",
    "calamus/calamus_reference_set_controller.py",
    "calamus/calamus_reference_integrity.py",
    "calamus/calamus_research_integrity_controller.py",
    "calamus/calamus_modal_dialog.py",
    "calamus/calamus_runtime_identity.py",
)
for relative in pure_modules:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            else:
                names = [node.module or ""]
            if any(name == "gi" or name.startswith("gi.") for name in names):
                raise SystemExit(f"GTK import escaped into pure module: {relative}")
    if re.search(r"\b(?:Gtk|Gdk|GLib|Pango|PangoCairo)\.", text):
        raise SystemExit(f"GTK symbol escaped into pure module: {relative}")
print("GTK_BOUNDARY_W89_PURE_MODULES=PASS")

launcher = (root / "bin/calamus").read_text(encoding="utf-8")
import_line = "from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo"
requirements = {
    "Gtk": 'gi.require_version("Gtk", "3.0")',
    "Gdk": 'gi.require_version("Gdk", "3.0")',
    "Pango": 'gi.require_version("Pango", "1.0")',
    "PangoCairo": 'gi.require_version("PangoCairo", "1.0")',
}
if import_line not in launcher:
    raise SystemExit("launcher GI import contract is missing")
import_at = launcher.index(import_line)
for namespace, required in requirements.items():
    if required not in launcher or launcher.index(required) > import_at:
        raise SystemExit(
            f"{namespace} version must be required before the launcher import"
        )
print("GTK_BOUNDARY_LAUNCHER_NAMESPACE_VERSIONS=PASS")

changed_gtk_files = (
    "bin/calamus",
    "calamus/calamus_authoring_bridge_view.py",
    "calamus/calamus_reference_panel.py",
    "calamus/calamus_reference_runtime.py",
    "calamus/calamus_reference_set_dialogs.py",
    "calamus/calamus_reference_set_runtime.py",
    "calamus/calamus_reference_set_view.py",
    "calamus/calamus_related_reference_dialogs.py",
    "calamus/calamus_research_integrity_dialogs.py",
    "calamus/calamus_identity_dialogs.py",
)
version_map = {
    "Gtk": "3.0",
    "Gdk": "3.0",
    "Pango": "1.0",
    "PangoCairo": "1.0",
}
for relative in changed_gtk_files:
    text = (root / relative).read_text(encoding="utf-8")
    for match in re.finditer(r"from gi\.repository import ([^\n]+)", text):
        imported = {
            part.strip().split(" as ", 1)[0]
            for part in match.group(1).split(",")
        }
        prefix = text[: match.start()]
        for namespace in sorted(imported & version_map.keys()):
            token = (
                f'gi.require_version("{namespace}", '
                f'"{version_map[namespace]}")'
            )
            if token not in prefix:
                raise SystemExit(
                    f"unversioned direct {namespace} import in changed GTK file: "
                    f"{relative}"
                )
    for forbidden in (":prelight", "override_font(", ".set_opacity(", ".get_opacity("):
        if forbidden in text:
            raise SystemExit(
                f"new/changed GTK boundary contains deprecated pattern "
                f"{forbidden}: {relative}"
            )
print("GTK_BOUNDARY_CHANGED_NAMESPACE_VERSIONS=PASS")
print("GTK_BOUNDARY_W89_NO_NEW_DEPRECATED_API=PASS")

modal_files = (
    "calamus/calamus_reference_set_dialogs.py",
    "calamus/calamus_related_reference_dialogs.py",
    "calamus/calamus_research_integrity_dialogs.py",
    "calamus/calamus_reference_set_runtime.py",
    "calamus/calamus_reference_runtime.py",
    "calamus/calamus_identity_dialogs.py",
)
for relative in modal_files:
    text = (root / relative).read_text(encoding="utf-8")
    if ".run()" in text:
        raise SystemExit(f"direct nested modal loop escaped adapter: {relative}")
    if "run_modal(" not in text:
        raise SystemExit(f"modal adapter is not used: {relative}")
adapter = (root / "calamus/calamus_modal_dialog.py").read_text(encoding="utf-8")
for token in ("def run_modal", "def destroy_modal", "dialog.run()", "dialog.destroy()"):
    if token not in adapter:
        raise SystemExit(f"modal boundary contract missing: {token}")
print("GTK_BOUNDARY_MODAL_ADAPTER=PASS")

helper = (root / "tests/calamus_gtk_test_driver.py").read_text(encoding="utf-8")
research_e2e = (
    root / "tests/test_w89_related_sets_app_desktop_e2e.py"
).read_text(encoding="utf-8")
identity_e2e = (
    root / "tests/test_w89_identity_app_desktop_e2e.py"
).read_text(encoding="utf-8")
identity_dialogs = (
    root / "calamus/calamus_identity_dialogs.py"
).read_text(encoding="utf-8")
for token in (
    "class ModalDriver",
    "timeout_seconds",
    "close_visible_dialogs",
    "label_texts",
    "named_widget",
):
    if token not in helper:
        raise SystemExit(f"GTK test driver contract missing: {token}")
for token in (
    "ModalDriver",
    "finally:",
    "close_visible_dialogs()",
    "dialog_text",
    "W89_REAL_LIFECYCLE_DELETE=PASS",
    "W89_REAL_LIFECYCLE_QUIT=PASS",
):
    if token not in research_e2e:
        raise SystemExit(f"W89 true-App cleanup/lifecycle contract missing: {token}")
if "values.extend(_visible_text(child))" in research_e2e:
    raise SystemExit("character-splitting recursive dialog text helper returned")
for token in (
    'visible_dialog("About Calamus")',
    'visible_dialog("System Info")',
    '"calamus-about-text"',
    '"calamus-system-info-text"',
):
    if token not in identity_e2e:
        raise SystemExit(f"identity true-App semantic lookup missing: {token}")
for forbidden in (
    "dialogs = visible_dialogs()",
    "visible_dialogs()[0]",
    "dialogs[0]",
):
    if forbidden in identity_e2e:
        raise SystemExit(f"identity test uses global dialog ordering: {forbidden}")
for token in (
    "class AboutDialogWidgets",
    "class SystemInfoDialogWidgets",
    "def build_about_dialog",
    "def build_system_info_dialog",
    "run_modal(widgets.dialog)",
    "destroy_modal(widgets.dialog)",
):
    if token not in identity_dialogs:
        raise SystemExit(f"owned identity dialog contract missing: {token}")
if "Gtk.MessageDialog(" in identity_dialogs:
    raise SystemExit("identity lane reintroduced Gtk.MessageDialog")
print("GTK_BOUNDARY_IDENTITY_DIALOG_OWNERSHIP=PASS")
print("GTK_BOUNDARY_MODAL_DRIVER_STATIC=PASS")

for token in (
    'self.connect("delete-event", self.on_close)',
    'self.connect("destroy", self.on_destroy)',
    "self.request_application_close()",
    "self.destroy()",
    "Gtk.main_level() > 0",
    "Gtk.main_quit()",
):
    if token not in launcher:
        raise SystemExit(f"canonical lifecycle gateway missing: {token}")
print("GTK_BOUNDARY_LIFECYCLE_GATEWAY=PASS")
PY

# Runtime/version probing deliberately runs in a fresh interpreter.  GTK 3 and
# GTK 4 are never imported in the same process.
python3 -B - <<'PY'
from __future__ import annotations
import os
import sys

enforce = os.environ.get("CALAMUS_GTK_ENFORCE_RUNTIME") == "1"
print(f"GTK_BOUNDARY_PYTHON_VERSION={sys.version.split()[0]}")
if not (3, 10) <= sys.version_info[:2] < (3, 13):
    message = f"Unsupported Python runtime: {sys.version.split()[0]}"
    if enforce:
        raise SystemExit(message)
    print(f"GTK_BOUNDARY_PYTHON_RANGE=SKIP reason={message}")
else:
    print("GTK_BOUNDARY_PYTHON_RANGE=PASS")

try:
    import gi
except Exception as error:
    if enforce:
        raise SystemExit(f"PyGObject unavailable: {error}")
    print(f"GTK_BOUNDARY_RUNTIME=SKIP reason={error}")
    raise SystemExit(77)

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gdk, Gtk, Pango, PangoCairo

parts = tuple(int(value) for value in gi.__version__.split(".")[:2])
if not (3, 42) <= parts < (3, 51):
    raise SystemExit(f"Unsupported PyGObject runtime: {gi.__version__}")
if Gtk.get_major_version() != 3 or Gtk.get_minor_version() != 24:
    raise SystemExit(
        f"Unsupported GTK runtime: {Gtk.get_major_version()}."
        f"{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
    )
if Gtk.get_micro_version() < 30:
    raise SystemExit(f"GTK micro version is below 30: {Gtk.get_micro_version()}")
print(f"GTK_BOUNDARY_PYGOBJECT_VERSION={gi.__version__}")
print(
    "GTK_BOUNDARY_GTK_VERSION="
    f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
)
print(f"GTK_BOUNDARY_PANGO_MODULE={Pango.__name__}")
print(f"GTK_BOUNDARY_PANGOCAIRO_MODULE={PangoCairo.__name__}")
try:
    init_result = Gtk.init_check()
except TypeError:
    init_result = Gtk.init_check(None)
init_ok = bool(init_result[0]) if isinstance(init_result, tuple) else bool(init_result)
display = Gdk.Display.get_default()
if enforce and (not init_ok or display is None):
    raise SystemExit("GTK display is unavailable for the enforced runtime gate")
print(f"GTK_BOUNDARY_DISPLAY={display.get_name() if display else '<none>'}")
print("GTK_BOUNDARY_RUNTIME_RANGE=PASS")
PY
