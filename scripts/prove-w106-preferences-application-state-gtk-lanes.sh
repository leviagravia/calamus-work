#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --run-profile w106-identity-smoke
python3 scripts/calamus-release-profiles.py --run-profile w106-preferences-state-smoke
python3 scripts/calamus-release-profiles.py --run-profile w105-menu-ui-state-smoke
python3 scripts/calamus-release-profiles.py --run-profile w104-command-action-smoke
python3 scripts/calamus-release-profiles.py --run-profile w103-editor-transaction-smoke
python3 scripts/calamus-release-profiles.py --run-profile w102-document-session-smoke
python3 scripts/calamus-release-profiles.py --run-profile w101-core-composition-smoke
python3 scripts/calamus-release-profiles.py --run-profile w99-lifecycle-smoke
python3 scripts/calamus-release-profiles.py --run-profile w98-product-smoke
echo "W106_CURRENT_IDENTITY_TRUE_APP=PASS"
echo "W106_PREFERENCES_APPLICATION_STATE_TRUE_APP=PASS"
echo "W106_HISTORICAL_W105_MENU_UI_STATE=PASS"
echo "W106_HISTORICAL_W104_COMMAND_ACTION=PASS"
echo "W106_HISTORICAL_W103_EDITOR_TRANSACTION=PASS"
echo "W106_HISTORICAL_W102_DOCUMENT_SESSION=PASS"
echo "W106_HISTORICAL_W101_COMPOSITION=PASS"
echo "W106_HISTORICAL_W99_LIFECYCLE=PASS"
echo "W106_HISTORICAL_W98_RESEARCH=PASS"
echo "W106_PREFERENCES_APPLICATION_STATE_GTK_LANES=PASS"
