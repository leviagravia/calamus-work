#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_ROOT="${CALAMUS_W92_GTK_LOG_ROOT:-$(mktemp -d)}"
PY_CACHE="$(mktemp -d)"
TEMP_ROOT="$(mktemp -d)"
mkdir -p "$LOG_ROOT"
cleanup() { rm -rf "$PY_CACHE" "$TEMP_ROOT"; }
trap cleanup EXIT

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="$PY_CACHE"
export PYTHONPATH="$ROOT/calamus:$ROOT/tests:$ROOT"

scan_blocking() {
    local log="$1"
    for token in \
        'Gtk-CRITICAL' 'Gdk-CRITICAL' 'GLib-CRITICAL' \
        'GLib-GObject-CRITICAL' 'Traceback (most recent call last)' \
        'PyGTKDeprecationWarning' 'unversioned namespace'; do
        if grep -Fq "$token" "$log"; then
            echo "W92_GTK_LANE_BLOCKING_DIAGNOSTIC=$token"
            return 1
        fi
    done
}

run_lane() {
    local name="$1"; shift
    local lane_root="$TEMP_ROOT/$name"
    local log="$LOG_ROOT/$name.log"
    mkdir -p "$lane_root/home" "$lane_root/data" "$lane_root/config" "$lane_root/cache"
    echo "--- W92 GTK LANE: $name ---"
    set +e
    HOME="$lane_root/home" \
    XDG_DATA_HOME="$lane_root/data" \
    XDG_CONFIG_HOME="$lane_root/config" \
    XDG_CACHE_HOME="$lane_root/cache" \
    G_DEBUG=fatal-criticals \
    timeout 300s "$@" >"$log" 2>&1
    local status=$?
    set -e
    cat "$log"
    [[ "$status" -eq 0 ]] || { echo "${name}=FAIL status=$status"; return 1; }
    if grep -Eiq 'skipped|OK \(skipped=' "$log"; then
        echo "${name}=FAIL skipped-test"
        return 1
    fi
    scan_blocking "$log" || { echo "${name}=FAIL diagnostics"; return 1; }
    echo "${name}=PASS"
}

cd "$ROOT"
CALAMUS_W91_GTK_LOG_ROOT="$LOG_ROOT/historical" scripts/prove-w91-gtk-lanes.sh

declare -a PY=(python3 -B -m unittest -v)
run_lane W92_RESEARCH_SINGLE_ACTIVATION env CALAMUS_W92_RUN_REAL_GTK=1 \
    "${PY[@]}" \
    tests.test_w92_research_efficiency_app_desktop_e2e.W92ResearchEfficiencyGtkE2E.test_real_research_selector_activates_each_semantic_change_once
run_lane W92_SCRATCHPAD_REFRESH_KEYS env CALAMUS_W92_RUN_REAL_GTK=1 \
    "${PY[@]}" \
    tests.test_w92_research_efficiency_app_desktop_e2e.W92ResearchEfficiencyGtkE2E.test_real_scratchpad_refresh_button_and_list_keys_are_owned
run_lane W92_HELP_NAVIGATOR env CALAMUS_W92_RUN_REAL_GTK=1 \
    "${PY[@]}" \
    tests.test_w92_help_navigator_app_desktop_e2e.W92HelpNavigatorGtkE2E.test_real_help_opens_with_visible_hierarchical_navigator_and_menu_map
run_lane W92_HELP_HISTORICAL_GUIDE \
    "${PY[@]}" \
    tests.test_help_user_guide_app_desktop_e2e.UserGuideAppDesktopE2E.test_real_dialog_navigates_to_tag_integrity_example
run_lane W92_HELP_HISTORICAL_BIBTEX \
    "${PY[@]}" \
    tests.test_bibtex_help_app_desktop_e2e.BibtexHelpAppDesktopE2E.test_real_user_guide_navigates_to_import_and_export_examples

ACTIVATION_LOG="$LOG_ROOT/W92_RESEARCH_SINGLE_ACTIVATION.log"
for marker in \
    W92_REAL_RESEARCH_SINGLE_ACTIVATION=PASS \
    W92_REAL_RESEARCH_SELECTOR_STACK_SYNC=PASS; do
    grep -Fxq "$marker" "$ACTIVATION_LOG" || {
        echo "W92_RESEARCH_ACTIVATION_CONTRACT=FAIL missing=$marker"
        exit 1
    }
done
REFRESH_LOG="$LOG_ROOT/W92_SCRATCHPAD_REFRESH_KEYS.log"
for marker in \
    W92_REAL_SCRATCHPAD_REFRESH=PASS \
    W92_REAL_SCRATCHPAD_LIST_KEYS=PASS; do
    grep -Fxq "$marker" "$REFRESH_LOG" || {
        echo "W92_SCRATCHPAD_EFFICIENCY_CONTRACT=FAIL missing=$marker"
        exit 1
    }
done
HELP_LOG="$LOG_ROOT/W92_HELP_NAVIGATOR.log"
for marker in \
    W92_REAL_HELP_NAVIGATOR_VISIBLE=PASS \
    W92_REAL_HELP_HIERARCHY=PASS \
    W92_REAL_HELP_CURRENT_AND_FINAL_MENU=PASS; do
    grep -Fxq "$marker" "$HELP_LOG" || {
        echo "W92_HELP_NAVIGATOR_CONTRACT=FAIL missing=$marker"
        exit 1
    }
done

echo "W92_GTK_LANES_LOG_ROOT=$LOG_ROOT"
echo "W92_GTK_LANE_NO_SKIPS=PASS"
echo "W92_GTK_LANES=PASS"
