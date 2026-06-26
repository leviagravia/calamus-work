import unittest

from calamus_history import TextHistory


class HistoryTests(unittest.TestCase):
    def test_undo_redo(self):
        h = TextHistory(max_steps=5)
        h.reset("a")
        self.assertTrue(h.commit("ab"))
        self.assertTrue(h.commit("abc"))
        self.assertEqual(h.undo("abc"), "ab")
        self.assertEqual(h.redo(), "abc")

    def test_duplicate_commits_are_ignored(self):
        h = TextHistory()
        h.reset("same")
        self.assertFalse(h.commit("same"))
        self.assertFalse(h.can_undo)

    def test_large_document_limits_history(self):
        h = TextHistory(max_snapshot_chars=4)
        h.reset("12345")
        self.assertIsNotNone(h.disabled_reason)
        self.assertFalse(h.commit("123456"))
        self.assertIsNone(h.undo("123456"))

    def test_total_history_is_trimmed(self):
        h = TextHistory(max_steps=100, max_total_chars=6)
        h.reset("a")
        h.commit("ab")
        h.commit("abc")
        h.commit("abcd")
        self.assertLessEqual(sum(len(x) for x in h.undo_stack), 6)


if __name__ == "__main__":
    unittest.main()
