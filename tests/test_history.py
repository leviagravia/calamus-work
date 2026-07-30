import unittest

from calamus_history import HistoryState, TextHistory


class HistoryTests(unittest.TestCase):
    def test_undo_redo_restores_exact_caret_and_selection_direction(self):
        h = TextHistory(max_steps=5)
        initial = HistoryState("alpha beta", 5, 0)
        edited = HistoryState("alpha X beta", 7, 7)
        h.reset(initial)
        self.assertTrue(h.commit(edited))
        self.assertEqual(h.undo(HistoryState(edited.text, 0, 0)), initial)
        self.assertEqual(h.redo(), edited)

    def test_duplicate_text_does_not_create_navigation_only_undo(self):
        h = TextHistory()
        h.reset(HistoryState("same", 0, 0))
        self.assertFalse(h.commit(HistoryState("same", 4, 4)))
        self.assertFalse(h.can_undo)
        self.assertTrue(h.replace_current_view_state(HistoryState("same", 4, 1)))
        self.assertEqual(h.current, HistoryState("same", 4, 1))

    def test_large_document_limits_history(self):
        h = TextHistory(max_snapshot_chars=4)
        h.reset(HistoryState("12345", 5, 5))
        self.assertIsNotNone(h.disabled_reason)
        self.assertFalse(h.commit(HistoryState("123456", 6, 6)))
        self.assertIsNone(h.undo(HistoryState("123456", 6, 6)))

    def test_total_history_is_trimmed_by_text_size(self):
        h = TextHistory(max_steps=100, max_total_chars=6)
        h.reset("a")
        h.commit("ab")
        h.commit("abc")
        h.commit("abcd")
        self.assertLessEqual(sum(len(x.text) for x in h.undo_stack), 6)

    def test_offsets_are_clamped_to_snapshot_text(self):
        self.assertEqual(HistoryState("abc", 99, -3), HistoryState("abc", 3, 0))


if __name__ == "__main__":
    unittest.main()
