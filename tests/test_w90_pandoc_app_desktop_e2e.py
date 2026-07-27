"""True App/GTK and real-Pandoc proof lanes for W90.

The integrated export proof drives the real App callback, real controller,
canonical Markdown stores and real Pandoc process.  It substitutes only the
semantic dialog boundaries (options, destination, preview acknowledgement and
result presentation).  Real GTK builders and modal ownership are proven in
fresh component lanes, while the complete native-dialog workflow remains the
manual desktop validation.  This avoids treating a transient modal window as a
process-completion API.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
import unittest
import uuid
from unittest.mock import patch

from calamus_pandoc_artifact_assertions import contains_semantic_text

from calamus_gtk_test_driver import (
    HAVE_GTK,
    close_visible_dialogs,
    display_ready,
    pump,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_REAL_GTK = os.environ.get("CALAMUS_W90_RUN_REAL_GTK") == "1"


def _load_app_module():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = f"calamus_w90_pandoc_{uuid.uuid4().hex}"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _set_isolated_config(root: Path) -> None:
    import calamus_config
    config = root / "config" / "calamus"
    calamus_config.CONFIG_DIR = str(config)
    calamus_config.SETTINGS_FILE = str(config / "settings.json")
    calamus_config.RECENT_FILE = str(config / "recent.json")
    calamus_config.FAVOURITES_FILE = str(config / "favourites.json")


def _environment(root: Path) -> dict[str, str]:
    return {
        "HOME": str(root),
        "XDG_DATA_HOME": str(root / "data"),
        "XDG_CONFIG_HOME": str(root / "config"),
        "XDG_CACHE_HOME": str(root / "cache"),
        "PYTHONPATH": f"{ROOT / 'calamus'}:{ROOT}",
    }


def _prepare_research(root: Path) -> tuple[Path, Path]:
    from calamus_reference_set_store import MarkdownReferenceSetStore
    from calamus_reference_sets import ReferenceSet, serialize_reference_sets_markdown
    from calamus_reference_store import MarkdownReferenceStore, serialize_references_markdown
    from calamus_references import ReferenceRecord

    research = root / "data" / "calamus" / "research"
    research.mkdir(parents=True, exist_ok=True)
    references = research / "references.md"
    sets = research / "reference-sets.md"
    records = (
        ReferenceRecord(
            "ratzinger1968",
            "Introduction to Christianity",
            authors=("Ratzinger, Joseph",),
            year="1968",
            publisher="Herder and Herder",
            aliases=("ratzinger-old",),
        ),
        ReferenceRecord(
            "guardini1950",
            "The Lord",
            authors=("Guardini, Romano",),
            year="1950",
            publisher="Regnery",
        ),
    )
    references.write_text(serialize_references_markdown(records), encoding="utf-8")
    sets.write_text(
        serialize_reference_sets_markdown(
            (ReferenceSet("Core sources", members=("ratzinger1968", "guardini1950")),)
        ),
        encoding="utf-8",
    )
    assert Path(MarkdownReferenceStore().path) == references
    assert Path(MarkdownReferenceSetStore().path) == sets
    return references, sets


@unittest.skipUnless(
    RUN_REAL_GTK and HAVE_GTK and display_ready() and shutil.which("pandoc"),
    "set CALAMUS_W90_RUN_REAL_GTK=1 on a real GTK desktop with Pandoc",
)
class W90PandocRealAppE2E(unittest.TestCase):
    def test_real_app_typed_handoff_real_pandoc_and_normal_close(self):
        from calamus_pandoc import (
            FORMAT_PLAIN,
            PRODUCT_BIBLIOGRAPHY,
            SCOPE_REFERENCE_SET,
        )
        from calamus_pandoc_runtime import PandocExportRuntime

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, _environment(root), clear=False):
                _set_isolated_config(root)
                references, sets = _prepare_research(root)
                references_before = references.read_bytes()
                sets_before = sets.read_bytes()
                output = root / "exports" / "core-bibliography.txt"
                output.parent.mkdir()
                module = _load_app_module()
                win = module.App()
                observed: dict[str, object] = {
                    "set_names": (),
                    "preview": None,
                    "result": None,
                    "errors": [],
                    "operations": [],
                }

                def choose_options(_parent, set_names):
                    observed["set_names"] = tuple(set_names)
                    return (
                        PRODUCT_BIBLIOGRAPHY,
                        SCOPE_REFERENCE_SET,
                        FORMAT_PLAIN,
                        "Core sources",
                        "",
                    )

                def execute_operation(title, operation):
                    observed["operations"].append(title)
                    return operation()

                def present_preview(_parent, plan, preview):
                    observed["preview"] = (plan, preview)
                    self.assertTrue(preview.succeeded, preview.message)
                    self.assertEqual(plan.selection.reference_set_name, "Core sources")
                    self.assertEqual(plan.selection.keys, ("ratzinger1968", "guardini1950"))
                    self.assertIn("Introduction to Christianity", preview.text)
                    self.assertIn("The Lord", preview.text)
                    return True

                runtime = PandocExportRuntime(
                    win,
                    win.pandoc_export_controller,
                    document_path_provider=lambda: win.document.file_path,
                    reference_set_names_provider=lambda: tuple(
                        item.name
                        for item in win.reference_set_runtime.sets_snapshot(force=True)
                    ),
                    options_chooser=choose_options,
                    destination_chooser=lambda *_: str(output),
                    preview_presenter=present_preview,
                    progress_builder=lambda *_: None,
                    show_error=lambda _parent, message: observed["errors"].append(message),
                    show_result=lambda _parent, result: observed.__setitem__("result", result),
                    operation_executor=execute_operation,
                )
                win.pandoc_export_runtime = runtime
                try:
                    win.show_all()
                    pump()
                    self.assertTrue(win.on_export_with_pandoc(), runtime.last_outcome)
                    self.assertTrue(runtime.last_outcome.succeeded)
                    self.assertEqual(runtime.last_outcome.stage, "result")
                    self.assertEqual(runtime.last_outcome.path, str(output))
                    self.assertEqual(observed["set_names"], ("Core sources",))
                    self.assertEqual(len(observed["operations"]), 3)
                    self.assertIsNotNone(observed["preview"])
                    self.assertIsNotNone(observed["result"])
                    self.assertEqual(observed["errors"], [])
                    self.assertTrue(output.is_file())
                    rendered = output.read_text(encoding="utf-8")
                    self.assertTrue(
                        contains_semantic_text(
                            rendered, "Introduction to Christianity", casefold=True
                        )
                    )
                    self.assertTrue(
                        contains_semantic_text(rendered, "The Lord", casefold=True)
                    )
                    self.assertTrue(
                        contains_semantic_text(rendered, "Herder and Herder")
                    )
                    self.assertFalse(
                        contains_semantic_text(rendered, "Herder; Herder")
                    )
                    self.assertEqual(references.read_bytes(), references_before)
                    self.assertEqual(sets.read_bytes(), sets_before)
                    self.assertIsNone(win.pandoc_export_controller.active_pid)
                    self.assertTrue(win.request_application_close())
                    pump()
                    self.assertFalse(win.get_visible())
                    print("W90_REAL_APP_TYPED_DIALOG_HANDOFF=PASS")
                    print("W90_REAL_APP_REFERENCE_SET_PROVIDER=PASS")
                    print("W90_REAL_PANDOC_PREVIEW=PASS")
                    print("W90_REAL_PANDOC_BIBLIOGRAPHY_EXPORT=PASS")
                    print("W90_REAL_PANDOC_TERMINAL_OUTCOME=PASS")
                    print("W90_REAL_PANDOC_AUTHORITIES_UNCHANGED=PASS")
                    print("W90_REAL_PANDOC_NORMAL_CLOSE=PASS")
                finally:
                    close_visible_dialogs()
                    if win.get_visible():
                        win.destroy()
                    pump()

    def test_true_app_close_cancels_exact_active_pandoc_child(self):
        fake_source = r"""#!/usr/bin/env python3
import sys
import time
if "--version" in sys.argv:
    print("pandoc 3.1.11")
    raise SystemExit(0)
time.sleep(30)
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake = root / "pandoc-slow"
            fake.write_text(fake_source, encoding="utf-8")
            fake.chmod(0o755)
            with patch.dict(os.environ, _environment(root), clear=False):
                _set_isolated_config(root)
                _prepare_research(root)
                module = _load_app_module()
                from calamus_pandoc_process import PandocProcessRunner

                runner = PandocProcessRunner(executable_name=str(fake))
                win = module.App()
                holder = {}
                try:
                    win.show_all()
                    pump()
                    win.pandoc_export_controller._runner = runner

                    def run_child():
                        holder["result"] = runner.run(
                            (str(fake), "--sleep"),
                            timeout_seconds=20.0,
                        )

                    thread = threading.Thread(
                        target=run_child,
                        name="calamus-pandoc-worker",
                        daemon=False,
                    )
                    win.pandoc_export_runtime._thread = thread
                    thread.start()
                    deadline = time.monotonic() + 4.0
                    while runner.active_pid is None and time.monotonic() < deadline:
                        pump()
                        time.sleep(0.01)
                    pid = runner.active_pid
                    self.assertIsNotNone(pid)

                    self.assertTrue(win.request_application_close())
                    pump()
                    thread.join(4.0)
                    self.assertFalse(thread.is_alive())
                    self.assertEqual(holder["result"].status, "cancelled")
                    self.assertIsNone(runner.active_pid)
                    with self.assertRaises(ProcessLookupError):
                        os.kill(pid, 0)
                    self.assertFalse(win.get_visible())
                    print("W90_TRUE_APP_ACTIVE_PANDOC_CLOSE=PASS")
                    print("W90_TRUE_APP_NO_SURVIVING_PANDOC=PASS")
                finally:
                    runner.cancel_active()
                    close_visible_dialogs()
                    if win.get_visible():
                        win.destroy()
                    pump()


if __name__ == "__main__":
    unittest.main()
