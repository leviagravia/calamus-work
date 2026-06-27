import unittest

import calamus_search as search


class SearchTests(unittest.TestCase):
    def test_repeat_search_query_helpers(self):
        self.assertEqual(search.normalize_search_query(None), "")
        self.assertEqual(search.normalize_search_query("alpha"), "alpha")
        self.assertEqual(search.normalize_search_query(123), "123")
        self.assertFalse(search.can_repeat_search(None))
        self.assertFalse(search.can_repeat_search(""))
        self.assertTrue(search.can_repeat_search("alpha"))
        self.assertTrue(search.can_repeat_search(123))

    def test_text_stats(self):
        self.assertEqual(search.text_stats("uno due\ntre"), (3, 11, 2))
        self.assertEqual(search.text_stats(""), (0, 0, 1))

    def test_search_case_and_whole_word(self):
        text = "casa casale Casa"
        self.assertEqual(len(search.search_matches(text, "casa", match_case=False)), 3)
        self.assertEqual(len(search.search_matches(text, "casa", match_case=True)), 2)
        self.assertEqual(len(search.search_matches(text, "casa", whole_word=True)), 2)

    def test_replace_all_literal_text(self):
        new, count = search.replace_all_literal_text("uno due uno", "uno", "tre")
        self.assertEqual((new, count), ("tre due tre", 2))


if __name__ == "__main__":
    unittest.main()
