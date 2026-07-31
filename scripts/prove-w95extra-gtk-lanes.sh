#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CALAMUS_SOURCE_ROOT="$ROOT"
export CALAMUS_LIB_DIR="$ROOT/calamus"
export CALAMUS_TEST_DIR="$ROOT/tests"
export PYTHONPATH="$ROOT/calamus"
export PYTHONDONTWRITEBYTECODE=1
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
    raise SystemExit('W95EXTRA_GTK_DISPLAY=FAIL')
print('W95EXTRA_GTK_DISPLAY=PASS')
PY
python3 -B "$ROOT/scripts/w95-true-gtk-app-gate.py"
python3 -B "$ROOT/scripts/w95extra-true-gtk-app-gate.py"
printf '%s\n' 'W95EXTRA_GTK_LANES=PASS'
