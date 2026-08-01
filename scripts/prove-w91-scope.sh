#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
python3 -B - "$ROOT" <<'PY'
from __future__ import annotations
import ast
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
modules = (
    "calamus_scratchpad.py",
    "calamus_scratchpad_store.py",
    "calamus_scratchpad_controller.py",
    "calamus_scratchpad_gateway.py",
    "calamus_scratchpad_runtime.py",
    "calamus_scratchpad_panel.py",
    "calamus_scratchpad_dialogs.py",
)
for name in modules:
    if not (root / "calamus" / name).is_file():
        raise SystemExit(f"missing W91 module: {name}")
print(f"W91_SCOPE_PRODUCTION_MODULES={len(modules)}")

pure = modules[:3]
for name in pure:
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
        raise SystemExit(f"GTK leaked into pure W91 module: {name}")
print("W91_SCOPE_PURE_GTK_FREE=PASS")

model = (root / "calamus/calamus_scratchpad.py").read_text(encoding="utf-8")
if not re.search(r'_TYPES\s*=\s*\("note",\s*"idea",\s*"draft",\s*"task"\)', model):
    raise SystemExit("W91 four-type contract is missing")
for forbidden in ("concept", "question", "reference_key", "source_note", "related_entries"):
    if forbidden in model.casefold():
        raise SystemExit(f"W91 Basic model contains Full-only surface: {forbidden}")
print("W91_SCOPE_FOUR_TYPES_ONLY=PASS")
print("W91_SCOPE_FULL_AUTHORITIES_EXCLUDED=PASS")

store = (root / "calamus/calamus_scratchpad_store.py").read_text(encoding="utf-8")
for required in (
    '+ ".scratchpad.md"',
    '_HEADER = "# Calamus Scratchpad v1"',
    "atomic_write_utf8",
    'ScratchpadSaveResult("conflict"',
):
    if required not in store:
        raise SystemExit(f"W91 store boundary missing: {required}")
print("W91_SCOPE_MARKDOWN_SIDECAR_AND_STALE=PASS")

ui = (root / "calamus/calamus_ui.py").read_text(encoding="utf-8")
for label in (
    '"Scratchpad"',
    '"Capture Selection in Scratchpad…"',
    '"New Scratchpad Entry for Current Section…"',
    '"Show Scratchpad for Current Section"',
):
    if ui.count(label) != 1:
        raise SystemExit(f"W91 visible command count invalid: {label}")
launcher = (root / "bin/calamus").read_text(encoding="utf-8")
for required in (
    "self.scratchpad_runtime",
    "def show_scratchpad",
    "def on_capture_selection_in_scratchpad",
    "def on_new_scratchpad_for_current_section",
    "def on_show_scratchpad_for_current_section",
):
    if required not in launcher:
        raise SystemExit(f"W91 App wiring missing: {required}")
if len(launcher.splitlines()) > 3100:
    raise SystemExit(f"launcher ceiling exceeded: {len(launcher.splitlines())}")
print("W91_SCOPE_DOCUMENT_LINK_COMMANDS=PASS")
print("W91_SCOPE_LAUNCHER_CEILING=PASS")

workspace = (root / "calamus/calamus_workspace.py").read_text(encoding="utf-8")
operations = (root / "calamus/calamus_workspace_operations.py").read_text(encoding="utf-8")
gio = (root / "calamus/calamus_workspace_gio.py").read_text(encoding="utf-8")
for required in ('".source-notes.md"', '".scratchpad.md"'):
    if required not in workspace or required not in operations:
        raise SystemExit(f"managed sidecar contract missing: {required}")
for required in ("scratchpad_source_path", "scratchpad_target_path", "scratchpad_path"):
    if required not in operations + gio:
        raise SystemExit(f"workspace Scratchpad transaction field missing: {required}")
print("W91_SCOPE_WORKSPACE_MANAGED_SIDECAR=PASS")

guide = (root / "share/doc/calamus/USER_GUIDE.md").read_text(encoding="utf-8")
for required in (
    "## Scratchpad Basic",
    "Capture Selection in Scratchpad",
    "Show Scratchpad for Current Section",
    "Rename, Duplicate e Move to Trash",
    "Scratchpad Full",
):
    if required not in guide:
        raise SystemExit(f"W91 guide contract missing: {required}")
print("W91_SCOPE_HELP_COMPLETE=PASS")

version = (root / "calamus/calamus_version.py").read_text(encoding="utf-8")
if 'DEVELOPMENT_WORK_ITEM = "W91"' not in version:
    raise SystemExit("W91 identity is missing")
if 'PUBLISHED_BASELINE = "5a2dd7efe24fa5e6bb4660053c3db936010e6d06"' not in version:
    raise SystemExit("published W90 baseline identity changed")
print("W91_SCOPE_IDENTITY_BASELINE=PASS")

for script_name in (
    "prove-w91-headless-regression.sh",
    "prove-w91-gtk-lanes.sh",
):
    script = root / "scripts" / script_name
    if not script.is_file() or not (script.stat().st_mode & 0o111):
        raise SystemExit(f"W91 gate script missing or not executable: {script_name}")
print("W91_SCOPE_GATE_SCRIPTS=PASS")
print("W91_SCOPE_GATE=PASS")
PY
