#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
TEMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEMP_ROOT"' EXIT

TESTS=(
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_menu_root_change_recent_and_navigate_use_operational_panel
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_new_text_file_command_creates_rescans_selects_and_opens
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_new_folder_command_creates_rescans_and_selects_without_opening
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_rename_active_modified_file_updates_identity_sidecar_and_path_stores
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_rename_folder_rewrites_active_descendant_identity
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_duplicate_text_file_preserves_active_unsaved_identity_and_copies_sidecar
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_context_menu_rename_uses_canonical_gateway
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_context_menu_duplicate_uses_canonical_gateway
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_move_to_trash_detaches_active_document_and_carries_sidecar
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_context_menu_trash_folder_uses_canonical_gateway
  tests.test_workspace_app_desktop_e2e.WorkspaceAppDesktopE2E.test_real_app_opens_real_workspace_file_from_real_tree_signal
)

for index in "${!TESTS[@]}"; do
  test_id="${TESTS[$index]}"
  lane="$TEMP_ROOT/lane-$index"
  home="$lane/home"
  workspace="$lane/workspace"
  alt="$lane/alternative"
  mkdir -p "$home" "$lane/config" "$lane/data" "$lane/cache" \
           "$workspace/01_Drafts" "$workspace/02_Research" "$alt"
  printf '# Capitolo 1\n\nTesto iniziale.\n' > "$workspace/01_Drafts/Capitolo_1.md"
  printf 'Appunti\n' > "$workspace/01_Drafts/Appunti.txt"
  printf '# Alternative\n\nAlternative document.\n' > "$alt/Alternative_Document.md"
  log="$lane/test.log"
  echo "--- WORKSPACE RELEASE PROFILE: $test_id ---"
  set +e
  HOME="$home" \
  XDG_CONFIG_HOME="$lane/config" \
  XDG_DATA_HOME="$lane/data" \
  XDG_CACHE_HOME="$lane/cache" \
  CALAMUS_W79_E2E_WORKSPACE="$workspace" \
  CALAMUS_W79_E2E_ALT_WORKSPACE="$alt" \
  G_DEBUG=fatal-criticals \
  timeout 360s python3 -B -m unittest -v "$test_id" >"$log" 2>&1
  status=$?
  set -e
  cat "$log"
  [[ "$status" -eq 0 ]] || { echo "CALAMUS_WORKSPACE_E2E_PROFILE=FAIL status=$status test=$test_id"; exit 1; }
  ! grep -Eiq 'skipped|OK \(skipped=' "$log" || { echo "CALAMUS_WORKSPACE_E2E_PROFILE=FAIL skipped test=$test_id"; exit 1; }
done

echo "CALAMUS_WORKSPACE_E2E_PROFILE=PASS tests=${#TESTS[@]} skips=0"
