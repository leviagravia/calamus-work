"""Headless orchestration proofs for the thin W90 runtime."""
from pathlib import Path
import shutil
import tempfile
import threading
import time
import unittest

from calamus_pandoc import (
    FORMAT_PLAIN,
    PRODUCT_BIBLIOGRAPHY,
    SCOPE_ALL,
)
from calamus_pandoc_controller import PandocExportController
from calamus_pandoc_runtime import PandocExportRuntime
from calamus_reference_set_store import MarkdownReferenceSetStore
from calamus_reference_store import MarkdownReferenceStore, serialize_references_markdown
from calamus_references import ReferenceRecord


@unittest.skipUnless(shutil.which("pandoc"), "real Pandoc unavailable")
class PandocRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        references = self.root / "references.md"
        references.write_text(
            serialize_references_markdown(
                (ReferenceRecord("guardini1950", "The Lord", authors=("Guardini, Romano",), year="1950"),)
            ),
            encoding="utf-8",
        )
        sets = self.root / "reference-sets.md"
        self.controller = PandocExportController(
            MarkdownReferenceStore(str(references)),
            MarkdownReferenceSetStore(str(sets)),
            document_path_provider=lambda: None,
            document_text_provider=lambda: "",
        )

    def tearDown(self):
        self.controller.cancel_active()
        self.temp.cleanup()

    def test_complete_injected_workflow_calls_one_controller_path(self):
        destination = self.root / "bibliography.txt"
        observed = {"preview": [], "result": [], "errors": []}
        runtime = PandocExportRuntime(
            object(),
            self.controller,
            document_path_provider=lambda: None,
            reference_set_names_provider=lambda: (),
            options_chooser=lambda *_: (
                PRODUCT_BIBLIOGRAPHY,
                SCOPE_ALL,
                FORMAT_PLAIN,
                "",
                "",
            ),
            destination_chooser=lambda *_: str(destination),
            preview_presenter=lambda _parent, plan, preview: observed["preview"].append((plan, preview)) or True,
            progress_builder=lambda *_: None,
            show_error=lambda _parent, message: observed["errors"].append(message),
            show_result=lambda _parent, result: observed["result"].append(result),
            operation_executor=lambda _title, operation: operation(),
        )
        self.assertTrue(runtime.export())
        self.assertTrue(destination.is_file())
        self.assertIn("The Lord", destination.read_text(encoding="utf-8"))
        self.assertEqual(len(observed["preview"]), 1)
        self.assertEqual(len(observed["result"]), 1)
        self.assertEqual(observed["errors"], [])
        self.assertFalse(runtime.busy)
        self.assertTrue(runtime.last_outcome.succeeded)
        self.assertEqual(runtime.last_outcome.stage, "result")
        self.assertEqual(runtime.last_outcome.path, str(destination))


    def test_cancel_and_executor_failure_have_stable_terminal_outcomes(self):
        errors = []
        cancelled = PandocExportRuntime(
            object(),
            self.controller,
            document_path_provider=lambda: None,
            reference_set_names_provider=lambda: (),
            options_chooser=lambda *_: None,
            destination_chooser=lambda *_: None,
            preview_presenter=lambda *_: False,
            progress_builder=lambda *_: None,
            show_error=lambda _parent, message: errors.append(message),
            show_result=lambda *_: None,
            operation_executor=lambda _title, operation: operation(),
        )
        self.assertFalse(cancelled.export())
        self.assertEqual(cancelled.last_outcome.status, "cancelled")
        self.assertEqual(cancelled.last_outcome.stage, "options")

        failed = PandocExportRuntime(
            object(),
            self.controller,
            document_path_provider=lambda: None,
            reference_set_names_provider=lambda: (),
            options_chooser=lambda *_: (
                PRODUCT_BIBLIOGRAPHY,
                SCOPE_ALL,
                FORMAT_PLAIN,
                "",
                "",
            ),
            destination_chooser=lambda *_: str(self.root / "failure.txt"),
            preview_presenter=lambda *_: True,
            progress_builder=lambda *_: None,
            show_error=lambda _parent, message: errors.append(message),
            show_result=lambda *_: None,
            operation_executor=lambda _title, _operation: (_ for _ in ()).throw(RuntimeError("executor failed")),
        )
        self.assertFalse(failed.export())
        self.assertEqual(failed.last_outcome.status, "error")
        self.assertEqual(failed.last_outcome.stage, "prepare")
        self.assertIn("executor failed", failed.last_outcome.message)
        self.assertIn("executor failed", errors[-1])

    def test_busy_gate_and_shutdown_join_are_explicit(self):
        errors = []
        runtime = PandocExportRuntime(
            object(),
            self.controller,
            document_path_provider=lambda: None,
            reference_set_names_provider=lambda: (),
            options_chooser=lambda *_: None,
            destination_chooser=lambda *_: None,
            preview_presenter=lambda *_: False,
            progress_builder=lambda *_: None,
            show_error=lambda _parent, message: errors.append(message),
            show_result=lambda *_: None,
        )
        stop = threading.Event()
        thread = threading.Thread(target=lambda: stop.wait(2), daemon=False)
        runtime._thread = thread
        thread.start()
        self.assertFalse(runtime.export())
        self.assertIn("already active", errors[-1])
        stop.set()
        self.assertTrue(runtime.shutdown(join_timeout=1.0))
        thread.join(1)


if __name__ == "__main__":
    unittest.main()
