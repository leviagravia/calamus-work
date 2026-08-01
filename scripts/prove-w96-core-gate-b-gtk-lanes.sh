#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
export PYTHONDONTWRITEBYTECODE=1
cd "$ROOT"
python3 -B - <<'PY'
import gi
gi.require_version('Gtk','3.0')
gi.require_version('Gdk','3.0')
from gi.repository import Gdk, Gtk
try:
    result = Gtk.init_check()
except TypeError:
    result = Gtk.init_check(None)
ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
if not ok or Gdk.Display.get_default() is None:
    raise SystemExit('W96_CORE_GATE_B_GTK_DISPLAY=FAIL')
print('W96_CORE_GATE_B_GTK_DISPLAY=PASS')
PY
CALAMUS_W96_RUN_REAL_GTK=1 python3 -B -m unittest -v tests.test_w96_document_overview_app_desktop_e2e
printf '%s\n' 'W96_CORE_GATE_B_GTK_LANES=PASS'
