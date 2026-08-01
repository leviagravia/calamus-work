#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
export PYTHONDONTWRITEBYTECODE=1
"$ROOT/scripts/prove-source-provenance.sh"
"$ROOT/scripts/prove-w95extra-scope.sh"
"$ROOT/scripts/selftest-from-source.sh"
printf '%s\n' 'W95EXTRA_HEADLESS_REGRESSION=PASS'
