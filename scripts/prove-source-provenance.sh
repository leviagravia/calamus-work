#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CALAMUS_LIB_DIR="$ROOT/calamus"
export CALAMUS_TEST_DIR="$ROOT/tests"
export CALAMUS_SOURCE_ROOT="$ROOT"
export PYTHONPATH="$ROOT/calamus"
export PYTHONDONTWRITEBYTECODE=1
python3 -B - "$ROOT" <<'PY'
import os
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
expected_lib = root / "calamus"

sys.path.insert(0, str(expected_lib))

modules = [
    "calamus_document",
    "calamus_model",
    "calamus_commands",
    "calamus_state",
    "calamus_ui",
    "calamus_dialogs",
    "calamus_help",
    "calamus_help_dialogs",
    "calamus_version",
    "calamus_runtime_identity",
    "calamus_identity_dialogs",
    "calamus_shortcuts",
    "calamus_editor",
    "calamus_layout",
    "calamus_line_numbers",
    "calamus_line_numbers_gateway",
    "calamus_search",
    "calamus_search_gateway",
    "calamus_search_view",
    "calamus_search_dialogs",
    "calamus_clips",
    "calamus_clip_collection",
    "calamus_clip_panel",
    "calamus_right_panel",
    "calamus_document_structure",
    "calamus_navigation_gateway",
    "calamus_navigation_view",
    "calamus_navigation_dialogs",
    "calamus_navigator_panel",
    "calamus_navigator_panel_view",
    "calamus_left_panel",
    "calamus_workspace",
    "calamus_workspace_controller",
    "calamus_workspace_application",
    "calamus_workspace_menu",
    "calamus_workspace_external",
    "calamus_workspace_tree",
    "calamus_workspace_panel",
    "calamus_workspace_operations",
    "calamus_workspace_gio",
    "calamus_workspace_mutation",
    "calamus_workspace_identity",
    "calamus_panel_chrome",
    "calamus_references",
    "calamus_reference_store",
    "calamus_reference_controller",
    "calamus_reference_panel",
    "calamus_reference_dialogs",
    "calamus_reference_runtime",
    "calamus_modal_dialog",
    "calamus_related_references",
    "calamus_related_reference_dialogs",
    "calamus_reference_sets",
    "calamus_reference_set_store",
    "calamus_reference_set_controller",
    "calamus_reference_set_view",
    "calamus_reference_set_dialogs",
    "calamus_reference_set_runtime",
    "calamus_citations",
    "calamus_citation_controller",
    "calamus_citation_dialogs",
    "calamus_reference_integrity",
    "calamus_research_integrity_controller",
    "calamus_research_integrity_dialogs",
    "calamus_research_integrity_runtime",
    "calamus_tag_integrity",
    "calamus_tag_integrity_controller",
    "calamus_tag_integrity_dialogs",
    "calamus_tag_integrity_runtime",
    "calamus_tags_controller",
    "calamus_tags_panel",
    "calamus_tags_runtime",
    "calamus_bibtex",
    "calamus_bibtex_import_session",
    "calamus_bibtex_import_view",
    "calamus_bibtex_controller",
    "calamus_bibtex_dialogs",
    "calamus_bibtex_runtime",
    "calamus_research_file",
    "calamus_managed_sidecars",
    "calamus_source_notes",
    "calamus_source_note_store",
    "calamus_source_note_controller",
    "calamus_source_note_panel",
    "calamus_source_note_dialogs",
    "calamus_source_note_runtime",
    "calamus_scratchpad",
    "calamus_scratchpad_store",
    "calamus_scratchpad_controller",
    "calamus_scratchpad_panel",
    "calamus_scratchpad_dialogs",
    "calamus_scratchpad_runtime",
    "calamus_scratchpad_gateway",
    "calamus_authoring_bridge",
    "calamus_authoring_bridge_controller",
    "calamus_authoring_bridge_view",
    "calamus_authoring_bridge_dialogs",
    "calamus_authoring_bridge_runtime",
    "calamus_research_panel",
    "calamus_research_panel_view",
    "calamus_pandoc",
    "calamus_pandoc_process",
    "calamus_pandoc_controller",
    "calamus_pandoc_dialogs",
    "calamus_pandoc_runtime",
    "calamus_logging",
]

import importlib.util

for name in modules:
    spec = importlib.util.find_spec(name)
    if spec is None or not spec.origin:
        raise SystemExit(f"FATAL: source spec unavailable: {name}")
    path = Path(spec.origin).resolve()
    if not str(path).startswith(str(expected_lib) + os.sep):
        raise SystemExit(f"FATAL: {name} resolved from wrong path: {path}")
    try:
        mod = __import__(name)
    except ModuleNotFoundError as error:
        if error.name != "gi":
            raise
        print(f"{name}: {path} [IMPORT SKIP: PyGObject unavailable]")
    else:
        imported = Path(getattr(mod, "__file__", "")).resolve()
        if imported != path:
            raise SystemExit(f"FATAL: {name} imported from wrong path: {imported}")
        print(f"{name}: {imported}")

print("SOURCE_PROVENANCE=PASS")
PY
