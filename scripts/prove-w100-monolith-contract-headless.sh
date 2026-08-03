#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --inventory
python3 scripts/calamus-release-profiles.py --run-profile w100-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w99-headless-focused
echo "W100_MONOLITH_DECOMPOSITION_CONTRACT_HEADLESS=PASS"
