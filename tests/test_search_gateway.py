import unittest

from calamus_search import SearchResult
from calamus_search_gateway import SearchController


class FakeAdapter:
    def __init__(self, text="", cursor=0, selection=None, coordinates=None):
        self.text_value = text
        self.cursor = cursor
        self.selection = selection
        self.coordinates = dict(coordinates or {})
        self.highlights = []
        self.selected = None
        self.clear_calls = 0

    def text(self):
        return self.text_value

    def cursor_offset(self, *, backwards=False):
        if self.selection is not None:
            return self.selection[0] if backwards else self.selection[1]
        return self.cursor

    def clear_highlights(self):
        self.clear_calls += 1
        self.highlights = []

    def apply_highlights(self, spans):
        self.clear_highlights()
        self.highlights = list(spans)
        return len(self.highlights)

    def select_span(self, start, end):
        self.selected = (start, end)
        self.selection = (start, end)

    def line_column_for_offset(self, offset):
        if offset in self.coordinates:
            return self.coordinates[offset]
        prefix = self.text_value[:offset]
        line = prefix.count("\n") + 1
        last_break = prefix.rfind("\n")
        column = offset + 1 if last_break < 0 else offset - last_break
        return line, column


class SearchControllerTests(unittest.TestCase):
    def test_requires_search_view_protocol(self):
        with self.assertRaises(TypeError):
            SearchController(object())

    def test_find_highlight_and_repeat_share_one_query_options(self):
        adapter = FakeAdapter("Alpha alpha alphabet alpha", cursor=0)
        controller = SearchController(adapter)
        count = controller.highlight(
            "alpha", match_case=True, whole_word=True, wrap=False
        )
        self.assertEqual(count, 2)
        self.assertEqual(adapter.highlights, [(6, 11), (21, 26)])
        self.assertTrue(controller.find())
        self.assertEqual(adapter.selected, (6, 11))
        self.assertTrue(controller.query.options.match_case)
        self.assertTrue(controller.query.options.whole_word)
        self.assertFalse(controller.query.options.wrap)
        self.assertTrue(controller.repeat())
        self.assertEqual(adapter.selected, (21, 26))
        self.assertFalse(controller.repeat())

    def test_backward_find_uses_selection_start(self):
        adapter = FakeAdapter("alpha beta alpha", selection=(11, 16))
        controller = SearchController(adapter)
        controller.configure("alpha")
        self.assertTrue(controller.find(backwards=True))
        self.assertEqual(adapter.selected, (0, 5))

    def test_find_all_uses_view_authoritative_coordinates_and_builds_navigation(self):
        adapter = FakeAdapter(
            "alpha one\nsecond alpha",
            coordinates={17: (315, 8)},
        )
        controller = SearchController(adapter)
        results = controller.find_all("alpha")
        self.assertEqual(len(results), 2)
        self.assertEqual(adapter.highlights, [(0, 5), (17, 22)])
        self.assertEqual((results[1].line, results[1].column), (315, 8))
        controller.navigate_result(results[1])
        self.assertEqual(adapter.selected, (17, 22))
        self.assertEqual(controller.current_match, (17, 22))

    def test_navigate_rejects_non_result(self):
        controller = SearchController(FakeAdapter("alpha"))
        with self.assertRaises(TypeError):
            controller.navigate_result((0, 5))

    def test_current_replace_and_replace_all_use_session_options(self):
        adapter = FakeAdapter("Alpha alpha")
        controller = SearchController(adapter)
        controller.configure("alpha", match_case=True, whole_word=True)
        controller.session = type(controller.session)(
            query=controller.query, current_match=(6, 11)
        )
        self.assertEqual(
            controller.prepare_current_replacement("omega"),
            (6, 11, "omega", (6, 11)),
        )
        self.assertEqual(controller.prepare_replace_all("omega"), ("Alpha omega", 1))

    def test_configure_new_query_clears_current_match(self):
        adapter = FakeAdapter("alpha beta")
        controller = SearchController(adapter)
        controller.configure("alpha")
        controller.session = type(controller.session)(
            query=controller.query, current_match=(0, 5)
        )
        controller.configure("beta")
        self.assertIsNone(controller.current_match)

    def test_schedule_highlight_coalesces_and_clears_stale_match(self):
        adapter = FakeAdapter("alpha alpha")
        controller = SearchController(adapter)
        controller.configure("alpha")
        controller.session = type(controller.session)(
            query=controller.query, current_match=(0, 5)
        )
        callbacks = []

        def timeout_add(delay, callback):
            callbacks.append((delay, callback))
            return 77

        self.assertTrue(controller.schedule_highlight(timeout_add))
        self.assertIsNone(controller.current_match)
        self.assertFalse(controller.schedule_highlight(timeout_add))
        self.assertEqual(callbacks[0][0], 300)
        self.assertFalse(callbacks[0][1]())
        self.assertEqual(adapter.highlights, [(0, 5), (6, 11)])
        self.assertTrue(controller.schedule_highlight(timeout_add))

    def test_schedule_without_query_is_noop(self):
        controller = SearchController(FakeAdapter("alpha"))
        self.assertFalse(controller.schedule_highlight(lambda *_: 1))

    def test_clear_current_match_and_commit(self):
        controller = SearchController(FakeAdapter("alpha"))
        controller.configure("alpha")
        controller.commit_current_replacement((0, 5))
        self.assertEqual(controller.current_match, (0, 5))
        controller.clear_current_match()
        self.assertIsNone(controller.current_match)
