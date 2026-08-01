#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
export PYTHONDONTWRITEBYTECODE=1
cd "$ROOT"
./scripts/prove-source-provenance.sh
python3 -B -m unittest -v \
  tests.test_w96_document_dossier \
  tests.test_w96_document_overview_program \
  tests.test_w96_document_dossier_app \
  tests.test_w96_document_overview_runtime \
  tests.test_w96_document_overview_wiring \
  tests.test_w96_profile_owned_rebuild
printf '%s\n' 'W96_CORE_GATE_B_HEADLESS=PASS'
