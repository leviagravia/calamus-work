#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --inventory
python3 scripts/calamus-release-profiles.py --run-profile w102-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w101-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w100-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w99-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w98-headless-focused
echo "W102_DOCUMENT_SESSION_HEADLESS=PASS"
