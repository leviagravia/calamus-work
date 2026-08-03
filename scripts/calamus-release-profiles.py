#!/usr/bin/env python3
"""Canonical explicit release-profile runner for Calamus.

Broad discovery is used only to inventory test identities. Release profiles load
exact identities from tests/calamus_release_test_profiles.json and fail on every
skip, failure, error, unexpected success, missing capability, or inventory drift.
"""
from __future__ import annotations

import argparse
import contextlib
import faulthandler
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from typing import Iterable, Iterator

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "tests"
MANIFEST = TEST_DIR / "calamus_release_test_profiles.json"

sys.dont_write_bytecode = True
faulthandler.enable(all_threads=True)
for path in (ROOT / "calamus", ROOT):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

LANE_FLAG_PREFIXES = (
    "CALAMUS_W79_",
    "CALAMUS_W85_",
    "CALAMUS_W86_",
    "CALAMUS_W87_",
    "CALAMUS_W88_",
    "CALAMUS_W89_",
    "CALAMUS_W90_",
    "CALAMUS_W91_",
    "CALAMUS_W92_",
    "CALAMUS_W94_",
    "CALAMUS_W95_",
    "CALAMUS_W95EXTRA_",
    "CALAMUS_W96_",
    "CALAMUS_W97_",
    "CALAMUS_W98_",
    "CALAMUS_W99_",
    "CALAMUS_W100_",
)


def _flatten(suite: unittest.TestSuite) -> Iterator[unittest.TestCase]:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _flatten(item)
        else:
            yield item


def discover_test_ids() -> tuple[str, ...]:
    suite = unittest.defaultTestLoader.discover(
        str(TEST_DIR), pattern="test*.py", top_level_dir=str(ROOT)
    )
    ids = sorted(test.id() for test in _flatten(suite))
    failed = [test_id for test_id in ids if "_FailedTest" in test_id]
    if failed:
        raise RuntimeError(f"inventory contains _FailedTest: {failed}")
    if not ids:
        raise RuntimeError("inventory discovered zero tests")
    return tuple(ids)


def load_manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema") != 1:
        raise RuntimeError("unsupported release-profile manifest schema")
    if data.get("published_baseline") != "9a80b266cbdb41b499efdb296ff2a312cf85656f":
        raise RuntimeError("manifest baseline identity mismatch")
    if not isinstance(data.get("profiles"), dict) or not data["profiles"]:
        raise RuntimeError("manifest has no profiles")
    return data


def validate_inventory(data: dict) -> tuple[int, int]:
    discovered = set(discover_test_ids())
    assigned: set[str] = set()
    duplicates: set[str] = set()
    for name, profile in data["profiles"].items():
        ids = profile.get("test_ids", [])
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"profile {name!r} contains duplicate test identities")
        for test_id in ids:
            if test_id in assigned:
                duplicates.add(test_id)
            assigned.add(test_id)
    unknown = sorted(assigned - discovered)
    unassigned = sorted(discovered - assigned)
    if unknown:
        raise RuntimeError(f"manifest assigns unknown tests: {unknown[:20]}")
    if unassigned:
        raise RuntimeError(f"unassigned discovered tests: {unassigned[:20]}")
    release_profiles = [
        name for name, profile in data["profiles"].items()
        if profile.get("release_gate", False)
    ]
    if not release_profiles:
        raise RuntimeError("manifest has no release profiles")
    print(
        "CALAMUS_RELEASE_PROFILE_INVENTORY=PASS "
        f"tests={len(discovered)} assigned={len(assigned)} "
        f"multi_profile={len(duplicates)} profiles={len(data['profiles'])}",
        flush=True,
    )
    return len(discovered), len(assigned)


def clean_environment(profile: dict) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT / 'calamus'}:{ROOT}"
    env["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    env["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    env["CALAMUS_TEST_DIR"] = str(TEST_DIR)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONFAULTHANDLER"] = "1"
    env.setdefault("TERM", "dumb")
    for key in list(env):
        if any(key.startswith(prefix) for prefix in LANE_FLAG_PREFIXES):
            env.pop(key, None)
    for key in profile.get("unset_env", []):
        env.pop(key, None)
    for key, value in profile.get("set_env", {}).items():
        env[key] = str(value)
    return env


def probe_capability(name: str, env: dict[str, str]) -> None:
    if name == "pandoc":
        path = shutil.which("pandoc", path=env.get("PATH"))
        if not path:
            raise RuntimeError("required capability unavailable: pandoc")
        completed = subprocess.run(
            [path, "--version"], env=env, cwd=ROOT,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=30, check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"pandoc probe failed: {completed.stdout}")
        print(f"CALAMUS_PROFILE_CAPABILITY_PANDOC=PASS path={path}")
        return
    if name == "symlink":
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            link = root / "link"
            target.write_text("x", encoding="utf-8")
            os.symlink(target, link)
            if not link.is_symlink():
                raise RuntimeError("symlink probe did not create a symlink")
        print("CALAMUS_PROFILE_CAPABILITY_SYMLINK=PASS")
        return
    if name == "fifo":
        if not hasattr(os, "mkfifo"):
            raise RuntimeError("required capability unavailable: FIFO")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "probe.fifo"
            os.mkfifo(path)
            if not path.exists():
                raise RuntimeError("FIFO probe failed")
        print("CALAMUS_PROFILE_CAPABILITY_FIFO=PASS")
        return
    if name == "case-rename":
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "CaseProbe"
            target = root / "caseprobe"
            source.write_text("x", encoding="utf-8")
            os.rename(source, target)
            if source.exists() or not target.is_file():
                raise RuntimeError("case-only rename probe failed")
        print("CALAMUS_PROFILE_CAPABILITY_CASE_RENAME=PASS")
        return
    if name in {"gio", "gtk-display"}:
        code = """
import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio
print('GIO=PASS')
"""
        if name == "gtk-display":
            code = """
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gtk
try:
    result = Gtk.init_check()
except TypeError:
    result = Gtk.init_check(None)
ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
if not ok or Gdk.Display.get_default() is None:
    raise SystemExit('GTK_DISPLAY=FAIL')
print('GTK_DISPLAY=PASS')
"""
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code], env=env, cwd=ROOT,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=30, check=False,
        )
        sys.stdout.write(completed.stdout)
        if completed.returncode != 0:
            raise RuntimeError(f"required capability unavailable: {name}")
        print(f"CALAMUS_PROFILE_CAPABILITY_{name.upper().replace('-', '_')}=PASS")
        return
    raise RuntimeError(f"unknown capability: {name}")


def _run_suite(test_ids: list[str], verbosity: int = 2) -> unittest.TestResult:
    print(f"CALAMUS_RELEASE_PROFILE_TEST_LOAD_BEGIN count={len(test_ids)}", file=sys.stderr, flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromNames(test_ids)
    print("CALAMUS_RELEASE_PROFILE_TEST_LOAD_COMPLETE=PASS", file=sys.stderr, flush=True)
    loaded = list(_flatten(suite))
    if len(loaded) != len(test_ids):
        raise RuntimeError(
            f"selected-test cardinality mismatch: requested={len(test_ids)} loaded={len(loaded)}"
        )
    failed_loads = [test.id() for test in loaded if "_FailedTest" in test.id()]
    if failed_loads:
        raise RuntimeError(f"selected profile contains _FailedTest: {failed_loads}")
    print("CALAMUS_RELEASE_PROFILE_TEST_RUN_BEGIN", file=sys.stderr, flush=True)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=verbosity).run(suite)
    print("CALAMUS_RELEASE_PROFILE_TEST_RUN_COMPLETE", file=sys.stderr, flush=True)
    return result


def validate_result(profile_name: str, result: unittest.TestResult, expected: int) -> None:
    problems: list[str] = []
    if result.testsRun != expected:
        problems.append(f"expected {expected} tests, ran {result.testsRun}")
    if result.failures:
        problems.append(f"failures={len(result.failures)}")
    if result.errors:
        problems.append(f"errors={len(result.errors)}")
    if result.skipped:
        details = "; ".join(f"{test.id()}: {reason}" for test, reason in result.skipped[:8])
        problems.append(f"skips={len(result.skipped)} [{details}]")
    if result.unexpectedSuccesses:
        problems.append(f"unexpected_successes={len(result.unexpectedSuccesses)}")
    if not result.wasSuccessful():
        problems.append("wasSuccessful=false")
    if problems:
        raise RuntimeError(f"profile {profile_name} failed: " + " | ".join(problems))
    print(
        f"CALAMUS_RELEASE_PROFILE_{profile_name.upper().replace('-', '_')}=PASS "
        f"tests={result.testsRun} skips=0"
    )


def run_unittest_profile(name: str, profile: dict) -> None:
    ids = profile.get("test_ids", [])
    if not ids:
        raise RuntimeError(f"unittest profile {name} has zero tests")
    env = clean_environment(profile)
    for capability in profile.get("capabilities", []):
        probe_capability(capability, env)
    # The release runner is itself a fresh process in normal use. Apply the
    # manifest-owned environment before importing selected test modules.
    os.environ.clear()
    os.environ.update(env)
    result = _run_suite(ids)
    validate_result(name, result, len(ids))


def run_script_profile(name: str, profile: dict) -> None:
    command = profile.get("command")
    if not isinstance(command, list) or not command:
        raise RuntimeError(f"script profile {name} has no command")
    env = clean_environment(profile)
    # Historical script profiles merge unittest's verbose stderr with marker
    # stdout and then validate exact marker lines. Forced unbuffered child stdout
    # can splice the first marker into unittest's unfinished status line. Keep
    # the release-profile process itself unbuffered, but preserve the historical
    # child buffering contract unless a profile explicitly opts into overriding it.
    if "PYTHONUNBUFFERED" not in profile.get("set_env", {}):
        env.pop("PYTHONUNBUFFERED", None)
    for capability in profile.get("capabilities", []):
        probe_capability(capability, env)
    timeout = int(profile.get("timeout_seconds", 1800))
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    sys.stdout.write(completed.stdout)
    if completed.returncode != 0:
        raise RuntimeError(f"script profile {name} exited {completed.returncode}")
    folded = completed.stdout.casefold()
    if "skipped" in folded or "ok (skipped=" in folded:
        raise RuntimeError(f"script profile {name} emitted a skipped test")
    for marker in profile.get("required_markers", []):
        if marker not in completed.stdout.splitlines():
            raise RuntimeError(f"script profile {name} missing marker: {marker}")
    print(f"CALAMUS_RELEASE_PROFILE_{name.upper().replace('-', '_')}=PASS script=1 skips=0")


def validate_inventory_in_subprocess() -> None:
    """Inventory in a disposable interpreter so imported tests cannot cache profile state."""
    inventory_profile = {
        "unset_env": ["DISPLAY", "WAYLAND_DISPLAY", "MIR_SOCKET", "GDK_BACKEND"],
        "set_env": {"CALAMUS_RELEASE_PROFILE": "inventory-only"},
    }
    env = clean_environment(inventory_profile)
    completed = subprocess.run(
        [sys.executable, "-B", str(Path(__file__).resolve()), "--inventory"],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
        check=False,
    )
    sys.stdout.write(completed.stdout)
    if completed.returncode != 0:
        raise RuntimeError("release-profile inventory subprocess failed")
    if "CALAMUS_RELEASE_PROFILE_INVENTORY=PASS" not in completed.stdout:
        raise RuntimeError("release-profile inventory subprocess omitted PASS marker")


def run_profile(name: str, data: dict) -> None:
    profile = data["profiles"].get(name)
    if profile is None:
        raise RuntimeError(f"unknown profile: {name}")
    kind = profile.get("kind")
    if kind == "unittest":
        run_unittest_profile(name, profile)
    elif kind == "script":
        run_script_profile(name, profile)
    elif kind == "manual":
        raise RuntimeError("manual profile cannot be executed by the automated runner")
    else:
        raise RuntimeError(f"unsupported profile kind for {name}: {kind}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--list-profiles", action="store_true")
    parser.add_argument("--run-profile")
    args = parser.parse_args()
    data = load_manifest()
    if args.inventory:
        validate_inventory(data)
        return 0
    if args.list_profiles:
        for name, profile in data["profiles"].items():
            print(f"{name}\t{profile.get('kind')}\t{len(profile.get('test_ids', []))}")
        return 0
    if args.run_profile:
        validate_inventory_in_subprocess()
        run_profile(args.run_profile, data)
        return 0
    parser.error("choose --inventory, --list-profiles or --run-profile")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"CALAMUS_RELEASE_PROFILE=FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
