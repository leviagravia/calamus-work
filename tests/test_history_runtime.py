import unittest

from calamus_history import HistoryState, TextHistory
from calamus_history_runtime import (
    SnapshotHistoryRuntime,
    capture_buffer_state,
    compute_vertical_reveal,
    restore_buffer_state,
)


class _Iter:
    def __init__(self, offset):
        self._offset = offset

    def get_offset(self):
        return self._offset


class _Mark:
    def __init__(self, name):
        self.name = name


class _Rect:
    def __init__(self, x=0, y=0, width=1, height=16):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class _Buffer:
    def __init__(self, text="", insert=0, bound=0):
        self.text = text
        self.insert = insert
        self.bound = bound
        self._insert_mark = _Mark("insert")
        self._bound_mark = _Mark("bound")

    def get_bounds(self):
        return _Iter(0), _Iter(len(self.text))

    def get_text(self, _start, _end, _include_hidden):
        return self.text

    def get_insert(self):
        return self._insert_mark

    def get_selection_bound(self):
        return self._bound_mark

    def get_iter_at_mark(self, mark):
        return _Iter(self.insert if mark is self._insert_mark else self.bound)

    def get_iter_at_offset(self, offset):
        return _Iter(max(0, min(offset, len(self.text))))

    def set_text(self, text):
        self.text = text
        self.insert = self.bound = 0

    def select_range(self, insert, bound):
        self.insert = insert.get_offset()
        self.bound = bound.get_offset()


class _Adjustment:
    def __init__(self, *, lower=0, upper=12000, page_size=600, value=0):
        self.lower = lower
        self.upper = upper
        self.page_size = page_size
        self.value = value
        self.handlers = {}
        self.next_handler = 1

    def connect(self, signal, callback):
        handler = self.next_handler
        self.next_handler += 1
        self.handlers[handler] = (signal, callback)
        return handler

    def disconnect(self, handler):
        self.handlers.pop(handler, None)

    def emit_changed(self):
        for signal, callback in list(self.handlers.values()):
            if signal == "changed":
                callback(self)

    def get_lower(self):
        return self.lower

    def get_upper(self):
        return self.upper

    def get_page_size(self):
        return self.page_size

    def set_value(self, value):
        maximum = max(self.lower, self.upper - self.page_size)
        self.value = max(self.lower, min(value, maximum))


class _Scroller:
    def __init__(self, adjustment=None):
        self.adjustment = adjustment or _Adjustment()

    def get_vadjustment(self):
        return self.adjustment


class _View:
    def __init__(self, buffer, *, caret_y=0, visible_y=0, visible_height=600):
        self.buffer = buffer
        self.caret_y = caret_y
        self.visible_y = visible_y
        self.visible_height = visible_height
        self.handlers = {}
        self.next_handler = 1

    def get_buffer(self):
        return self.buffer

    def connect(self, signal, callback):
        handler = self.next_handler
        self.next_handler += 1
        self.handlers[handler] = (signal, callback)
        return handler

    def disconnect(self, handler):
        self.handlers.pop(handler, None)

    def emit_size_allocate(self):
        for signal, callback in list(self.handlers.values()):
            if signal == "size-allocate":
                callback(self, None)

    def get_iter_location(self, _iterator):
        return _Rect(y=self.caret_y, height=16)

    def get_visible_rect(self):
        return _Rect(y=self.visible_y, height=self.visible_height)

    def get_top_margin(self):
        return 10


class _GLib:
    PRIORITY_LOW = 300

    def __init__(self):
        self.next_id = 1
        self.callbacks = {}

    def timeout_add(self, _delay, callback):
        source = self.next_id
        self.next_id += 1
        self.callbacks[source] = callback
        return source

    def idle_add(self, callback, priority=None):
        source = self.next_id
        self.next_id += 1
        self.callbacks[source] = (callback, priority)
        return source

    def source_remove(self, source):
        self.callbacks.pop(source, None)

    def run(self, source):
        callback = self.callbacks.pop(source)
        if isinstance(callback, tuple):
            callback = callback[0]
        return callback()


class HistoryRuntimeTests(unittest.TestCase):
    def test_capture_and_restore_preserve_selection_direction(self):
        buffer = _Buffer("alpha beta", insert=10, bound=6)
        view = _View(buffer)
        state = capture_buffer_state(view)
        self.assertEqual(state, HistoryState("alpha beta", 10, 6))
        buffer.text = "changed"
        restore_buffer_state(view, state)
        self.assertEqual((buffer.text, buffer.insert, buffer.bound), ("alpha beta", 10, 6))

    def test_debounced_group_keeps_pre_edit_and_post_edit_marks(self):
        buffer = _Buffer("ab", insert=1, bound=1)
        view = _View(buffer)
        glib = _GLib()
        history = TextHistory()
        runtime = SnapshotHistoryRuntime(history, view, _Scroller(), glib, lambda *_: None)
        runtime.reset()
        runtime.begin_user_action()
        buffer.text = "aXb"
        buffer.insert = buffer.bound = 2
        runtime.end_user_action()
        runtime.flush()
        target = runtime.undo_target()
        self.assertEqual(target, HistoryState("ab", 1, 1))
        self.assertEqual(runtime.redo_target(), HistoryState("aXb", 2, 2))

    def test_navigation_does_not_add_undo_but_pre_command_state_is_refreshable(self):
        buffer = _Buffer("abc", insert=0, bound=0)
        view = _View(buffer)
        history = TextHistory()
        runtime = SnapshotHistoryRuntime(history, view, _Scroller(), _GLib(), lambda *_: None)
        runtime.reset()
        buffer.insert = buffer.bound = 2
        runtime.prepare_command()
        self.assertEqual(history.current, HistoryState("abc", 2, 2))
        buffer.text = "abXc"
        buffer.insert = buffer.bound = 3
        runtime.finalize_command()
        self.assertEqual(runtime.undo_target(), HistoryState("abc", 2, 2))

    def test_projection_centers_caret_only_when_outside_safe_viewport(self):
        self.assertIsNone(
            compute_vertical_reveal(
                caret_y=200,
                caret_height=16,
                visible_y=0,
                visible_height=600,
                lower=0,
                upper=12000,
                page_size=600,
            )
        )
        value = compute_vertical_reveal(
            caret_y=11381,
            caret_height=16,
            visible_y=-10,
            visible_height=647,
            lower=0,
            upper=12050,
            page_size=647,
            top_margin=10,
        )
        self.assertGreater(value, 10_000)
        self.assertLessEqual(value, 12_050 - 647)

    def test_reveal_waits_for_adjustment_geometry_then_sets_value(self):
        buffer = _Buffer("x" * 100, insert=100, bound=100)
        adjustment = _Adjustment(upper=500, page_size=400)
        view = _View(buffer, caret_y=1200, visible_y=0, visible_height=400)
        glib = _GLib()
        runtime = SnapshotHistoryRuntime(
            TextHistory(), view, _Scroller(adjustment), glib, lambda *_: None
        )
        runtime.queue_scroll_to_insert()
        first = runtime.scroll_source
        glib.run(first)
        self.assertTrue(runtime.reveal_pending)
        self.assertEqual(adjustment.value, 0)

        adjustment.upper = 1600
        adjustment.emit_changed()
        second = runtime.scroll_source
        self.assertIsNotNone(second)
        glib.run(second)
        self.assertFalse(runtime.reveal_pending)
        self.assertGreater(adjustment.value, 800)

    def test_reveal_request_is_replaceable_and_shutdown_disconnects_handlers(self):
        buffer = _Buffer("abc", insert=3, bound=3)
        adjustment = _Adjustment()
        view = _View(buffer, caret_y=1000)
        glib = _GLib()
        runtime = SnapshotHistoryRuntime(
            TextHistory(), view, _Scroller(adjustment), glib, lambda *_: None
        )
        runtime.queue_scroll_to_insert(0.02)
        first = runtime.scroll_source
        runtime.queue_scroll_to_insert(0.20)
        self.assertNotIn(first, glib.callbacks)
        self.assertAlmostEqual(runtime.reveal_margin, 0.20)
        runtime.shutdown()
        self.assertFalse(runtime.reveal_pending)
        self.assertFalse(adjustment.handlers)
        self.assertFalse(view.handlers)


if __name__ == "__main__":
    unittest.main()
