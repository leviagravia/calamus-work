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


    def test_text_stats_matches_editor_paragraph_delimiters(self):
        text = "one\r\ntwo\rthree\u2029four\nfive"
        self.assertEqual(search.text_stats(text), (5, len(text), 5))
        self.assertEqual(search.text_buffer_line_count(text), 5)

    def test_search_case_and_whole_word(self):
        text = "casa casale Casa"
        self.assertEqual(len(search.search_matches(text, "casa", match_case=False)), 3)
        self.assertEqual(len(search.search_matches(text, "casa", match_case=True)), 2)
        self.assertEqual(len(search.search_matches(text, "casa", whole_word=True)), 2)

    def test_choose_search_match_forward_and_wrap(self):
        matches = search.search_matches("alpha beta alpha", "alpha")
        self.assertEqual(search.choose_search_match(matches, 0).start(), 0)
        self.assertEqual(search.choose_search_match(matches, 1).start(), 11)
        self.assertEqual(search.choose_search_match(matches, 99).start(), 0)
        self.assertIsNone(search.choose_search_match(matches, 99, wrap=False))

    def test_choose_search_match_backward_and_wrap(self):
        matches = search.search_matches("alpha beta alpha", "alpha")
        self.assertEqual(search.choose_search_match(matches, 99, backwards=True).start(), 11)
        self.assertEqual(search.choose_search_match(matches, 11, backwards=True).start(), 0)
        self.assertEqual(search.choose_search_match(matches, 0, backwards=True).start(), 11)
        self.assertIsNone(search.choose_search_match(matches, 0, backwards=True, wrap=False))

    def test_choose_search_match_empty(self):
        self.assertIsNone(search.choose_search_match([], 0))

    def test_prepare_current_replacement_success(self):
        plan = search.prepare_current_replacement("alpha beta", "alpha", "omega", (0, 5))
        self.assertEqual(plan, (0, 5, "omega", (0, 5)))

    def test_prepare_current_replacement_case_modes(self):
        self.assertEqual(
            search.prepare_current_replacement("Alpha beta", "alpha", "omega", (0, 5), match_case=False),
            (0, 5, "omega", (0, 5)),
        )
        self.assertIsNone(
            search.prepare_current_replacement("Alpha beta", "alpha", "omega", (0, 5), match_case=True)
        )

    def test_prepare_current_replacement_whole_word_boundaries(self):
        self.assertEqual(
            search.prepare_current_replacement("alpha beta", "alpha", "omega", (0, 5), whole_word=True),
            (0, 5, "omega", (0, 5)),
        )
        self.assertIsNone(
            search.prepare_current_replacement("alphabet beta", "alpha", "omega", (0, 5), whole_word=True)
        )

    def test_prepare_current_replacement_rejects_invalid_state(self):
        self.assertIsNone(search.prepare_current_replacement("alpha", "", "omega", (0, 5)))
        self.assertIsNone(search.prepare_current_replacement("alpha", "alpha", "omega", None))
        self.assertIsNone(search.prepare_current_replacement("alpha", "alpha", "omega", (-1, 5)))
        self.assertIsNone(search.prepare_current_replacement("alpha", "alpha", "omega", (0, 99)))
        self.assertIsNone(search.prepare_current_replacement("alpha", "alpha", "omega", (4, 2)))
        self.assertIsNone(search.prepare_current_replacement("alpha", "beta", "omega", (0, 5)))

    def test_prepare_replace_all_plan_success(self):
        new_text, count = search.prepare_replace_all_plan("alpha beta alpha", "alpha", "omega")
        self.assertEqual(new_text, "omega beta omega")
        self.assertEqual(count, 2)

    def test_prepare_replace_all_plan_empty_needle_is_noop(self):
        new_text, count = search.prepare_replace_all_plan("alpha", "", "omega")
        self.assertEqual(new_text, "alpha")
        self.assertEqual(count, 0)

    def test_prepare_replace_all_plan_case_modes(self):
        self.assertEqual(
            search.prepare_replace_all_plan("Alpha alpha", "alpha", "omega", match_case=False),
            ("omega omega", 2),
        )
        self.assertEqual(
            search.prepare_replace_all_plan("Alpha alpha", "alpha", "omega", match_case=True),
            ("Alpha omega", 1),
        )

    def test_prepare_replace_all_plan_whole_word(self):
        self.assertEqual(
            search.prepare_replace_all_plan("alpha alphabet alpha", "alpha", "omega", whole_word=True),
            ("omega alphabet omega", 2),
        )

    def test_replace_all_literal_text(self):
        new, count = search.replace_all_literal_text("uno due uno", "uno", "tre")
        self.assertEqual((new, count), ("tre due tre", 2))


if __name__ == "__main__":
    unittest.main()


class SearchSessionAndFindAllTests(unittest.TestCase):
    def test_typed_query_and_session_are_immutable(self):
        options = search.SearchOptions(match_case=True, whole_word=True, wrap=False)
        query = search.SearchQuery("Alpha", options)
        session = search.SearchSession(query=query, current_match=(4, 9))
        self.assertEqual(session.query.text, "Alpha")
        self.assertEqual(session.current_match, (4, 9))
        with self.assertRaises(Exception):
            session.current_match = None

    def test_options_reject_python_truthiness(self):
        with self.assertRaises(TypeError):
            search.SearchOptions(match_case=1)
        with self.assertRaises(TypeError):
            search.SearchOptions(whole_word="yes")
        with self.assertRaises(TypeError):
            search.SearchOptions(wrap=None)

    def test_query_builder_and_repeat_support_typed_query(self):
        query = search.build_search_query(
            "alpha", match_case=True, whole_word=False, wrap=False
        )
        self.assertEqual(query.text, "alpha")
        self.assertTrue(query.options.match_case)
        self.assertFalse(query.options.wrap)
        self.assertTrue(search.can_repeat_search(query))
        self.assertFalse(search.can_repeat_search(search.SearchQuery()))

    def test_find_all_results_report_line_column_context_and_offsets(self):
        text = "alpha one\nsecond alpha here\nalpha"
        query = search.build_search_query("alpha")
        results = search.build_search_results(text, query)
        self.assertEqual(
            [(r.line, r.column, r.start, r.end) for r in results],
            [(1, 1, 0, 5), (2, 8, 17, 22), (3, 1, 28, 33)],
        )
        self.assertEqual(results[0].context, "alpha one")
        self.assertEqual(results[1].context, "second alpha here")
        self.assertEqual(results[2].context, "alpha")


    def test_find_all_coordinates_match_editor_line_delimiters(self):
        text = "one\r\ntwo\rthree\u2029four\nBottom bar:"
        query = search.build_search_query("Bottom bar")
        result = search.build_search_results(text, query)[0]
        self.assertEqual((result.line, result.column), (5, 1))
        self.assertEqual(result.context, "Bottom bar:")

    def test_find_all_counts_repeated_carriage_return_lines_like_gutter(self):
        text = "head" + ("\rblank" * 8) + "\rBottom bar:"
        query = search.build_search_query("Bottom bar")
        result = search.build_search_results(text, query)[0]
        self.assertEqual((result.line, result.column), (10, 1))
        self.assertEqual(search.text_stats(text)[2], 10)

    def test_find_all_respects_case_and_whole_word(self):
        text = "Alpha alpha alphabet alpha"
        query = search.build_search_query(
            "alpha", match_case=True, whole_word=True
        )
        results = search.build_search_results(text, query)
        self.assertEqual([(r.start, r.end) for r in results], [(6, 11), (21, 26)])

    def test_find_all_context_is_bounded_around_match(self):
        text = ("x" * 80) + " target " + ("y" * 80)
        query = search.build_search_query("target")
        result = search.build_search_results(text, query, context_limit=40)[0]
        self.assertLessEqual(len(result.context), 42)
        self.assertIn("target", result.context)
        self.assertTrue(result.context.startswith("…"))
        self.assertTrue(result.context.endswith("…"))

    def test_find_all_context_limit_is_validated(self):
        with self.assertRaises(ValueError):
            search.build_search_results(
                "alpha", search.build_search_query("alpha"), context_limit=10
            )

    def test_search_result_rejects_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            search.SearchResult(start=4, end=2, line=1, column=1, context="x")
        with self.assertRaises(ValueError):
            search.SearchResult(start=0, end=1, line=0, column=1, context="x")
