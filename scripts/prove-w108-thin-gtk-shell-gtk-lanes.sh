#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/calamus-release-profiles.py --run-profile w108-identity-smoke
python3 scripts/calamus-release-profiles.py --run-profile w108-thin-gtk-shell-smoke
python3 scripts/calamus-release-profiles.py --run-profile w107-subsystem-host-port-smoke
python3 scripts/calamus-release-profiles.py --run-profile w106-preferences-state-smoke
python3 scripts/calamus-release-profiles.py --run-profile w105-menu-ui-state-smoke
python3 scripts/calamus-release-profiles.py --run-profile w104-command-action-smoke
python3 scripts/calamus-release-profiles.py --run-profile w103-editor-transaction-smoke
python3 scripts/calamus-release-profiles.py --run-profile w102-document-session-smoke
python3 scripts/calamus-release-profiles.py --run-profile w101-core-composition-smoke
python3 scripts/calamus-release-profiles.py --run-profile w99-lifecycle-smoke
python3 scripts/calamus-release-profiles.py --run-profile w98-product-smoke
echo "W108_CURRENT_IDENTITY_TRUE_APP=PASS"
echo "W108_THIN_GTK_SHELL_TRUE_APP=PASS"
echo "W108_HISTORICAL_W107_SUBSYSTEM_HOST_PORT=PASS"
echo "W108_HISTORICAL_W106_PREFERENCES_STATE=PASS"
echo "W108_HISTORICAL_W105_MENU_UI_STATE=PASS"
echo "W108_HISTORICAL_W104_COMMAND_ACTION=PASS"
echo "W108_HISTORICAL_W103_EDITOR_TRANSACTION=PASS"
echo "W108_HISTORICAL_W102_DOCUMENT_SESSION=PASS"
echo "W108_HISTORICAL_W101_COMPOSITION=PASS"
echo "W108_HISTORICAL_W99_LIFECYCLE=PASS"
echo "W108_HISTORICAL_W98_RESEARCH=PASS"
echo "W108_THIN_GTK_SHELL_GTK_LANES=PASS"
