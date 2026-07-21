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
