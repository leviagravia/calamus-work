#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/calamus:$ROOT"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1
unset DISPLAY WAYLAND_DISPLAY CALAMUS_W97_RUN_REAL_GTK
python3 -X faulthandler -u -B -m unittest -v \
  tests.test_w97_bibliography \
  tests.test_w97_bibliography_program \
  tests.test_w97_bibliography_view_lifecycle \
  tests.test_w97_bibliography_manual_fixture \
  tests.test_w97_bibliography_wiring \
  tests.test_w97_identity_gate_contract \
  tests.test_reference_controller \
  tests.test_reference_markdown_store \
  tests.test_references \
  tests.test_reference_integrity \
  tests.test_related_references \
  tests.test_reference_sets
printf '%s\n' 'W97_BIBLIOGRAPHY_MANAGER_CORE_HEADLESS=PASS'
