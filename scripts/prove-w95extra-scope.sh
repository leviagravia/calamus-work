#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CALAMUS_SOURCE_ROOT="$ROOT"
export CALAMUS_LIB_DIR="$ROOT/calamus"
export CALAMUS_TEST_DIR="$ROOT/tests"
export PYTHONPATH="$ROOT/calamus"
export PYTHONDONTWRITEBYTECODE=1
python3 -B -m unittest -v \
  tests.test_w95extra_viewport_policy \
  tests.test_w95extra_viewport_runtime \
  tests.test_w95extra_typewriter_runtime \
  tests.test_w95extra_writing_menu \
  tests.test_insert_date_time_layer_wiring
printf '%s\n' 'W95EXTRA_SCOPE=PASS'
