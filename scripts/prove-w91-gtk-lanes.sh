#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_ROOT="${CALAMUS_W91_GTK_LOG_ROOT:-$(mktemp -d)}"
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
            echo "W91_GTK_LANE_BLOCKING_DIAGNOSTIC=$token"
            return 1
        fi
    done
}

run_lane() {
    local name="$1"; shift
    local lane_root="$TEMP_ROOT/$name"
    local log="$LOG_ROOT/$name.log"
    mkdir -p "$lane_root/home" "$lane_root/data" "$lane_root/config" "$lane_root/cache"
    echo "--- W91 GTK LANE: $name ---"
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
CALAMUS_W90_GTK_LOG_ROOT="$LOG_ROOT/historical" scripts/prove-w90-gtk-lanes.sh

declare -a PY=(python3 -B -m unittest -v)
run_lane W91_SCRATCHPAD_TYPED_DIALOG env CALAMUS_W91_RUN_REAL_GTK=1 \
    "${PY[@]}" \
    tests.test_w91_scratchpad_app_desktop_e2e.W91ScratchpadGtkE2E.test_real_scratchpad_dialog_is_typed_owned_and_multi_section
run_lane W91_SCRATCHPAD_TRUE_APP env CALAMUS_W91_RUN_REAL_GTK=1 \
    "${PY[@]}" \
    tests.test_w91_scratchpad_app_desktop_e2e.W91ScratchpadGtkE2E.test_real_app_capture_filter_navigate_insert_and_persist

for method in \
    test_document_sidecar_renames_with_document \
    test_duplicate_managed_sidecar_is_transactional_and_preserves_source \
    test_move_to_system_trash_is_real_and_carries_managed_sidecar; do
    run_lane "W91_GIO_${method}" "${PY[@]}" \
        "tests.test_workspace_gio.WorkspaceGioAdapterTests.${method}"
done

TRUE_APP_LOG="$LOG_ROOT/W91_SCRATCHPAD_TRUE_APP.log"
for marker in \
    W91_REAL_APP_CAPTURE_SELECTION=PASS \
    W91_REAL_APP_SECTION_LINK_FILTER_NAVIGATION=PASS \
    W91_REAL_APP_INSERT_COMMAND_GATEWAY=PASS \
    W91_REAL_APP_MARKDOWN_PERSISTENCE=PASS \
    W91_REAL_APP_ARCHIVE_RELOAD=PASS; do
    grep -Fxq "$marker" "$TRUE_APP_LOG" || {
        echo "W91_TRUE_APP_CONTRACT=FAIL missing=$marker"
        exit 1
    }
done

echo "W91_GTK_LANES_LOG_ROOT=$LOG_ROOT"
echo "W91_GTK_LANE_NO_SKIPS=PASS"
echo "W91_GTK_LANES=PASS"
