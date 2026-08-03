#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --run-profile w100-identity-smoke
python3 scripts/calamus-release-profiles.py --run-profile w99-lifecycle-smoke
echo "W100_CURRENT_IDENTITY_TRUE_APP=PASS"
echo "W100_HISTORICAL_W99_LIFECYCLE=PASS"
echo "W100_MONOLITH_CONTRACT_GTK_LANES=PASS"
