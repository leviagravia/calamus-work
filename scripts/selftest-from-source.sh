#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CALAMUS_LIB_DIR="$ROOT/calamus"
export CALAMUS_TEST_DIR="$ROOT/tests"
export CALAMUS_SOURCE_ROOT="$ROOT"
export PYTHONPATH="$ROOT/calamus"
export PYTHONDONTWRITEBYTECODE=1
TMP_HOME="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_HOME"
}
trap cleanup EXIT
export HOME="$TMP_HOME"
export XDG_CONFIG_HOME="$TMP_HOME/.config"

"$ROOT/scripts/prove-source-provenance.sh"
python3 -B "$ROOT/bin/calamus-selftest" --full
