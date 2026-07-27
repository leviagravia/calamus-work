"""Real-process hostile proofs for the W90 Pandoc adapter."""
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

from calamus_pandoc_process import PandocProcessRunner


_FAKE = r'''#!/usr/bin/env python3
import os
import sys
import time
if "--version" in sys.argv:
    print("pandoc 3.1.11")
    print("Features: test")
    raise SystemExit(0)
if "--sleep" in sys.argv:
    time.sleep(30)
output = None
for index, item in enumerate(sys.argv):
    if item == "--output" and index + 1 < len(sys.argv):
        output = sys.argv[index + 1]
if "--loud" in sys.argv:
    sys.stdout.write("A" * 200000 + "STDOUT-END")
    sys.stderr.write("B" * 200000 + "STDERR-END")
    raise SystemExit(0)
if "--fail" in sys.argv:
    print("synthetic failure", file=sys.stderr)
    raise SystemExit(7)
if output:
    with open(output, "wb") as handle:
        handle.write(b"generated")
print("ok")
'''


class PandocProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.executable = self.root / "pandoc-test"
        self.executable.write_text(_FAKE, encoding="utf-8")
        self.executable.chmod(0o755)
        self.runner = PandocProcessRunner(executable_name=str(self.executable))

    def tearDown(self):
        self.runner.cancel_active()
        self.temp.cleanup()

    def test_detects_absolute_executable_and_supported_version(self):
        identity = self.runner.detect()
        self.assertEqual(identity.path, str(self.executable.resolve()))
        self.assertEqual(identity.version, "3.1.11")
        self.assertEqual(identity.version_parts, (3, 1, 11))

    def test_rejects_old_and_malformed_version_output(self):
        old = self.root / "pandoc-old"
        old.write_text("#!/bin/sh\necho 'pandoc 2.10.1'\n", encoding="utf-8")
        old.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "2.11.0 or newer"):
            PandocProcessRunner(executable_name=str(old)).detect()
        malformed = self.root / "pandoc-malformed"
        malformed.write_text("#!/bin/sh\necho 'not pandoc'\n", encoding="utf-8")
        malformed.chmod(0o755)
        with self.assertRaisesRegex(ValueError, "unrecognized version"):
            PandocProcessRunner(executable_name=str(malformed)).detect()

    def test_runs_shell_free_and_reports_nonzero_stderr(self):
        success = self.runner.run((str(self.executable), "--anything"))
        self.assertTrue(success.succeeded)
        self.assertEqual(success.stdout.strip(), "ok")
        failed = self.runner.run((str(self.executable), "--fail"))
        self.assertEqual(failed.status, "error")
        self.assertEqual(failed.returncode, 7)
        self.assertIn("synthetic failure", failed.stderr)
        self.assertIsNone(self.runner.active_pid)

    def test_stdout_and_stderr_are_bounded_during_capture(self):
        result = self.runner.run((str(self.executable), "--loud"))
        self.assertTrue(result.succeeded)
        self.assertLessEqual(len(result.stdout.encode("utf-8")), 64 * 1024)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 64 * 1024)
        self.assertTrue(result.stdout.endswith("STDOUT-END"))
        self.assertTrue(result.stderr.endswith("STDERR-END"))

    def test_timeout_terminates_exact_process(self):
        result = self.runner.run(
            (str(self.executable), "--sleep"), timeout_seconds=0.25
        )
        self.assertEqual(result.status, "timeout")
        self.assertIsNone(self.runner.active_pid)

    def test_external_cancel_terminates_exact_process_and_thread(self):
        holder = {}

        def work():
            holder["result"] = self.runner.run(
                (str(self.executable), "--sleep"), timeout_seconds=20
            )

        thread = threading.Thread(target=work)
        thread.start()
        deadline = time.monotonic() + 3
        while self.runner.active_pid is None and time.monotonic() < deadline:
            time.sleep(0.01)
        pid = self.runner.active_pid
        self.assertIsNotNone(pid)
        self.assertTrue(self.runner.cancel_active())
        thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(holder["result"].status, "cancelled")
        self.assertIsNone(self.runner.active_pid)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_one_active_process_gate_is_explicit(self):
        holder = {}
        thread = threading.Thread(
            target=lambda: holder.setdefault(
                "result",
                self.runner.run((str(self.executable), "--sleep"), timeout_seconds=20),
            )
        )
        thread.start()
        deadline = time.monotonic() + 3
        while self.runner.active_pid is None and time.monotonic() < deadline:
            time.sleep(0.01)
        with self.assertRaisesRegex(RuntimeError, "already active"):
            self.runner.run((str(self.executable), "--anything"))
        self.runner.cancel_active()
        thread.join(4)


if __name__ == "__main__":
    unittest.main()
