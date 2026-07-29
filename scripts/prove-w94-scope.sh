#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/calamus:$ROOT/tests:$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python3 -B - "$ROOT" <<'PY'
from __future__ import annotations
import ast
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()

pure = (
    "calamus_tag_integrity.py",
    "calamus_tag_integrity_controller.py",
    "calamus_tags_controller.py",
)
for name in pure:
    path = root / "calamus" / name
    if not path.is_file():
        raise SystemExit(f"missing W94 pure module: {name}")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    if any(item == "gi" or item.startswith("gi.") for item in imports):
        raise SystemExit(f"GTK leaked into pure W94 module: {name}")
    if any(symbol in source for symbol in ("Gtk.", "Gdk.", "GLib.", "Pango.")):
        raise SystemExit(f"GTK symbol leaked into pure W94 module: {name}")
print("W94_SCOPE_PURE_GTK_FREE=PASS")

model = (root / "calamus/calamus_tag_integrity.py").read_text(encoding="utf-8")
controller = (root / "calamus/calamus_tag_integrity_controller.py").read_text(encoding="utf-8")
for required in (
    'TAG_SCOPE_ALL = "all"', 'TAG_SCOPE_SCRATCHPAD = "scratchpad"',
    "scratchpad_uses", "scratchpad_entries_changed", "scratchpad_before",
    "scratchpad_after", "authority_in_scope",
):
    if required not in model:
        raise SystemExit(f"three-authority pure contract missing: {required}")
for required in (
    "scratchpad_store_factory", "scratchpad_token", "_rollback_after_scratchpad_failure",
    "refresh_scratchpad", "scope=approved_plan.impact.scope",
):
    if required not in controller:
        raise SystemExit(f"three-authority transaction contract missing: {required}")
if "force=True" in controller:
    raise SystemExit("W94 transaction bypasses stale protection")
print("W94_SCOPE_THREE_AUTHORITIES_TRANSACTION=PASS")

panel = (root / "calamus/calamus_tags_panel.py").read_text(encoding="utf-8")
runtime = (root / "calamus/calamus_tags_runtime.py").read_text(encoding="utf-8")
for required in (
    'set_name("tags-panel")', 'set_name("tags-search")', 'set_name("tags-scope")',
    'set_name("tags-sort")', 'Name (A–Z)', 'Most used',
    'set_name("tags-show-all-az")', 'label="All tags A–Z"',
    'label="Variants only"', 'set_name("tags-list")',
    'set_name("tag-uses-list")', 'Gtk.ListBox()',
    'item.total_count', 'item.reference_count', 'item.source_note_count',
    'item.scratchpad_count', 'label="Open"',
    'label="Rename / Merge…"', 'label="Remove…"', 'label="Normalize All…"',
    'label="Refresh"',
):
    if required not in panel:
        raise SystemExit(f"Tags panel contract missing: {required}")
for required in ("TagsController", "confirm_tag_mutation", "show_tag_result", "controller.set_sort"):
    if required not in runtime:
        raise SystemExit(f"Tags runtime contract missing: {required}")
tags_controller = (root / "calamus/calamus_tags_controller.py").read_text(encoding="utf-8")
for required in ('TAG_SORT_NAME = "name"', 'TAG_SORT_USAGE = "usage"', 'def set_sort(', 'def _visible_sort_key('):
    if required not in tags_controller:
        raise SystemExit(f"Tags derived sort/ranking contract missing: {required}")
print("W94_SCOPE_TAGS_PANEL=PASS")
print("W94_SCOPE_DERIVED_SORT_AND_SEARCH_RANK=PASS")

controller_tree = ast.parse(tags_controller, filename=str(root / "calamus/calamus_tags_controller.py"))
protocol = next(
    node for node in controller_tree.body
    if isinstance(node, ast.ClassDef) and node.name == "TagsView"
)
protocol_members = {
    node.name for node in protocol.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
expected_view_members = {
    "widget", "render_tags", "render_uses", "selected_tag_identity",
    "selected_use", "set_query", "set_scope", "set_issues_only", "set_sort",
}
if protocol_members != expected_view_members:
    raise SystemExit(
        f"W94 consumer-driven TagsView contract mismatch: {sorted(protocol_members)}"
    )
if "focus_search" in tags_controller:
    raise SystemExit("stale focus_search leaked into the GTK-free Tags controller contract")
panel_tree = ast.parse(panel, filename=str(root / "calamus/calamus_tags_panel.py"))
adapter = next(
    node for node in panel_tree.body
    if isinstance(node, ast.ClassDef) and node.name == "TagsPanelViewAdapter"
)
adapter_methods = {
    node.name for node in adapter.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
if not (expected_view_members - {"widget"}).issubset(adapter_methods):
    raise SystemExit("concrete Tags adapter does not satisfy controller surface")
if not {"_queue_selection_sync", "_run_deferred_selection"}.issubset(adapter_methods):
    raise SystemExit("Tags post-map selection lifecycle is missing from the concrete adapter")
if {"queue_activation_focus", "focus_search"} & adapter_methods:
    raise SystemExit("Tags activation focus leaked back into the concrete adapter")
if "grab_focus" in panel or "queue_activation_focus" in runtime or "grab_focus" in runtime:
    raise SystemExit("Tags activation must not steal focus")
print("W94_SCOPE_CONSUMER_DRIVEN_VIEW_CONTRACT=PASS")

app = (root / "bin/calamus").read_text(encoding="utf-8")
ui = (root / "calamus/calamus_ui.py").read_text(encoding="utf-8")
if app.count('("tags", "Tags", self.tags_runtime.widget, self.tags_runtime.activate)') != 1:
    raise SystemExit("Tags Research client is not registered exactly once")
if 'self.research_panel_view.register_client(*client)' not in app:
    raise SystemExit("Research client registry loop is missing")
if 'def show_tags(self, *_):\n        return self.research_panel_runtime.show("tags")' not in app:
    raise SystemExit("thin App Tags command missing")
if ui.count('add_item(researchm, "Tags", app.show_tags)') != 1:
    raise SystemExit("Research menu Tags command missing or duplicated")
print("W94_SCOPE_REAL_APP_WIRING=PASS")

guide = (root / "share/doc/calamus/USER_GUIDE.md").read_text(encoding="utf-8")
for required in (
    "## Current command menu (W94 candidate)", "## Tags",
    "### Tutorial: build a useful tag vocabulary from one article",
    "### First guided exercise", "All tags A–Z", "Name (A–Z)", "Most used",
    "Three daily workflows", "A good stopping rule",
    "Variants only", "Rename / Merge", "Normalize All",
    "three readable Markdown authorities", "Mode: Rename", "Mode: Merge",
    "Mode: Normalize spelling", "Tag Integrity", "Scratchpad Full",
    "Only the logical variants of `Faith` become `doctrine`",
    "unrelated tags such as `church history` and `temporary` remain unchanged",
    "The active document remains byte-identical.",
    "Relationship with the W94 Tags client",
):
    if required not in guide:
        raise SystemExit(f"W94 Help contract missing: {required}")
if guide.index("## Tags") > guide.index("## Related References"):
    raise SystemExit("Tags Help topic is not in Research command order")
from calamus_help import parse_user_guide_sections
published_tag_integrity = '`Research → Tag Integrity…` builds a transient inventory from References and the current document Source Notes. It does not scan or rewrite the document text.\n\nLogical identity uses Unicode NFC normalization, collapsed whitespace and case-insensitive comparison. Therefore `Faith`, `faith`, ` FAITH ` and Unicode-equivalent spellings are treated as variants of one logical tag.\n\nAvailable operations:\n\n- `Show Uses`: list the exact References and Source Notes that use the selected tag.\n- `Rename / Merge…`: rename all selected variants in the chosen scope; if the target already exists, duplicates are merged.\n- `Remove Everywhere…`: remove the selected logical tag in the chosen scope.\n- `Normalize All…`: rewrite variant spellings to the first canonical display spelling.\n\nScopes are `References and Source Notes`, `References only`, and `Current Source Notes only`.\n\nPractical example: the current Reference has tags `Faith`, `church history`, `temporary`; a Source Note has `FAITH`, `church history`, `temporary`. Select `Faith`, choose `Rename / Merge…`, enter `doctrine`, review the impact preview and confirm. Only the logical variants of `Faith` become `doctrine`; unrelated tags such as `church history` and `temporary` remain unchanged. The active document remains byte-identical.\n\nThe colour swatch is deterministic and derived from tag identity. It is presentation only: it is not stored in References or Source Notes and cannot create a colour-only tag.'
tag_integrity = next(
    section for section in parse_user_guide_sections(guide)
    if section.title == "Tag Integrity"
)
if not tag_integrity.body.startswith(published_tag_integrity):
    raise SystemExit("published W92 Tag Integrity Help contract was not preserved verbatim")
print("W94_SCOPE_PUBLISHED_HELP_COMPATIBILITY=PASS")
print("W94_SCOPE_HELP=PASS")

for forbidden in ("sqlite3", "CREATE TABLE", "watchdog", "knowledge graph", "auto-tagging"):
    production = "\n".join((root / "calamus" / name).read_text(encoding="utf-8") for name in (
        "calamus_tag_integrity.py", "calamus_tag_integrity_controller.py",
        "calamus_tags_controller.py", "calamus_tags_panel.py", "calamus_tags_runtime.py",
    ))
    if forbidden in production.lower():
        raise SystemExit(f"forbidden W94 architecture leaked: {forbidden}")
print("W94_SCOPE_NO_HIDDEN_AUTHORITY=PASS")

version = (root / "calamus/calamus_version.py").read_text(encoding="utf-8")
if 'DEVELOPMENT_WORK_ITEM = "W94"' not in version:
    raise SystemExit("W94 identity missing")
if 'PUBLISHED_BASELINE = "1e8cd2c584eb3f28c814f0dee433aaf7ae580f51"' not in version:
    raise SystemExit("W92 published baseline identity missing")
print("W94_SCOPE_IDENTITY_BASELINE=PASS")

audit = root / "docs/canonical/CALAMUS_W94_TAGS_AUDIT.md"
if not audit.is_file():
    raise SystemExit("W94 canonical audit missing")
text = audit.read_text(encoding="utf-8")
for required in (
    "Direct mature-source audit", "ADOPT", "ADAPT", "REJECT", "Explicit exclusions",
    "nemo-tags", "Tagsistant", "TagStudio", "TMSU", "Failure-driven R2 decisions", "Post-R5 suspension audit and unitary reconstruction", "Rebuilt R1 True-App constructor failure", "Rebuilt R2 persistent GtkRange failure and Rebuilt R3 staged selection redesign",
):
    if required not in text:
        raise SystemExit(f"W94 audit incomplete: {required}")
for name in ("prove-w94-headless-regression.sh", "prove-w94-gtk-lanes.sh"):
    path = root / "scripts" / name
    if not path.is_file() or not (path.stat().st_mode & 0o111):
        raise SystemExit(f"W94 gate script missing/not executable: {name}")
print("W94_SCOPE_MATURE_AUDIT=PASS")

gtk_test_path = root / "tests/test_w94_tags_app_desktop_e2e.py"
gtk_test_source = gtk_test_path.read_text(encoding="utf-8")
gtk_test_tree = ast.parse(gtk_test_source, filename=str(gtk_test_path))
named_widget_calls = [
    node for node in ast.walk(gtk_test_tree)
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "named_widget"
]
if not named_widget_calls:
    raise SystemExit("W94 GTK test does not exercise semantic widget lookup")
for call in named_widget_calls:
    if len(call.args) != 3 or call.keywords:
        raise SystemExit(
            f"W94 GTK named_widget contract mismatch at line {call.lineno}: "
            "expected widget, name, widget_type"
        )
for required in (
    '("tags-search", Gtk.SearchEntry)',
    '("tags-show-all-az", Gtk.Button)',
    '("tags-scope", Gtk.ComboBoxText)',
    '("tags-sort", Gtk.ComboBoxText)',
    '("tags-issues-only", Gtk.CheckButton)',
    '("tags-list", Gtk.ListBox)',
    '("tag-uses-list", Gtk.ListBox)',
    '("tags-open", Gtk.Button)',
    '("tags-rename", Gtk.Button)',
    '("tags-refresh", Gtk.Button)',
    '("tags-remove", Gtk.Button)',
    '("tags-normalize", Gtk.Button)',
):
    if required not in gtk_test_source:
        raise SystemExit(f"W94 typed GTK widget map incomplete: {required}")
contract_test = root / "tests/test_w94_gtk_widget_contract.py"
if not contract_test.is_file():
    raise SystemExit("W94 headless GTK widget contract test missing")
print("W94_SCOPE_TYPED_GTK_WIDGET_CONTRACT=PASS")

for forbidden in ("Gtk.TreeView", "Gtk.ListStore", "scroll_to_cell", "get_vadjustment", "get_adjustment"):
    if forbidden in panel:
        raise SystemExit(f"W94 Tags viewport-free contract violated: {forbidden}")
for required in (
    'self.widget.connect("unmap", self._on_unmap)',
    'self.widget.connect("destroy", self._on_destroy)',
    'self.widget.connect(\n                "map", self._on_map_for_selection',
    'GLib.idle_add(self._run_deferred_selection)',
    'GLib.source_remove(self._selection_source_id)',
):
    if required not in panel:
        raise SystemExit(f"W94 lifecycle contract missing: {required}")
render_tree = ast.parse(panel, filename=str(root / "calamus/calamus_tags_panel.py"))
render_methods = {
    node.name: node for node in ast.walk(render_tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
for render_name in ("render_tags", "render_uses"):
    calls = {
        node.func.attr for node in ast.walk(render_methods[render_name])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    if "select_row" in calls or "grab_focus" in calls:
        raise SystemExit(f"W94 synchronous selection/focus leaked into {render_name}")
if "grab_focus" in panel or "queue_activation_focus" in panel or "queue_activation_focus" in runtime:
    raise SystemExit("W94 Tags activation focus must remain absent")
lifecycle_test = root / "tests/test_w94_tags_view_lifecycle_contract.py"
if not lifecycle_test.is_file():
    raise SystemExit("W94 headless lifecycle contract test missing")
print("W94_SCOPE_VIEWPORT_FREE_LISTBOX=PASS")
print("W94_SCOPE_POST_MAP_SELECTION=PASS")
print("W94_SCOPE_NO_ACTIVATION_FOCUS=PASS")

right_host = (root / "calamus/calamus_right_panel.py").read_text(encoding="utf-8")
for required in (
    "self._paned.pack2(widget, False, True)",
    "widget.set_size_request(-1, -1)",
    "self._remember_current_width()",
    "bound_right_panel_width",
):
    if required not in right_host:
        raise SystemExit(f"W94 right-panel resize contract missing: {required}")
if "self._paned.pack2(widget, False, False)" in right_host:
    raise SystemExit("W94 right panel still disables shrink")
for required in (
    "set_propagate_natural_width(False)",
    "set_min_content_width(1)",
    'label="All tags A–Z"',
    'sort.append(TAG_SORT_NAME, "Name (A–Z)")',
):
    if required not in panel:
        raise SystemExit(f"W94 responsive Tags contract missing: {required}")
print("W94_SCOPE_RESEARCH_RESIZE_REOPEN=PASS")
print("W94_SCOPE_TAGS_RESPONSIVE_LAYOUT=PASS")
print("W94_SCOPE_ALL_TAGS_AZ=PASS")

gtk_gate = (root / "scripts" / "prove-w94-gtk-lanes.sh").read_text(encoding="utf-8")
for required in (
    'return 0',
    '--self-test-diagnostics',
    'W94_GTK_DIAGNOSTIC_SCANNER_SELFTEST=PASS',
):
    if required not in gtk_gate:
        raise SystemExit(f"W94 gate diagnostic contract missing: {required}")
ordered_lanes = (
    "run_lane W94_TAGS_RUNTIME_CONTRACT",
    "run_lane W94_TAGS_APP_CONSTRUCT",
    "run_lane W94_TAGS_APP_MAP",
    "run_lane W94_TAGS_APP_OPEN",
    "run_lane W94_TAGS_APP_ACTIVATE",
    "run_lane W94_RESEARCH_RESIZE_REOPEN",
    "run_lane W94_TAGS_TRUE_APP",
    "run_lane W94_TAGS_PANEL",
)
positions = tuple(gtk_gate.index(value) for value in ordered_lanes)
if positions != tuple(sorted(positions)):
    raise SystemExit("W94 staged true-App lanes are not in risk-first order")
for required in ("capture_native_backtrace", "W94_STAGED_TRUE_APP_LANES=PASS"):
    if required not in gtk_gate:
        raise SystemExit(f"W94 diagnostic staging contract missing: {required}")
print("W94_SCOPE_DIAGNOSTIC_SCANNER_CONTRACT=PASS")
print("W94_SCOPE_RUNTIME_CONTRACT_RISK_FIRST=PASS")
print("W94_SCOPE_STAGED_TRUE_APP=PASS")
print("W94_SCOPE_TRUE_APP_RISK_FIRST=PASS")
print("W94_SCOPE_GATE=PASS")
PY
