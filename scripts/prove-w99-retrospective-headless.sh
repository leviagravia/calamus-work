#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --inventory
python3 scripts/calamus-release-profiles.py --run-profile w99-headless-focused
echo "W99_RETROSPECTIVE_HEADLESS=PASS"
