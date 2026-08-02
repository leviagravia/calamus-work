#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/calamus:$ROOT"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1
: "${DISPLAY:?GTK display is required}"
export CALAMUS_W97_RUN_REAL_GTK=1
python3 -X faulthandler -u -B -m unittest -v \
  tests.test_w97_identity_app_desktop_e2e.W97CurrentIdentityRealAppE2E.test_exact_current_identity_and_stable_about
printf '%s\n' 'W97_CURRENT_IDENTITY_TRUE_APP=PASS'
python3 -X faulthandler -u -B -m unittest -v \
  tests.test_w97_bibliography_app_desktop_e2e.W97BibliographyAppDesktopE2E.test_real_app_list_detail_filters_context_file_actions_and_lifecycle
printf '%s\n' 'W97_BIBLIOGRAPHY_MANAGER_CORE_TRUE_APP=PASS'
printf '%s\n' 'W97_BIBLIOGRAPHY_MANAGER_CORE_GTK_LANES=PASS'
