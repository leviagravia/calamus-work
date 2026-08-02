#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --inventory
python3 scripts/calamus-release-profiles.py --run-profile w98-headless-focused
echo "W98_RESEARCH_PANEL_HEADLESS=PASS"
