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
    "calamus_version",
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
    "calamus_panel_chrome",
    "calamus_references",
    "calamus_reference_store",
    "calamus_reference_controller",
    "calamus_reference_panel",
    "calamus_reference_dialogs",
    "calamus_reference_runtime",
    "calamus_citations",
    "calamus_citation_controller",
    "calamus_citation_dialogs",
    "calamus_reference_integrity",
    "calamus_research_integrity_controller",
    "calamus_research_integrity_dialogs",
    "calamus_research_integrity_runtime",
    "calamus_research_file",
    "calamus_source_notes",
    "calamus_source_note_store",
    "calamus_source_note_controller",
    "calamus_source_note_panel",
    "calamus_source_note_dialogs",
    "calamus_source_note_runtime",
    "calamus_research_panel",
    "calamus_research_panel_view",
    "calamus_logging",
]

for name in modules:
    mod = __import__(name)
    path = Path(getattr(mod, "__file__", "")).resolve()
    print(f"{name}: {path}")
    if not str(path).startswith(str(expected_lib) + os.sep):
        raise SystemExit(f"FATAL: {name} imported from wrong path: {path}")

print("SOURCE_PROVENANCE=PASS")
PY
