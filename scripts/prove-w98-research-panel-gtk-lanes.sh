#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --run-profile w98-identity-smoke
python3 scripts/calamus-release-profiles.py --run-profile w98-product-smoke
echo "W98_CURRENT_IDENTITY_TRUE_APP=PASS"
echo "W98_RESEARCH_PANEL_INTEGRAL_CLOSURE_GTK_LANES=PASS"
