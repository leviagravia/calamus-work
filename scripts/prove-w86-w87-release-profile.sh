#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
TEMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEMP_ROOT"' EXIT

run_one() {
  local name="$1"; shift
  local lane="$TEMP_ROOT/$name"
  local log="$lane/test.log"
  mkdir -p "$lane/home" "$lane/config" "$lane/data" "$lane/cache" "$lane/files"
  echo "--- LEGACY FIXTURE RELEASE PROFILE: $name ---"
  set +e
  HOME="$lane/home" XDG_CONFIG_HOME="$lane/config" XDG_DATA_HOME="$lane/data" XDG_CACHE_HOME="$lane/cache" \
  G_DEBUG=fatal-criticals timeout 420s "$@" >"$log" 2>&1
  local status=$?
  set -e
  cat "$log"
  [[ "$status" -eq 0 ]] || { echo "${name}=FAIL status=$status"; exit 1; }
  ! grep -Eiq 'skipped|OK \(skipped=' "$log" || { echo "${name}=FAIL skipped"; exit 1; }
  echo "${name}=PASS"
}

# W86 real two-authority fixture.
W86="$TEMP_ROOT/w86"
mkdir -p "$W86/home" "$W86/config" "$W86/data" "$W86/cache" "$W86/files"
W86_DOC="$W86/files/W86.md"
HOME="$W86/home" XDG_CONFIG_HOME="$W86/config" XDG_DATA_HOME="$W86/data" XDG_CACHE_HOME="$W86/cache" \
python3 -B - "$W86_DOC" <<'PY'
from pathlib import Path
import sys
from calamus_reference_store import MarkdownReferenceStore
from calamus_references import ReferenceRecord
from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
from calamus_source_notes import SourceNote

document = Path(sys.argv[1])
document.write_text('# W86\n\nDocument body.\n', encoding='utf-8')
store = MarkdownReferenceStore()
snapshot = store.load()
result = store.save((
    ReferenceRecord(key='r1', title='One', tags=('Faith','Church  History','Café','temporary','reference-only')),
    ReferenceRecord(key='r2', title='Two', tags=('faith','Church History','Cafe\u0301','temporary')),
), snapshot.token)
if not result.saved:
    raise SystemExit(result.message)
notes = MarkdownSourceNoteStore(source_notes_path(str(document)))
snap = notes.load()
result = notes.save((SourceNote(id='sn-1', kind='comment', text='Note', tags=(' FAITH ','church history','CAFÉ','temporary','reference-only')),), snap.token)
if not result.saved:
    raise SystemExit(result.message)
PY
log="$W86/test.log"
set +e
HOME="$W86/home" XDG_CONFIG_HOME="$W86/config" XDG_DATA_HOME="$W86/data" XDG_CACHE_HOME="$W86/cache" \
CALAMUS_W86_E2E_DOCUMENT="$W86_DOC" G_DEBUG=fatal-criticals timeout 420s \
python3 -B -m unittest -v tests.test_tag_integrity_app_desktop_e2e.TagIntegrityAppDesktopE2E.test_real_app_renames_tags_across_two_markdown_authorities >"$log" 2>&1
status=$?
set -e
cat "$log"
[[ "$status" -eq 0 ]] || { echo "W86_REAL_FIXTURE_PROFILE=FAIL status=$status"; exit 1; }
! grep -Eiq 'skipped|OK \(skipped=' "$log" || { echo 'W86_REAL_FIXTURE_PROFILE=FAIL skipped'; exit 1; }
echo 'W86_REAL_FIXTURE_PROFILE=PASS'

# W87 import/export fixture.
W87="$TEMP_ROOT/w87"
mkdir -p "$W87/home" "$W87/config" "$W87/data" "$W87/cache" "$W87/files"
W87_DOC="$W87/files/W87.md"
W87_BIB="$W87/files/import.bib"
W87_OUT="$W87/files/export.bib"
HOME="$W87/home" XDG_CONFIG_HOME="$W87/config" XDG_DATA_HOME="$W87/data" XDG_CACHE_HOME="$W87/cache" \
python3 -B - "$W87_DOC" "$W87_BIB" <<'PY'
from pathlib import Path
import sys
from calamus_reference_store import MarkdownReferenceStore
from calamus_references import ReferenceRecord

document = Path(sys.argv[1]); source = Path(sys.argv[2])
document.write_text('# W87\n\nDocument body.\n', encoding='utf-8')
source.write_text('''@book{existing, title={Incoming title}, doi={10.1000/incoming}, publisher={Cambridge University Press}}\n@online{fresh, title={Fresh title}}\n@book{invalid, title={One}, title={Two}}\n''', encoding='utf-8')
store = MarkdownReferenceStore(); snapshot = store.load()
result = store.save((ReferenceRecord(key='existing', title='Existing local title'),), snapshot.token)
if not result.saved:
    raise SystemExit(result.message)
PY
log="$W87/test.log"
set +e
HOME="$W87/home" XDG_CONFIG_HOME="$W87/config" XDG_DATA_HOME="$W87/data" XDG_CACHE_HOME="$W87/cache" \
CALAMUS_W87_E2E_DOCUMENT="$W87_DOC" CALAMUS_W87_E2E_IMPORT_SOURCE="$W87_BIB" CALAMUS_W87_E2E_EXPORT_OUTPUT="$W87_OUT" \
G_DEBUG=fatal-criticals timeout 480s \
python3 -B -m unittest -v tests.test_bibtex_app_desktop_e2e.BibtexAppDesktopE2E.test_real_app_uses_real_preview_confirm_and_export_dialogs >"$log" 2>&1
status=$?
set -e
cat "$log"
[[ "$status" -eq 0 ]] || { echo "W87_REAL_FIXTURE_PROFILE=FAIL status=$status"; exit 1; }
! grep -Eiq 'skipped|OK \(skipped=' "$log" || { echo 'W87_REAL_FIXTURE_PROFILE=FAIL skipped'; exit 1; }
echo 'W87_REAL_FIXTURE_PROFILE=PASS'

echo 'CALAMUS_W86_W87_RELEASE_PROFILE=PASS tests=2 skips=0'
