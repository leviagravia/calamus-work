#!/usr/bin/env bash
# Canonical Calamus test environment. Every test/proof launcher must source this
# file instead of constructing cwd or import roots independently.
CALAMUS_TEST_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CALAMUS_SOURCE_ROOT="$CALAMUS_TEST_ROOT"
export CALAMUS_LIB_DIR="$CALAMUS_TEST_ROOT/calamus"
export CALAMUS_TEST_DIR="$CALAMUS_TEST_ROOT/tests"
export PYTHONPATH="$CALAMUS_TEST_ROOT/calamus:$CALAMUS_TEST_ROOT"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=0
cd "$CALAMUS_TEST_ROOT"
