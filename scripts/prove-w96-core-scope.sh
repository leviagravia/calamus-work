#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/calamus-test-env.sh"
python3 -B - "$ROOT" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
model = (root / "calamus/calamus_document_dossier.py").read_text(encoding="utf-8")
controller = (root / "calamus/calamus_document_dossier_controller.py").read_text(encoding="utf-8")
program = (root / "docs/canonical/CALAMUS_W96_DOCUMENT_OVERVIEW_CORE_FULL_PROGRAM.md").read_text(encoding="utf-8")
contract = (root / "docs/canonical/CALAMUS_W96_DOCUMENT_OVERVIEW_CORE_CONTRACT.md").read_text(encoding="utf-8")
for token in ("import gi", "from gi", "Gtk.", "Gdk.", "Gio."):
    assert token not in model + controller, token
for required in (
    "Related References",
    "Pertinent Reference Sets",
    "collected-unused",
    "W96 — Document Overview Core",
    "W97 — Bibliography Manager",
    "W98 — Research Panel Integral Closure",
    "W99 — retrospective GTK-free and lifecycle audit",
    "Scratchpad Full",
    "Document Overview Full",
):
    assert required in program, required
assert "no persistent dossier authority" in contract
assert "DocumentDossierSnapshot" in model
assert "DocumentDossierController" in controller
print("W96_CORE_GTK_FREE_MODEL=PASS")
print("W96_CORE_RELATED_REFERENCES=PASS")
print("W96_CORE_PERTINENT_REFERENCE_SETS=PASS")
print("W96_CORE_FULL_PROGRAM=PASS")
print("W96_CORE_SCOPE=PASS")
PY
