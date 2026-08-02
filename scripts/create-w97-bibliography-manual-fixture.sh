#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
[[ "$#" -eq 1 ]] || { echo "usage: $0 DOCUMENT" >&2; exit 2; }
python3 -B -m tests.w97_bibliography_manual_fixture "$1"
