#!/usr/bin/env python3
"""Aggregate the real W95extra GTK/App proof without external test tools."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env["CALAMUS_SOURCE_ROOT"] = str(ROOT)
env["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
env["CALAMUS_W95EXTRA_RUN_REAL_GTK"] = "1"
env["PYTHONPATH"] = str(ROOT / "calamus")
env["PYTHONDONTWRITEBYTECODE"] = "1"

completed = subprocess.run(
    [
        sys.executable,
        "-B",
        "-m",
        "unittest",
        "-v",
        "tests.test_w95extra_typewriter_app_desktop_e2e",
    ],
    cwd=ROOT,
    env=env,
    check=False,
)
if completed.returncode != 0:
    print(f"W95EXTRA_TRUE_GTK_APP_GATE=FAIL status={completed.returncode}")
    raise SystemExit(completed.returncode)
print("W95EXTRA_TRUE_GTK_APP_GATE=PASS")
