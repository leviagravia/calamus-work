#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CALAMUS_SOURCE_ROOT="$ROOT"
export CALAMUS_LIB_DIR="$ROOT/calamus"
export CALAMUS_TEST_DIR="$ROOT/tests"
export PYTHONPATH="$ROOT/calamus"
export PYTHONDONTWRITEBYTECODE=1
"$ROOT/scripts/prove-source-provenance.sh"
"$ROOT/scripts/prove-w95extra-scope.sh"
"$ROOT/scripts/selftest-from-source.sh"
printf '%s\n' 'W95EXTRA_HEADLESS_REGRESSION=PASS'
