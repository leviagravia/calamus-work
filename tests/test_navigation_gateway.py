import unittest

from calamus_document_structure import DocumentHeading
from calamus_navigation_gateway import NavigationController


class FakeAdapter:
    def __init__(self, text="", cursor=0):
        self.current_text = text
        self.cursor = cursor
        self.navigated = []
        self.text_reads = 0
        self.lines = []

    def text(self):
        self.text_reads += 1
        return self.current_text

    def cursor_offset(self):
        return self.cursor

    def line_count(self):
        return max(1, self.current_text.count("\n") + 1)

    def navigate_offset(self, offset):
        self.navigated.append(offset)
        self.cursor = offset

    def navigate_line(self, line_index):
        self.lines.append(line_index)


class NavigationControllerTests(unittest.TestCase):
    def test_requires_adapter_protocol(self):
        with self.assertRaises(TypeError):
            NavigationController(object())

    def test_refresh_is_lazy_and_reuses_unchanged_structure(self):
        adapter = FakeAdapter("# One\n")
        controller = NavigationController(adapter)
        first = controller.refresh_structure()
        second = controller.refresh_structure()
        self.assertIs(first, second)
        self.assertEqual(first.headings[0].title, "One")

    def test_invalidate_rebuilds_after_buffer_change(self):
        adapter = FakeAdapter("# One\n")
        controller = NavigationController(adapter)
        controller.refresh_structure()
        adapter.current_text = "# Two\n"
        controller.invalidate()
        self.assertEqual(controller.headings()[0].title, "Two")

    def test_go_to_line_uses_canonical_clamp_and_zero_based_adapter(self):
        adapter = FakeAdapter("one\ntwo\nthree")
        controller = NavigationController(adapter)
        self.assertEqual(controller.go_to_line(2), 2)
        self.assertEqual(adapter.lines[-1], 1)
        self.assertEqual(controller.go_to_line(99), 3)
        self.assertEqual(adapter.lines[-1], 2)

    def test_heading_filter_uses_one_canonical_structure(self):
        adapter = FakeAdapter("# Alpha\n## Beta\n# Gamma\n")
        controller = NavigationController(adapter)
        self.assertEqual([h.title for h in controller.headings("a")], ["Alpha", "Beta", "Gamma"])
        self.assertEqual([h.title for h in controller.headings("bet")], ["Beta"])

    def test_current_next_previous_and_navigation(self):
        text = "# One\nbody\n## Two\nbody\n# Three\n"
        adapter = FakeAdapter(text, cursor=text.index("body") + 1)
        controller = NavigationController(adapter)
        self.assertEqual(controller.current_heading().title, "One")
        next_heading = controller.next_heading()
        self.assertEqual(next_heading.title, "Two")
        self.assertEqual(adapter.navigated[-1], text.index("## Two"))
        previous_heading = controller.previous_heading()
        self.assertEqual(previous_heading.title, "One")
        self.assertEqual(adapter.navigated[-1], 0)

    def test_navigation_stops_at_boundaries(self):
        adapter = FakeAdapter("# One\n", cursor=0)
        controller = NavigationController(adapter)
        self.assertIsNone(controller.previous_heading())
        adapter.cursor = len(adapter.current_text)
        self.assertIsNone(controller.next_heading())
        self.assertEqual(adapter.navigated, [])

    def test_navigate_rejects_foreign_heading(self):
        adapter = FakeAdapter("# One\n")
        controller = NavigationController(adapter)
        foreign = DocumentHeading(1, "Other", 1, 0, len(adapter.current_text))
        with self.assertRaises(ValueError):
            controller.navigate_heading(foreign)

    def test_force_argument_is_typed(self):
        controller = NavigationController(FakeAdapter())
        with self.assertRaises(TypeError):
            controller.refresh_structure(force=1)


if __name__ == "__main__":
    unittest.main()
