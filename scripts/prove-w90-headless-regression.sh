#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
TMP_CACHE="$(mktemp -d)"
LOG="${CALAMUS_W90_HEADLESS_LOG:-$(mktemp)}"
trap 'rm -rf "$TMP_CACHE"' EXIT

cd "$ROOT"
set +e
DISPLAY= \
WAYLAND_DISPLAY= \
GDK_BACKEND=x11 \
CALAMUS_W90_RUN_REAL_GTK=0 \
CALAMUS_W90_RUN_IDENTITY_GTK=0 \
CALAMUS_W89_RUN_REAL_GTK=0 \
CALAMUS_W89_RUN_IDENTITY_GTK=0 \
G_DEBUG=fatal-criticals \
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$TMP_CACHE" \
timeout 360s python3 -B -m unittest discover -s tests -p 'test_*.py' >"$LOG" 2>&1
status=$?
set -e
cat "$LOG"
[[ "$status" -eq 0 ]] || {
    echo "W90_HEADLESS_REGRESSION=FAIL status=$status"
    exit 1
}
grep -Fq 'Ran 1322 tests' "$LOG" || {
    echo "W90_HEADLESS_REGRESSION=FAIL count"
    exit 1
}
for token in \
    'Gtk-CRITICAL' 'Gdk-CRITICAL' 'GLib-CRITICAL' \
    'GLib-GObject-CRITICAL' 'Traceback (most recent call last)' \
    'PyGTKDeprecationWarning' 'unversioned namespace'; do
    if grep -Fq "$token" "$LOG"; then
        echo "W90_HEADLESS_REGRESSION=FAIL diagnostic=$token"
        exit 1
    fi
done
echo "W90_HEADLESS_REGRESSION_1322=PASS"
echo "W90_HEADLESS_GTK_WORKFLOWS_ISOLATED=PASS"
