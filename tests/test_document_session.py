from pathlib import Path
import tempfile
import unittest

from calamus_document_session import (
    DocumentSession,
    DocumentSessionPhase,
)
from calamus_document_session_controller import (
    DocumentSessionController,
    DocumentSessionPorts,
)
from calamus_file_lifecycle import NewPlan, OpenPlan, SavePlan
from calamus_model import Document


class Harness:
    def __init__(self, *, replace_fail=False, write_fail=False):
        self.buffer = "old buffer"
        self.events = []
        self.replace_fail = replace_fail
        self.write_fail = write_fail
        self.files = {"/tmp/open.txt": "loaded text"}
        self.session = DocumentSession(
            Document(text="old text", file_path="/tmp/original.txt", modified=True)
        )
        self.controller = DocumentSessionController(
            self.session,
            DocumentSessionPorts(
                read_buffer_text=lambda: self.buffer,
                replace_buffer_text=self.replace,
                reset_undo_history=lambda: self.events.append(("reset",)),
                read_text_file=self.read,
                write_text_file=self.write,
                is_large_text_file=lambda path: path.endswith("large.txt"),
            ),
        )

    def replace(self, text):
        self.events.append(("replace", text, self.session.phase.value))
        if self.replace_fail:
            raise RuntimeError("replace failed")
        self.buffer = text

    def read(self, path):
        self.events.append(("read", path))
        if path not in self.files:
            raise OSError("read failed")
        return self.files[path]

    def write(self, path, text):
        self.events.append(("write", path, text))
        if self.write_fail:
            raise OSError("write failed")
        self.files[path] = text


class DocumentSessionTests(unittest.TestCase):
    def test_initial_snapshot_is_authoritative_and_gtk_free(self):
        h = Harness()
        snap = h.session.snapshot()
        self.assertEqual((snap.text, snap.file_path, snap.modified), ("old text", "/tmp/original.txt", True))
        self.assertEqual(snap.phase, DocumentSessionPhase.IDLE)

    def test_normal_change_synchronizes_and_marks_modified(self):
        h = Harness()
        h.session.mark_clean("old buffer")
        revision_before = h.session.revision
        h.buffer = "edited"
        self.assertTrue(h.controller.observe_buffer_change())
        self.assertEqual(h.session.text, "edited")
        self.assertTrue(h.session.modified)
        self.assertEqual(h.session.revision, revision_before + 1)

    def test_guarded_change_is_ignored_and_guard_unwinds(self):
        h = Harness()
        before = h.session.snapshot()
        with h.session.replacement(DocumentSessionPhase.OPENING):
            h.buffer = "signal text"
            self.assertFalse(h.controller.observe_buffer_change())
            self.assertTrue(h.session.loading)
        self.assertFalse(h.session.loading)
        self.assertEqual(h.session.snapshot().text, before.text)

    def test_guard_unwinds_after_exception(self):
        h = Harness()
        with self.assertRaises(RuntimeError):
            with h.session.replacement(DocumentSessionPhase.SAVING):
                raise RuntimeError("boom")
        self.assertEqual(h.session.phase, DocumentSessionPhase.IDLE)
        self.assertFalse(h.session.loading)

    def test_nested_guard_restores_outer_phase(self):
        h = Harness()
        with h.session.replacement(DocumentSessionPhase.OPENING):
            with h.session.replacement(DocumentSessionPhase.REPLACING):
                self.assertEqual(h.session.phase, DocumentSessionPhase.REPLACING)
            self.assertEqual(h.session.phase, DocumentSessionPhase.OPENING)
        self.assertEqual(h.session.phase, DocumentSessionPhase.IDLE)

    def test_new_replacement_failure_preserves_exact_snapshot(self):
        h = Harness(replace_fail=True)
        before = h.session.snapshot()
        with self.assertRaises(RuntimeError):
            h.controller.execute_new(NewPlan())
        self.assertEqual(h.session.snapshot(), before)
        self.assertFalse(h.session.loading)

    def test_new_success_commits_clean_untitled_after_replace(self):
        h = Harness()
        transition = h.controller.execute_new(NewPlan())
        self.assertEqual(h.events, [("replace", "", "replacing"), ("reset",)])
        self.assertIsNone(h.session.file_path)
        self.assertEqual(h.session.text, "")
        self.assertFalse(h.session.modified)
        self.assertTrue(transition.identity_changed)

    def test_open_read_failure_preserves_snapshot_and_never_replaces(self):
        h = Harness()
        before = h.session.snapshot()
        with self.assertRaises(OSError):
            h.controller.open_path("/tmp/missing.txt")
        self.assertEqual(h.session.snapshot(), before)
        self.assertEqual(h.events, [("read", "/tmp/missing.txt")])

    def test_open_replace_failure_preserves_snapshot(self):
        h = Harness(replace_fail=True)
        before = h.session.snapshot()
        with self.assertRaises(RuntimeError):
            h.controller.execute_open(OpenPlan("/tmp/open.txt", "loaded text"))
        self.assertEqual(h.session.snapshot(), before)
        self.assertFalse(h.session.loading)

    def test_open_success_commits_identity_after_replace(self):
        h = Harness()
        plan, transition = h.controller.open_path("/tmp/open.txt")
        self.assertEqual(plan.target_path, "/tmp/open.txt")
        self.assertEqual(h.events[0], ("read", "/tmp/open.txt"))
        self.assertEqual(h.events[1], ("replace", "loaded text", "opening"))
        self.assertEqual(h.session.file_path, "/tmp/open.txt")
        self.assertFalse(h.session.modified)
        self.assertTrue(transition.identity_changed)

    def test_large_file_flag_is_preserved(self):
        h = Harness()
        h.files["/tmp/large.txt"] = "x"
        plan, _ = h.controller.open_path("/tmp/large.txt")
        self.assertTrue(plan.large_file)

    def test_save_write_failure_preserves_identity_and_dirty(self):
        h = Harness(write_fail=True)
        before = h.session.snapshot()
        plan = SavePlan(False, "/tmp/new.txt", "old buffer", "old buffer")
        with self.assertRaises(OSError):
            h.controller.execute_save(plan)
        after = h.session.snapshot()
        self.assertEqual(after.file_path, before.file_path)
        self.assertEqual(after.modified, before.modified)

    def test_save_success_commits_identity_and_clean_state(self):
        h = Harness()
        plan = SavePlan(False, "/tmp/new.txt", "old buffer", "old buffer")
        transition = h.controller.execute_save(plan)
        self.assertEqual(h.files["/tmp/new.txt"], "old buffer")
        self.assertEqual(h.session.file_path, "/tmp/new.txt")
        self.assertFalse(h.session.modified)
        self.assertTrue(transition.identity_changed)

    def test_normalization_write_failure_preserves_path_dirty_but_updates_text(self):
        h = Harness(write_fail=True)
        plan = SavePlan(False, "/tmp/new.txt", "Body   \n", "Body\n")
        with self.assertRaises(OSError):
            h.controller.execute_save(plan)
        self.assertEqual(h.buffer, "Body\n")
        self.assertEqual(h.session.text, "Body\n")
        self.assertEqual(h.session.file_path, "/tmp/original.txt")
        self.assertTrue(h.session.modified)
        self.assertFalse(h.session.loading)

    def test_save_plan_without_target_is_rejected_without_write(self):
        h = Harness()
        with self.assertRaises(ValueError):
            h.controller.execute_save(SavePlan(True, None, "x", "x"))
        self.assertEqual(h.events, [])

    def test_rebind_preserves_text_and_dirty(self):
        h = Harness()
        before = h.session.snapshot()
        h.session.rebind_path("/tmp/renamed.txt")
        self.assertEqual(h.session.text, before.text)
        self.assertEqual(h.session.modified, before.modified)
        self.assertEqual(h.session.file_path, "/tmp/renamed.txt")

    def test_detach_preserves_visible_text_and_marks_modified(self):
        h = Harness()
        h.session.detach("visible")
        self.assertIsNone(h.session.file_path)
        self.assertEqual(h.session.text, "visible")
        self.assertTrue(h.session.modified)

    def test_capture_buffer_text_does_not_change_dirty_state(self):
        h = Harness()
        h.session.mark_clean()
        h.buffer = "captured"
        self.assertEqual(h.controller.capture_buffer_text(), "captured")
        self.assertEqual(h.session.text, "captured")
        self.assertFalse(h.session.modified)

    def test_replace_current_text_resets_undo_only_after_success(self):
        h = Harness()
        h.controller.replace_current_text("replacement", modified=True)
        self.assertEqual(h.events, [("replace", "replacement", "replacing"), ("reset",)])
        self.assertTrue(h.session.modified)

    def test_close_confirmation_follows_authoritative_dirty_state(self):
        h = Harness()
        self.assertTrue(h.session.requires_save_confirmation())
        h.session.mark_clean()
        self.assertFalse(h.session.requires_save_confirmation())

    def test_snapshot_is_frozen(self):
        h = Harness()
        snap = h.session.snapshot()
        with self.assertRaises((AttributeError, TypeError)):
            snap.modified = False


if __name__ == "__main__":
    unittest.main()
