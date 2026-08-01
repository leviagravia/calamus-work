#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
export PYTHONDONTWRITEBYTECODE=1
cd "$ROOT"
./scripts/prove-w96-core-scope.sh
python3 -B -m unittest -v \
  tests.test_w96_document_dossier \
  tests.test_w96_document_overview_program
printf '%s\n' 'W96_CORE_GATE_A_HEADLESS=PASS'
