#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/calamus:$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -B - "$ROOT" <<'PY'
from __future__ import annotations
import ast
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()

registry = root / "calamus/calamus_managed_sidecars.py"
if not registry.is_file():
    raise SystemExit("missing managed sidecar registry")
text = registry.read_text(encoding="utf-8")
if '".source-notes.md"' not in text or '".scratchpad.md"' not in text:
    raise SystemExit("managed sidecar registry is incomplete")
for required in (
    "ManagedSidecarSpec",
    "MANAGED_DOCUMENT_SIDECARS",
    "document_sidecar_path",
    "sidecar_spec_for_suffix",
    "is_managed_sidecar_name",
):
    if required not in text:
        raise SystemExit(f"managed sidecar registry missing: {required}")
production_literals = []
for path in (root / "calamus").glob("*.py"):
    if path == registry:
        continue
    source = path.read_text(encoding="utf-8")
    if '".source-notes.md"' in source or '".scratchpad.md"' in source:
        production_literals.append(path.name)
if production_literals:
    raise SystemExit(f"managed sidecar literals escaped registry: {production_literals}")
print("W92_SCOPE_MANAGED_SIDECAR_SINGLE_AUTHORITY=PASS")

pure_modules = (
    "calamus_managed_sidecars.py",
    "calamus_source_note_store.py",
    "calamus_scratchpad_store.py",
)
for name in pure_modules:
    path = root / "calamus" / name
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    if any(item == "gi" or item.startswith("gi.") for item in imports):
        raise SystemExit(f"GTK leaked into pure W92 module: {name}")
    if any(symbol in source for symbol in ("Gtk.", "Gdk.", "GLib.", "Pango.")):
        raise SystemExit(f"GTK symbol leaked into pure W92 module: {name}")
print("W92_SCOPE_PURE_BOUNDARY=PASS")

runtime = (root / "calamus/calamus_research_panel.py").read_text(encoding="utf-8")
view = (root / "calamus/calamus_research_panel_view.py").read_text(encoding="utf-8")
if "focus_active" in runtime or "def focus_active" in view:
    raise SystemExit("duplicate Research activation surface remains")
if runtime.count("self._view.show_client(target)") != 1:
    raise SystemExit("Research runtime does not have one client-selection owner")
if "Guard that transition and activate exactly once" not in view:
    raise SystemExit("selector/stack activation guard is missing")
print("W92_SCOPE_RESEARCH_SINGLE_ACTIVATION=PASS")

panel = (root / "calamus/calamus_scratchpad_panel.py").read_text(encoding="utf-8")
runtime_sp = (root / "calamus/calamus_scratchpad_runtime.py").read_text(encoding="utf-8")
for required in (
    'Gtk.Button(label="Refresh")',
    'def _dispatch_scratchpad_list_key',
    'key == "Insert"',
    'key in {"Delete", "KP_Delete"}',
    'key == "F5"',
):
    if required not in panel:
        raise SystemExit(f"Scratchpad efficiency control missing: {required}")
if "return self.sync_document(force=True)" not in runtime_sp:
    raise SystemExit("Scratchpad Refresh does not force a reload")
print("W92_SCOPE_SCRATCHPAD_REFRESH_AND_KEYS=PASS")

ui = (root / "calamus/calamus_ui.py").read_text(encoding="utf-8")
shortcuts = (root / "calamus/calamus_shortcuts.py").read_text(encoding="utf-8")
for required in (
    'Scratchpad\\tCtrl+Alt+S',
    'Capture Selection in Scratchpad…\\tCtrl+Alt+Shift+S',
    '("<Control><Alt>S", app.show_scratchpad)',
    '("<Control><Alt><Shift>S", app.on_capture_selection_in_scratchpad)',
):
    if required not in ui:
        raise SystemExit(f"W92 UI shortcut missing: {required}")
for required in (
    'ShortcutSpec("Research", "Scratchpad", "Ctrl+Alt+S")',
    'ShortcutSpec("Research", "Capture Selection in Scratchpad", "Ctrl+Alt+Shift+S")',
):
    if required not in shortcuts:
        raise SystemExit(f"shortcut registry missing: {required}")
print("W92_SCOPE_SHORTCUTS=PASS")

guide = (root / "share/doc/calamus/USER_GUIDE.md").read_text(encoding="utf-8")
for required in (
    "The six objects you must distinguish",
    "Le autorità sono cinque",
    "Scratchpad Basic: dal pensiero provvisorio al testo",
    "Document.md.scratchpad.md",
    "Documento.md.scratchpad.md",
    "Ctrl+Alt+S",
    "Ctrl+Alt+Shift+S",
    "Il pulsante **Refresh**",
    "Rename, Duplicate e Move to Trash",
    "Scratchpad Full",
):
    if required not in guide:
        raise SystemExit(f"W92 Help integration missing: {required}")
if "risultati ricostruiti leggendo i quattro file" in guide:
    raise SystemExit("pre-W91 four-file Research narrative remains")
for required in (
    "Start with the mental model, not with the buttons",
    "First guided exercise: ten minutes from an empty document",
    "capture → clarify → connect → retrieve → insert → resolve",
    "Three realistic working scenarios",
    "A five-minute end-of-session review",
):
    if required not in guide:
        raise SystemExit(f"W92 Scratchpad learning path missing: {required}")
from calamus_help import parse_user_guide_sections
help_titles = tuple(item.title for item in parse_user_guide_sections(guide))
menu_order = (
    "Research Panel",
    "Clip Collection",
    "Scratchpad",
    "References",
    "Reference Sets",
    "Source Notes",
    "Authoring Bridge",
)
positions = tuple(help_titles.index(title) for title in menu_order)
if positions != tuple(sorted(positions)):
    raise SystemExit(f"Research Help order does not follow the menu: {positions}")
if "Tradition and memory {#tradition-and-memory}" in help_titles:
    raise SystemExit("Scratchpad example heading polluted the Help navigator")
for required in (
    "## Current command menu (W92 candidate)",
    "## Final command menu target",
    "### File",
    "### Research",
    "### Options",
    "### Final Writing",
    "### Final Research",
    "Add Tag to Selection",
    "Go to Next Tag",
    "Insert Reference Marker",
    "Insert Source Note Marker",
    "Clear Scratchpad",
    "Rename Tag…",
    "Merge Tags…",
    "Scratchpad Full is frozen until after W96",
    "A work item cannot be published",
):
    if required not in guide:
        raise SystemExit(f"W92 complete command guide missing: {required}")
help_model = (root / "calamus/calamus_help.py").read_text(encoding="utf-8")
help_dialog = (root / "calamus/calamus_help_dialogs.py").read_text(encoding="utf-8")
for required in ("class HelpTopic", "def parse_user_guide_topics", "_markdown_headings"):
    if required not in help_model:
        raise SystemExit(f"hierarchical Help model missing: {required}")
for required in (
    "Gtk.TreeStore",
    "Gtk.TreeView",
    "Guide Navigator",
    "expand_row",
    'select_help_topic(widgets, "Current command menu (W92 candidate)")',
):
    if required not in help_dialog:
        raise SystemExit(f"default Help Navigator missing: {required}")
print("W92_SCOPE_HELP_MENU_ORDER=PASS")
print("W92_SCOPE_HELP_LEARNING_CURVE=PASS")
print("W92_SCOPE_HELP_SCRATCHPAD_INTEGRATED=PASS")
print("W92_SCOPE_HELP_CURRENT_MENU_COMPLETE=PASS")
print("W92_SCOPE_HELP_FINAL_TARGET_COMPLETE=PASS")
print("W92_SCOPE_HELP_HIERARCHICAL_NAVIGATOR=PASS")

audit = root / "docs/canonical/CALAMUS_W92_RESEARCH_EFFICIENCY_AUDIT.md"
if not audit.is_file():
    raise SystemExit("W92 canonical audit is missing")
audit_text = audit.read_text(encoding="utf-8")
for required in ("Measured findings", "Direct mature-source audit", "ADAPT", "Explicit non-goals"):
    if required not in audit_text:
        raise SystemExit(f"W92 audit incomplete: {required}")
print("W92_SCOPE_MATURE_AUDIT=PASS")

version = (root / "calamus/calamus_version.py").read_text(encoding="utf-8")
if 'DEVELOPMENT_WORK_ITEM = "W92"' not in version:
    raise SystemExit("W92 identity is missing")
if 'PUBLISHED_BASELINE = "42b3c052e23ba3da0072984f40b2afd4f569c1d2"' not in version:
    raise SystemExit("published W91 baseline identity changed")
print("W92_SCOPE_IDENTITY_BASELINE=PASS")

provenance = (root / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")
if '"calamus_managed_sidecars"' not in provenance:
    raise SystemExit("new production module is not provenance tracked")
for script_name in ("prove-w92-headless-regression.sh", "prove-w92-gtk-lanes.sh"):
    script = root / "scripts" / script_name
    if not script.is_file() or not (script.stat().st_mode & 0o111):
        raise SystemExit(f"W92 gate script missing or not executable: {script_name}")
print("W92_SCOPE_GATE_SCRIPTS=PASS")
print("W92_SCOPE_GATE=PASS")
PY
