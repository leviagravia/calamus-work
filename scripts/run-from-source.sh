#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CALAMUS_LIB_DIR="$ROOT/calamus"
export CALAMUS_SOURCE_ROOT="$ROOT"
export PYTHONPATH="$ROOT/calamus"
export PYTHONDONTWRITEBYTECODE=1
"$ROOT/scripts/prove-source-provenance.sh"
exec python3 -B "$ROOT/bin/calamus" "$@"
