from __future__ import annotations

import unittest

from calamus_document_session import DocumentSession
from calamus_document_session_controller import DocumentSessionController, DocumentSessionPorts
from calamus_editor_buffer_adapter import EditorBufferAdapter
from calamus_editor_transaction import EditorChangeKind, EditorTransactionController
from calamus_history import HistoryState, TextHistory
from calamus_history_runtime import SnapshotHistoryRuntime
from calamus_model import Document


class _Iter:
    def __init__(self, offset):
        self.offset = int(offset)

    def get_offset(self):
        return self.offset


class _Mark:
    def __init__(self, name):
        self.name = name


class _Buffer:
    def __init__(self, text="", insert=0, bound=0):
        self.text = text
        self.insert_offset = insert
        self.bound_offset = bound
        self.insert_mark = _Mark("insert")
        self.bound_mark = _Mark("bound")
        self.begin_count = 0
        self.end_count = 0

    def get_bounds(self):
        return _Iter(0), _Iter(len(self.text))

    def get_text(self, start, end, _hidden):
        return self.text[start.get_offset():end.get_offset()]

    def get_insert(self):
        return self.insert_mark

    def get_selection_bound(self):
        return self.bound_mark

    def get_iter_at_mark(self, mark):
        return _Iter(self.insert_offset if mark is self.insert_mark else self.bound_offset)

    def get_iter_at_offset(self, offset):
        return _Iter(max(0, min(int(offset), len(self.text))))

    def get_char_count(self):
        return len(self.text)

    def get_start_iter(self):
        return _Iter(0)

    def begin_user_action(self):
        self.begin_count += 1

    def end_user_action(self):
        self.end_count += 1

    def set_text(self, text):
        self.text = text
        self.insert_offset = self.bound_offset = 0

    def select_range(self, insert, bound):
        self.insert_offset = insert.get_offset()
        self.bound_offset = bound.get_offset()

    def delete(self, start, end):
        a, b = sorted((start.get_offset(), end.get_offset()))
        self.text = self.text[:a] + self.text[b:]
        self.insert_offset = self.bound_offset = a

    def insert(self, where, text):
        offset = where.get_offset()
        self.text = self.text[:offset] + text + self.text[offset:]
        self.insert_offset = self.bound_offset = offset + len(text)


class _View:
    def __init__(self, buffer):
        self.buffer = buffer

    def get_buffer(self):
        return self.buffer


class _GLib:
    def __init__(self):
        self.next_id = 1
        self.callbacks = {}

    def timeout_add(self, _delay, callback):
        ident = self.next_id
        self.next_id += 1
        self.callbacks[ident] = callback
        return ident

    def source_remove(self, ident):
        self.callbacks.pop(ident, None)


class _Viewport:
    scroll_source = None
    reveal_pending = False
    applying_adjustment = False

    def queue_visible_to_insert(self, *_args, **_kwargs):
        return True

    def cancel(self):
        return None

    def shutdown(self):
        return None


class EditorTransactionTests(unittest.TestCase):
    def make_controller(self, text="abc", *, modified=False, insert=0, bound=0):
        buffer = _Buffer(text, insert=insert, bound=bound)
        view = _View(buffer)
        history = TextHistory(max_steps=100)
        runtime = SnapshotHistoryRuntime(
            history,
            view,
            None,
            _GLib(),
            lambda *_: None,
            viewport_runtime=_Viewport(),
        )
        runtime.reset()
        session = DocumentSession(Document(text=text, modified=modified))
        session_controller = DocumentSessionController(
            session,
            DocumentSessionPorts(
                read_buffer_text=lambda: buffer.text,
                replace_buffer_text=buffer.set_text,
                reset_undo_history=runtime.reset,
                read_text_file=lambda _path: "",
                write_text_file=lambda _path, _text: None,
                is_large_text_file=lambda _path: False,
            ),
        )
        adapter = EditorBufferAdapter(view)
        controller = EditorTransactionController(
            session=session,
            session_controller=session_controller,
            history_runtime=runtime,
            buffer_adapter=adapter,
        )
        return controller, adapter, runtime, session, buffer

    def test_one_programmatic_command_is_one_undo_unit_and_syncs_session(self):
        tx, _adapter, runtime, session, buffer = self.make_controller("abc", insert=3, bound=3)

        def edit(buf):
            buf.insert(buf.get_iter_at_offset(3), "X")

        result = tx.execute_command("Insert", edit)
        self.assertTrue(result.changed)
        self.assertEqual(buffer.text, "abcX")
        self.assertEqual(session.text, "abcX")
        self.assertTrue(session.modified)
        self.assertEqual(buffer.begin_count, 1)
        self.assertEqual(buffer.end_count, 1)
        self.assertEqual(len(runtime.history.undo_stack), 2)

        undone = tx.undo()
        self.assertIsNotNone(undone)
        self.assertEqual(buffer.text, "abc")
        self.assertEqual((buffer.insert_offset, buffer.bound_offset), (3, 3))
        redone = tx.redo()
        self.assertIsNotNone(redone)
        self.assertEqual(buffer.text, "abcX")

    def test_partial_failure_rolls_back_buffer_history_and_session_exactly(self):
        tx, _adapter, runtime, session, buffer = self.make_controller(
            "alpha", modified=False, insert=2, bound=4
        )
        before_history = (tuple(runtime.history.undo_stack), tuple(runtime.history.redo_stack))
        before_revision = session.revision

        def edit(buf):
            buf.insert(buf.get_iter_at_offset(2), "BROKEN")
            raise RuntimeError("boom")

        with self.assertRaisesRegex(RuntimeError, "boom"):
            tx.execute_command("Broken", edit)

        self.assertEqual(buffer.text, "alpha")
        self.assertEqual((buffer.insert_offset, buffer.bound_offset), (2, 4))
        self.assertEqual((tuple(runtime.history.undo_stack), tuple(runtime.history.redo_stack)), before_history)
        self.assertEqual(session.text, "alpha")
        self.assertFalse(session.modified)
        self.assertEqual(session.revision, before_revision)
        self.assertFalse(tx.programmatic_active)
        self.assertFalse(tx.restoring)

    def test_noop_command_creates_no_undo_and_no_dirty_transition(self):
        tx, _adapter, runtime, session, _buffer = self.make_controller("abc")
        result = tx.execute_command("No-op", lambda _buf: None)
        self.assertFalse(result.changed)
        self.assertEqual(len(runtime.history.undo_stack), 1)
        self.assertFalse(session.modified)

    def test_nested_programmatic_transaction_fails_closed_and_outer_rolls_back(self):
        tx, _adapter, runtime, session, buffer = self.make_controller("abc", insert=3, bound=3)
        before = tuple(runtime.history.undo_stack)

        def outer(buf):
            buf.insert(buf.get_iter_at_offset(3), "X")
            tx.execute_command("Nested", lambda inner: inner.insert(inner.get_iter_at_offset(0), "Y"))

        with self.assertRaisesRegex(RuntimeError, "nested editor transactions"):
            tx.execute_command("Outer", outer)
        self.assertEqual(buffer.text, "abc")
        self.assertEqual(tuple(runtime.history.undo_stack), before)
        self.assertFalse(session.modified)

    def test_native_change_is_observed_but_replacement_and_programmatic_changes_are_not(self):
        tx, _adapter, runtime, session, buffer = self.make_controller("abc")
        buffer.text = "abcd"
        self.assertEqual(tx.observe_buffer_change(), EditorChangeKind.NATIVE)
        self.assertEqual(session.text, "abcd")
        self.assertTrue(session.modified)
        tx.flush()
        self.assertEqual(len(runtime.history.undo_stack), 2)

        with session.replacement():
            buffer.text = "opened"
            self.assertEqual(tx.observe_buffer_change(), EditorChangeKind.REPLACEMENT)
        self.assertEqual(session.text, "abcd")

        tx._programmatic_depth = 1
        try:
            buffer.text = "pending"
            self.assertEqual(tx.observe_buffer_change(), EditorChangeKind.PROGRAMMATIC)
        finally:
            tx._programmatic_depth = 0
        self.assertEqual(session.text, "abcd")

    def test_selection_after_is_part_of_committed_history_state(self):
        tx, _adapter, runtime, _session, buffer = self.make_controller("abcd", insert=0, bound=0)

        def edit(buf):
            buf.delete(buf.get_iter_at_offset(1), buf.get_iter_at_offset(3))
            buf.insert(buf.get_iter_at_offset(1), "XYZ")

        tx.execute_command("Replace", edit, select_range=(1, 4))
        self.assertEqual((buffer.insert_offset, buffer.bound_offset), (1, 4))
        self.assertEqual(runtime.history.current, HistoryState("aXYZd", 1, 4))

    def test_history_checkpoint_restores_model_and_pending_state(self):
        _tx, _adapter, runtime, _session, buffer = self.make_controller("abc")
        checkpoint = runtime.checkpoint()
        buffer.text = "changed"
        runtime.observe_changed(True)
        runtime.flush()
        self.assertEqual(runtime.history.current.text, "changed")
        runtime.restore_checkpoint(checkpoint)
        self.assertEqual(runtime.history.current.text, "abc")
        self.assertIsNone(runtime.before_state)
        self.assertIsNone(runtime.after_state)


if __name__ == "__main__":
    unittest.main()
