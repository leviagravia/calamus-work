#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
cd "$ROOT"
LOG="${1:-$(mktemp)}"
set +e
CALAMUS_W96_RUN_REAL_GTK=0 python3 -B -m unittest -v \
  tests.test_w96_identity_app_desktop_e2e \
  tests.test_w96_document_overview_app_desktop_e2e >"$LOG" 2>&1
status=$?
set -e
cat "$LOG"
[[ "$status" -eq 0 ]]
! grep -Fq '_FailedTest' "$LOG"
! grep -Fq 'ModuleNotFoundError' "$LOG"
! grep -Fq 'ImportError' "$LOG"
grep -Eq '^Ran 2 tests? in ' "$LOG"
grep -Eq '^OK \(skipped=2\)$' "$LOG"
printf '%s
' 'CALAMUS_CANONICAL_TEST_TOPOLOGY=PASS' 'W96_EXACT_DESKTOP_MODULE_IMPORT_PREFLIGHT=PASS'
