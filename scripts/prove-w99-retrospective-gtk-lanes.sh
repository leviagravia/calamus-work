#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --run-profile w99-identity-smoke
python3 scripts/calamus-release-profiles.py --run-profile w99-lifecycle-smoke
echo "W99_CURRENT_IDENTITY_TRUE_APP=PASS"
echo "W99_RETROSPECTIVE_GTK_LANES=PASS"
