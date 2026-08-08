import unittest

from calamus_clip_runtime import insert_clip_expansion_through_gateway, selected_document_text_from_view


class _Iter:
    def __init__(self, offset):
        self._offset = offset

    def get_offset(self):
        return self._offset


class _Buffer:
    def __init__(self, text="", selection=None, cursor=0):
        self.text = text
        self.selection = selection
        self.cursor = cursor
        self.inserted = []

    def get_has_selection(self):
        return self.selection is not None

    def get_selection_bounds(self):
        start, end = self.selection
        return _Iter(start), _Iter(end)

    def get_text(self, start, end, _include_hidden):
        return self.text[start.get_offset():end.get_offset()]

    def insert_at_cursor(self, text):
        self.inserted.append(text)


class _TextView:
    def __init__(self, buffer):
        self._buffer = buffer
        self.focused = False

    def get_buffer(self):
        return self._buffer

    def grab_focus(self):
        self.focused = True


class _App:
    def __init__(self, buffer):
        self.text = _TextView(buffer)
        self.commands = []
        self.cursor_offsets = []
        self.scroll_margins = []
        self.history_syncs = 0

    def get_cursor_offset(self):
        return self.text.get_buffer().cursor

    def execute_command(self, name, edit, select_range=None):
        self.commands.append((name, select_range))
        edit(self.text.get_buffer())
        return True

    def set_cursor_offset(self, offset):
        self.cursor_offsets.append(offset)

    def queue_insert_scroll(self, margin=0.02):
        self.scroll_margins.append(margin)

    def sync_history_view_state(self):
        self.history_syncs += 1


class ClipRuntimeGatewayTests(unittest.TestCase):
    def test_selected_document_text_is_read_only(self):
        buffer = _Buffer("alpha beta", selection=(6, 10))
        app = _App(buffer)
        self.assertEqual(selected_document_text_from_view(app.text), "beta")
        self.assertEqual(buffer.inserted, [])

    def test_selected_document_text_requires_a_selection(self):
        self.assertEqual(selected_document_text_from_view(_App(_Buffer("alpha")).text), "")

    def test_insert_uses_one_command_and_places_caret_from_cursor(self):
        buffer = _Buffer(cursor=4)
        app = _App(buffer)
        self.assertTrue(insert_clip_expansion_through_gateway(app.text, "ABCD", 2, execute_command=app.execute_command, get_cursor_offset=app.get_cursor_offset, set_cursor_offset=app.set_cursor_offset, sync_history_view_state=app.sync_history_view_state, queue_insert_scroll=app.queue_insert_scroll))
        self.assertEqual(buffer.inserted, ["ABCD"])
        self.assertEqual(app.commands, [("Insert Clip", None)])
        self.assertEqual(app.cursor_offsets, [6])
        self.assertEqual(app.scroll_margins, [0.15])
        self.assertEqual(app.history_syncs, 1)
        self.assertTrue(app.text.focused)

    def test_insert_uses_selection_start_and_clamps_cursor_offset(self):
        buffer = _Buffer(selection=(3, 8))
        app = _App(buffer)
        self.assertTrue(insert_clip_expansion_through_gateway(app.text, "XYZ", 99, execute_command=app.execute_command, get_cursor_offset=app.get_cursor_offset, set_cursor_offset=app.set_cursor_offset, sync_history_view_state=app.sync_history_view_state, queue_insert_scroll=app.queue_insert_scroll))
        self.assertEqual(app.commands, [("Insert Clip", None)])
        self.assertEqual(app.cursor_offsets, [6])

    def test_non_text_is_rejected_before_command_gateway(self):
        app = _App(_Buffer())
        self.assertFalse(insert_clip_expansion_through_gateway(app.text, None, 0, execute_command=app.execute_command, get_cursor_offset=app.get_cursor_offset, set_cursor_offset=app.set_cursor_offset, sync_history_view_state=app.sync_history_view_state, queue_insert_scroll=app.queue_insert_scroll))
        self.assertEqual(app.commands, [])


if __name__ == "__main__":
    unittest.main()
