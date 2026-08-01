#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
LOG_ROOT="${CALAMUS_W90_GTK_LOG_ROOT:-$(mktemp -d)}"
PY_CACHE="$(mktemp -d)"
TEMP_ROOT="$(mktemp -d)"
mkdir -p "$LOG_ROOT"

cleanup() {
    rm -rf "$PY_CACHE" "$TEMP_ROOT"
}
trap cleanup EXIT

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="$PY_CACHE"

scan_blocking() {
    local log="$1"
    for token in \
        'Gtk-CRITICAL' 'Gdk-CRITICAL' 'GLib-CRITICAL' \
        'GLib-GObject-CRITICAL' 'Traceback (most recent call last)' \
        'PyGTKDeprecationWarning' 'unversioned namespace'; do
        if grep -Fq "$token" "$log"; then
            echo "W90_GTK_LANE_BLOCKING_DIAGNOSTIC=$token"
            return 1
        fi
    done
}

run_lane() {
    local name="$1"
    shift
    local lane_home="$TEMP_ROOT/$name/home"
    local lane_data="$TEMP_ROOT/$name/data"
    local lane_config="$TEMP_ROOT/$name/config"
    local lane_cache="$TEMP_ROOT/$name/cache"
    local log="$LOG_ROOT/$name.log"
    mkdir -p "$lane_home" "$lane_data" "$lane_config" "$lane_cache"
    echo "--- W90 GTK LANE: $name ---"
    set +e
    HOME="$lane_home" \
    XDG_DATA_HOME="$lane_data" \
    XDG_CONFIG_HOME="$lane_config" \
    XDG_CACHE_HOME="$lane_cache" \
    G_DEBUG=fatal-criticals \
    timeout 240s "$@" >"$log" 2>&1
    local status=$?
    set -e
    cat "$log"
    if [[ "$status" -ne 0 ]]; then
        echo "${name}=FAIL status=$status"
        return 1
    fi
    if grep -Eiq 'skipped|OK \(skipped=' "$log"; then
        echo "${name}=FAIL skipped-test"
        return 1
    fi
    scan_blocking "$log" || {
        echo "${name}=FAIL diagnostics"
        return 1
    }
    if pgrep -af "^python3( -B)? $ROOT/bin/calamus$" >/dev/null; then
        echo "${name}=FAIL surviving-calamus"
        pgrep -af "^python3( -B)? $ROOT/bin/calamus$" || true
        return 1
    fi
    echo "${name}=PASS"
}

PY=(python3 -B -m unittest -v)
cd "$ROOT/tests"

PANDOC_PREFLIGHT="$({
    cd "$ROOT"
    python3 -B - <<'PY_INNER'
from calamus_pandoc_process import PandocProcessRunner
identity = PandocProcessRunner().detect()
print(f"path={identity.path}")
print(f"version={identity.version}")
PY_INNER
} 2>&1)" || {
    printf '%s\n' "$PANDOC_PREFLIGHT"
    echo "W90_PANDOC_PREFLIGHT=FAIL"
    exit 1
}
printf '%s\n' "$PANDOC_PREFLIGHT"
echo "W90_PANDOC_PREFLIGHT=PASS"

# One real-GTK modal session and one component workflow per fresh process.
run_lane W90_MODAL_SESSION "${PY[@]}" \
    test_modal_dialog_gtk_session.ModalDialogGtkSessionTests.test_response_hide_source_cleanup_and_destroy_are_owned

for method in \
    test_options_builder_has_typed_controls_and_closed_surface \
    test_destination_builder_is_local_owned_and_typed \
    test_preview_builder_owns_semantic_text \
    test_progress_builder_owns_spinner_and_status; do
    run_lane "W90_PANDOC_${method}" "${PY[@]}" \
        "test_pandoc_dialogs.PandocDialogComponentTests.${method}"
done

for method in \
    test_about_builder_returns_exact_owned_widgets \
    test_system_info_builder_returns_exact_owned_widgets; do
    run_lane "W90_IDENTITY_${method}" "${PY[@]}" \
        "test_identity_dialogs.IdentityDialogComponentTests.${method}"
done

for method in \
    test_real_tree_row_activation_emits_semantic_file_event \
    test_refresh_preserves_expanded_folder_and_selection \
    test_secondary_click_and_keyboard_popup_select_item_before_semantic_context_signal; do
    run_lane "W79_WORKSPACE_${method}" "${PY[@]}" \
        "test_workspace_gtk_semantics.WorkspaceGtkSemanticsTests.${method}"
done

# Historical W85 proof is deliberately split: builder, one modal response,
# destination builder, and true-App export each receive a fresh interpreter.
run_lane W85_PRODUCT_BUILDER "${PY[@]}" \
    test_research_export_app_desktop_e2e.ResearchExportAppDesktopE2E.test_real_product_dialog_builder_has_five_products_and_dossier_default
run_lane W85_PRODUCT_MODAL "${PY[@]}" \
    test_research_export_app_desktop_e2e.ResearchExportAppDesktopE2E.test_real_product_dialog_single_modal_cancel_is_owned

W85_FIXTURE="$TEMP_ROOT/w85-fixture"
mkdir -p "$W85_FIXTURE/home" "$W85_FIXTURE/data" "$W85_FIXTURE/config" "$W85_FIXTURE/cache"
W85_DOCUMENT="$W85_FIXTURE/W85_Research_Sample.md"
W85_OUTPUT="$W85_FIXTURE/W85_Research_Sample-research-dossier.md"
HOME="$W85_FIXTURE/home" \
XDG_DATA_HOME="$W85_FIXTURE/data" \
XDG_CONFIG_HOME="$W85_FIXTURE/config" \
XDG_CACHE_HOME="$W85_FIXTURE/cache" \
python3 -B - "$W85_DOCUMENT" <<'PY'
from pathlib import Path
import sys
from calamus_reference_store import MarkdownReferenceStore
from calamus_references import ReferenceRecord
from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
from calamus_source_notes import SourceNote

document = Path(sys.argv[1])
document.write_text(
    "# Introduction {#introduction}\n\n"
    "Evidence in the introduction [@ratzinger1968].\n",
    encoding="utf-8",
)
reference_store = MarkdownReferenceStore()
snapshot = reference_store.load()
result = reference_store.save(
    (
        ReferenceRecord(
            key="ratzinger1968",
            title="Introduction to Christianity",
            authors=("Ratzinger, Joseph",),
            year="1968",
        ),
    ),
    snapshot.token,
)
if not result.saved:
    raise SystemExit(result.message)
note_store = MarkdownSourceNoteStore(source_notes_path(str(document)))
note_snapshot = note_store.load()
note_result = note_store.save(
    (
        SourceNote(
            id="sn-introduction",
            kind="quote",
            text="Evidence in the introduction",
            reference_key="ratzinger1968",
            target="#introduction",
        ),
    ),
    note_snapshot.token,
)
if not note_result.saved:
    raise SystemExit(note_result.message)
PY

run_lane W85_DESTINATION_BUILDER env \
    CALAMUS_W85_E2E_DOCUMENT="$W85_DOCUMENT" \
    "${PY[@]}" \
    test_research_export_app_desktop_e2e.ResearchExportAppDesktopE2E.test_real_destination_dialog_builder_uses_product_specific_markdown_name

run_lane W85_TRUE_APP_EXPORT env \
    CALAMUS_W85_E2E_DOCUMENT="$W85_DOCUMENT" \
    CALAMUS_W85_E2E_OUTPUT="$W85_OUTPUT" \
    HOME="$W85_FIXTURE/home" \
    XDG_DATA_HOME="$W85_FIXTURE/data" \
    XDG_CONFIG_HOME="$W85_FIXTURE/config" \
    XDG_CACHE_HOME="$W85_FIXTURE/cache" \
    "${PY[@]}" \
    test_research_export_app_desktop_e2e.ResearchExportAppDesktopE2E.test_real_app_exports_dossier_without_mutating_authorities

# Historical W89 stable-identity behaviour and current W90 identity each receive a fresh interpreter.
run_lane W89_STABLE_IDENTITY_TRUE_APP env CALAMUS_W89_RUN_IDENTITY_GTK=1 \
    "${PY[@]}" \
    test_w89_identity_app_desktop_e2e.W89IdentityRealAppE2E.test_real_about_and_system_info_owned_identity

for method in \
    test_real_related_dialog_symmetric_write_and_bridge_navigation \
    test_real_reference_set_dialog_markdown_and_navigation \
    test_real_rename_impact_dialog_and_four_authorities \
    test_real_normal_close_lifecycle_exits_main_loop_and_process; do
    run_lane "W89_RESEARCH_${method}" env CALAMUS_W89_RUN_REAL_GTK=1 \
        "${PY[@]}" \
        "test_w89_related_sets_app_desktop_e2e.W89RealAppDesktopE2E.${method}"
done

run_lane W90_IDENTITY_TRUE_APP env CALAMUS_W90_RUN_IDENTITY_GTK=1 \
    "${PY[@]}" \
    test_w90_identity_app_desktop_e2e.W90IdentityRealAppE2E.test_real_about_and_system_info_owned_identity

for method in \
    test_real_app_typed_handoff_real_pandoc_and_normal_close \
    test_true_app_close_cancels_exact_active_pandoc_child; do
    run_lane "W90_PANDOC_${method}" env CALAMUS_W90_RUN_REAL_GTK=1 \
        "${PY[@]}" \
        "test_w90_pandoc_app_desktop_e2e.W90PandocRealAppE2E.${method}"
done

TRUE_APP_LOG="$LOG_ROOT/W90_PANDOC_test_real_app_typed_handoff_real_pandoc_and_normal_close.log"
for marker in \
    W90_REAL_APP_TYPED_DIALOG_HANDOFF=PASS \
    W90_REAL_APP_REFERENCE_SET_PROVIDER=PASS \
    W90_REAL_PANDOC_TERMINAL_OUTCOME=PASS \
    W90_REAL_PANDOC_BIBLIOGRAPHY_EXPORT=PASS; do
    grep -Fxq "$marker" "$TRUE_APP_LOG" || {
        echo "W90_PANDOC_TRUE_APP_CONTRACT=FAIL missing=$marker"
        exit 1
    }
done
echo 'W90_PANDOC_TRUE_APP_CONTRACT=PASS'

echo "W90_GTK_LANES_LOG_ROOT=$LOG_ROOT"
echo "W90_GTK_LANE_NO_SKIPS=PASS"
echo "W90_GTK_LANES=PASS"
