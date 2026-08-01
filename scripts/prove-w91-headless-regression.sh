#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
TMP_CACHE="$(mktemp -d)"
LOG="${CALAMUS_W91_HEADLESS_LOG:-$(mktemp)}"
trap 'rm -rf "$TMP_CACHE"' EXIT

cd "$ROOT"
set +e
DISPLAY= \
WAYLAND_DISPLAY= \
GDK_BACKEND=x11 \
CALAMUS_W91_RUN_REAL_GTK=0 \
CALAMUS_W90_RUN_REAL_GTK=0 \
CALAMUS_W90_RUN_IDENTITY_GTK=0 \
CALAMUS_W89_RUN_REAL_GTK=0 \
CALAMUS_W89_RUN_IDENTITY_GTK=0 \
G_DEBUG=fatal-criticals \
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX="$TMP_CACHE" \
timeout 600s python3 -u -B -m unittest discover -s tests -p 'test_*.py' >"$LOG" 2>&1
status=$?
set -e
cat "$LOG"
[[ "$status" -eq 0 ]] || {
    echo "W91_HEADLESS_REGRESSION=FAIL status=$status"
    exit 1
}
count="$(sed -nE 's/^Ran ([0-9]+) tests.*/\1/p' "$LOG" | tail -n 1)"
[[ -n "$count" ]] || {
    echo "W91_HEADLESS_REGRESSION=FAIL missing-count"
    exit 1
}
[[ "$count" -eq 1348 ]] || {
    echo "W91_HEADLESS_REGRESSION=FAIL count=$count"
    exit 1
}
for token in \
    'Gtk-CRITICAL' 'Gdk-CRITICAL' 'GLib-CRITICAL' \
    'GLib-GObject-CRITICAL' 'Traceback (most recent call last)' \
    'PyGTKDeprecationWarning' 'unversioned namespace'; do
    if grep -Fq "$token" "$LOG"; then
        echo "W91_HEADLESS_REGRESSION=FAIL diagnostic=$token"
        exit 1
    fi
done
echo "W91_HEADLESS_REGRESSION_COUNT=$count"
echo "W91_HEADLESS_REGRESSION=PASS"
echo "W91_HEADLESS_GTK_WORKFLOWS_ISOLATED=PASS"
