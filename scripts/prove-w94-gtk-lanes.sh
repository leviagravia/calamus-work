#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_ROOT="${CALAMUS_W94_GTK_LOG_ROOT:-$(mktemp -d)}"
PY_CACHE="$(mktemp -d)"
TEMP_ROOT="$(mktemp -d)"
mkdir -p "$LOG_ROOT"
cleanup() { rm -rf "$PY_CACHE" "$TEMP_ROOT"; }
trap cleanup EXIT
export PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$PY_CACHE"
export PYTHONPATH="$ROOT/calamus:$ROOT/tests:$ROOT"

scan_blocking() {
  local log="$1"
  local token
  for token in 'Gtk-CRITICAL' 'Gdk-CRITICAL' 'GLib-CRITICAL' 'GLib-GObject-CRITICAL' \
   'Traceback (most recent call last)' 'PyGTKDeprecationWarning' 'unversioned namespace'; do
    if grep -Fq "$token" "$log"; then
      echo "W94_GTK_LANE_BLOCKING_DIAGNOSTIC=$token"
      return 1
    fi
  done
  return 0
}

capture_native_backtrace() {
  local name="$1" lane_root="$2"; shift 2
  local backtrace="$LOG_ROOT/${name}.gdb.log"
  if ! command -v gdb >/dev/null 2>&1; then
    echo "${name}_NATIVE_BACKTRACE=UNAVAILABLE_NO_GDB"
    return 0
  fi
  echo "--- W94 NATIVE BACKTRACE: $name ---"
  set +e
  HOME="$lane_root/home" XDG_DATA_HOME="$lane_root/data" XDG_CONFIG_HOME="$lane_root/config" \
  XDG_CACHE_HOME="$lane_root/cache" G_DEBUG=fatal-criticals \
    timeout 180s gdb --batch \
      -ex 'set pagination off' \
      -ex 'set confirm off' \
      -ex 'handle SIGTRAP stop print nopass' \
      -ex run \
      -ex 'thread apply all bt full' \
      -ex 'info registers' \
      --args "$@" >"$backtrace" 2>&1
  set -e
  cat "$backtrace"
  echo "${name}_NATIVE_BACKTRACE=$backtrace"
}

run_lane() {
  local name="$1"; shift
  local lane_root="$TEMP_ROOT/$name" log="$LOG_ROOT/$name.log"
  mkdir -p "$lane_root/home" "$lane_root/data" "$lane_root/config" "$lane_root/cache"
  echo "--- W94 GTK LANE: $name ---"
  set +e
  HOME="$lane_root/home" XDG_DATA_HOME="$lane_root/data" XDG_CONFIG_HOME="$lane_root/config" \
  XDG_CACHE_HOME="$lane_root/cache" G_DEBUG=fatal-criticals timeout 300s "$@" >"$log" 2>&1
  local status=$?
  set -e
  cat "$log"
  if [[ "$status" -ne 0 ]]; then
    if [[ "$status" -eq 133 || "$status" -eq 134 ]]; then
      capture_native_backtrace "$name" "$lane_root" "$@"
    fi
    echo "${name}=FAIL status=$status"
    return 1
  fi
  grep -Eiq 'skipped|OK \(skipped=' "$log" && { echo "${name}=FAIL skipped-test"; return 1; }
  scan_blocking "$log" || { echo "${name}=FAIL diagnostics"; return 1; }
  echo "${name}=PASS"
}

selftest_diagnostic_scanner() {
  local clean_log="$TEMP_ROOT/diagnostic-clean.log"
  local blocked_log="$TEMP_ROOT/diagnostic-blocked.log"
  : >"$clean_log"
  printf '%s\n' 'Gtk-CRITICAL synthetic self-test' >"$blocked_log"

  if ! scan_blocking "$clean_log" >/dev/null; then
    echo "W94_GTK_DIAGNOSTIC_SCANNER_CLEAN=FAIL"
    return 1
  fi
  if scan_blocking "$blocked_log" >/dev/null; then
    echo "W94_GTK_DIAGNOSTIC_SCANNER_BLOCKED=FAIL"
    return 1
  fi
  echo "W94_GTK_DIAGNOSTIC_SCANNER_CLEAN=PASS"
  echo "W94_GTK_DIAGNOSTIC_SCANNER_BLOCKED=PASS"
  echo "W94_GTK_DIAGNOSTIC_SCANNER_SELFTEST=PASS"
}

if [[ "${1:-}" == "--self-test-diagnostics" ]]; then
  selftest_diagnostic_scanner
  exit $?
fi

cd "$ROOT"
PY=(python3 -B -m unittest -v)

# Risk-first order: published Help, concrete runtime, then separate true-App
# lifecycle stages. Each stage runs in its own process so a native GTK abort is
# attributed to construction, mapping, document opening or Tags activation.
run_lane W94_HELP_COMPATIBILITY_PREFLIGHT "${PY[@]}" \
 tests.test_help_user_guide_app_desktop_e2e.UserGuideAppDesktopE2E.test_real_dialog_navigates_to_tag_integrity_example
run_lane W94_TAGS_RUNTIME_CONTRACT env CALAMUS_W94_RUN_REAL_GTK=1 "${PY[@]}" \
 tests.test_w94_tags_app_desktop_e2e.W94TagsGtkE2E.test_real_tags_runtime_accepts_the_concrete_consumer_driven_view
run_lane W94_TAGS_APP_CONSTRUCT env CALAMUS_W94_RUN_REAL_GTK=1 "${PY[@]}" \
 tests.test_w94_tags_app_desktop_e2e.W94TagsGtkE2E.test_true_app_constructs_with_tags_client
run_lane W94_TAGS_APP_MAP env CALAMUS_W94_RUN_REAL_GTK=1 "${PY[@]}" \
 tests.test_w94_tags_app_desktop_e2e.W94TagsGtkE2E.test_true_app_maps_before_tags_activation
run_lane W94_TAGS_APP_OPEN env CALAMUS_W94_RUN_REAL_GTK=1 "${PY[@]}" \
 tests.test_w94_tags_app_desktop_e2e.W94TagsGtkE2E.test_true_app_opens_document_before_tags_activation
run_lane W94_TAGS_APP_ACTIVATE env CALAMUS_W94_RUN_REAL_GTK=1 "${PY[@]}" \
 tests.test_w94_tags_app_desktop_e2e.W94TagsGtkE2E.test_true_app_activates_tags_with_post_map_selection_and_no_focus_steal
run_lane W94_RESEARCH_RESIZE_REOPEN env CALAMUS_W94_RUN_REAL_GTK=1 "${PY[@]}" \
 tests.test_w94_tags_app_desktop_e2e.W94TagsGtkE2E.test_true_app_research_panel_remembers_width_and_remains_resizable_after_reopen
run_lane W94_TAGS_TRUE_APP env CALAMUS_W94_RUN_REAL_GTK=1 "${PY[@]}" \
 tests.test_w94_tags_app_desktop_e2e.W94TagsGtkE2E.test_true_app_projects_navigates_and_renames_three_markdown_authorities
run_lane W94_TAGS_PANEL env CALAMUS_W94_RUN_REAL_GTK=1 "${PY[@]}" \
 tests.test_w94_tags_app_desktop_e2e.W94TagsGtkE2E.test_real_tags_panel_owns_filters_counts_uses_and_actions

CALAMUS_W92_GTK_LOG_ROOT="$LOG_ROOT/historical" scripts/prove-w92-gtk-lanes.sh

grep -Fxq "W86_REAL_RESEARCH_EXAMPLE=PASS" "$LOG_ROOT/W94_HELP_COMPATIBILITY_PREFLIGHT.log" || {
  echo "W94_HELP_COMPATIBILITY_CONTRACT=FAIL"; exit 1;
}
echo "W94_HELP_COMPATIBILITY_CONTRACT=PASS"
for marker in W94_REAL_TAGS_RUNTIME_CONTRACT=PASS W94_REAL_TAGS_CONSUMER_VIEW=PASS; do
  grep -Fxq "$marker" "$LOG_ROOT/W94_TAGS_RUNTIME_CONTRACT.log" || {
    echo "W94_TAGS_RUNTIME_CONTRACT=FAIL missing=$marker"; exit 1;
  }
done
for spec in \
  'W94_TAGS_APP_CONSTRUCT.log:W94_REAL_APP_CONSTRUCT=PASS' \
  'W94_TAGS_APP_MAP.log:W94_REAL_APP_MAP=PASS' \
  'W94_TAGS_APP_OPEN.log:W94_REAL_APP_OPEN_DOCUMENT=PASS' \
  'W94_TAGS_APP_ACTIVATE.log:W94_REAL_APP_TAGS_ACTIVATION=PASS' \
  'W94_TAGS_APP_ACTIVATE.log:W94_REAL_APP_NO_ACTIVATION_FOCUS=PASS' \
  'W94_TAGS_APP_ACTIVATE.log:W94_REAL_APP_POST_MAP_SELECTION=PASS'; do
  file="${spec%%:*}"; marker="${spec#*:}"
  grep -Fxq "$marker" "$LOG_ROOT/$file" || {
    echo "W94_TAGS_STAGED_TRUE_APP_CONTRACT=FAIL missing=$marker"; exit 1;
  }
done
for marker in W94_REAL_RESEARCH_RESIZE_AFTER_REOPEN=PASS \
 W94_REAL_RESEARCH_WIDTH_PERSISTENCE=PASS W94_REAL_TAGS_RESPONSIVE_LAYOUT=PASS; do
  grep -Fxq "$marker" "$LOG_ROOT/W94_RESEARCH_RESIZE_REOPEN.log" || {
    echo "W94_RESEARCH_RESIZE_CONTRACT=FAIL missing=$marker"; exit 1;
  }
done
for marker in W94_REAL_TAGS_PANEL=PASS W94_REAL_TAGS_SCOPE_FILTERS=PASS \
 W94_REAL_TAGS_EXACT_USES=PASS W94_REAL_TAGS_SORTING=PASS \
 W94_REAL_TAGS_ALL_AZ_ACTION=PASS; do
  grep -Fxq "$marker" "$LOG_ROOT/W94_TAGS_PANEL.log" || {
    echo "W94_TAGS_PANEL_CONTRACT=FAIL missing=$marker"; exit 1;
  }
done
for marker in W94_REAL_APP_TAGS_CLIENT=PASS W94_REAL_APP_THREE_AUTHORITIES=PASS \
 W94_REAL_APP_EXACT_USE_NAVIGATION=PASS W94_REAL_APP_TAG_TRANSACTION=PASS \
 W94_REAL_TAG_OPERATION_MODE=PASS W94_REAL_APP_DOCUMENT_UNCHANGED=PASS \
 W94_REAL_APP_TAGS_LIFECYCLE=PASS W94_REAL_APP_VIEWPORT_FREE_RENDER=PASS \
 W94_REAL_APP_POST_MAP_SELECTION=PASS; do
  grep -Fxq "$marker" "$LOG_ROOT/W94_TAGS_TRUE_APP.log" || {
    echo "W94_TAGS_TRUE_APP_CONTRACT=FAIL missing=$marker"; exit 1;
  }
done

echo "W94_STAGED_TRUE_APP_LANES=PASS"
echo "W94_GTK_LANES_LOG_ROOT=$LOG_ROOT"
echo "W94_GTK_LANE_NO_SKIPS=PASS"
echo "W94_GTK_LANES=PASS"
