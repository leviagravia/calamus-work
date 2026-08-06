#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --run-profile w101-identity-smoke
python3 scripts/calamus-release-profiles.py --run-profile w101-core-composition-smoke
python3 scripts/calamus-release-profiles.py --run-profile w99-lifecycle-smoke
python3 scripts/calamus-release-profiles.py --run-profile w98-product-smoke
echo "W101_CURRENT_IDENTITY_TRUE_APP=PASS"
echo "W101_CORE_COMPOSITION_TRUE_APP=PASS"
echo "W101_HISTORICAL_W99_LIFECYCLE=PASS"
echo "W101_HISTORICAL_W98_RESEARCH=PASS"
echo "W101_CORE_COMPOSITION_GTK_LANES=PASS"
