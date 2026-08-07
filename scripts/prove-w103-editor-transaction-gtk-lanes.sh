#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --run-profile w103-identity-smoke
python3 scripts/calamus-release-profiles.py --run-profile w103-editor-transaction-smoke
python3 scripts/calamus-release-profiles.py --run-profile w102-document-session-smoke
python3 scripts/calamus-release-profiles.py --run-profile w101-core-composition-smoke
python3 scripts/calamus-release-profiles.py --run-profile w99-lifecycle-smoke
python3 scripts/calamus-release-profiles.py --run-profile w98-product-smoke
echo "W103_CURRENT_IDENTITY_TRUE_APP=PASS"
echo "W103_EDITOR_TRANSACTION_TRUE_APP=PASS"
echo "W103_HISTORICAL_W102_DOCUMENT_SESSION=PASS"
echo "W103_HISTORICAL_W101_COMPOSITION=PASS"
echo "W103_HISTORICAL_W99_LIFECYCLE=PASS"
echo "W103_HISTORICAL_W98_RESEARCH=PASS"
echo "W103_EDITOR_TRANSACTION_GTK_LANES=PASS"
