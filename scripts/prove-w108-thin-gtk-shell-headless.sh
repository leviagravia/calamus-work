#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --inventory
python3 scripts/calamus-release-profiles.py --run-profile w108-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w107-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w106-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w105-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w104-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w103-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w102-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w101-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w100-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w99-headless-focused
python3 scripts/calamus-release-profiles.py --run-profile w98-headless-focused
echo "W108_THIN_GTK_SHELL_HEADLESS=PASS"
