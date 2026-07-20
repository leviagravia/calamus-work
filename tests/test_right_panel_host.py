import unittest

from calamus_right_panel import RightPanelHost, calculate_right_panel_width


class Allocation:
    def __init__(self, width=900):
        self.width = width


class FakeWidget:
    def __init__(self):
        self.parent = None
        self.visible = False
        self.size = None
        self.hexpand = None
        self.vexpand = None
        self.hide_calls = 0

    def get_parent(self):
        return self.parent

    def show_all(self):
        self.visible = True

    def hide(self):
        self.visible = False
        self.hide_calls += 1

    def set_size_request(self, width, height):
        self.size = (width, height)

    def set_hexpand(self, value):
        self.hexpand = value

    def set_vexpand(self, value):
        self.vexpand = value


class FakePaned:
    def __init__(self, width=900):
        self.allocation = Allocation(width)
        self.child2 = None
        self.position = None
        self.pack_calls = []
        self.remove_calls = []

    def get_allocation(self):
        return self.allocation

    def pack2(self, widget, resize, shrink):
        self.pack_calls.append((widget, resize, shrink))
        self.child2 = widget
        widget.parent = self

    def remove(self, widget):
        if self.child2 is not widget:
            raise ValueError("not attached")
        self.remove_calls.append(widget)
        self.child2 = None
        widget.parent = None

    def set_position(self, position):
        self.position = position


class RightPanelHostTests(unittest.TestCase):
    def test_width_is_bounded_for_generic_right_panel(self):
        self.assertEqual(calculate_right_panel_width(2000), 190)
        self.assertGreaterEqual(calculate_right_panel_width(400), 184)
        self.assertLessEqual(calculate_right_panel_width(900), 190)

    def test_register_is_lazy_and_does_not_attach(self):
        paned = FakePaned()
        widget = FakeWidget()
        host = RightPanelHost(paned, lambda: None)
        host.register("clips", widget)
        self.assertTrue(host.has_section("clips"))
        self.assertIsNone(paned.child2)
        self.assertFalse(host.is_visible)

    def test_show_configures_one_slot_and_notifies_reflow(self):
        paned = FakePaned(1000)
        widget = FakeWidget()
        events = []
        host = RightPanelHost(paned, lambda: events.append("layout"))
        host.register("clips", widget)
        host.show("clips")
        self.assertIs(paned.child2, widget)
        self.assertEqual(paned.pack_calls, [(widget, False, False)])
        self.assertEqual(widget.size, (190, -1))
        self.assertFalse(widget.hexpand)
        self.assertTrue(widget.vexpand)
        self.assertEqual(paned.position, 810)
        self.assertEqual(host.active_section, "clips")
        self.assertEqual(events, ["layout"])

    def test_toggle_hides_by_detaching_the_single_slot(self):
        paned = FakePaned()
        widget = FakeWidget()
        events = []
        host = RightPanelHost(paned, lambda: events.append("layout"))
        host.register("clips", widget)
        self.assertTrue(host.toggle("clips"))
        self.assertFalse(host.toggle("clips"))
        self.assertIsNone(paned.child2)
        self.assertIsNone(host.active_section)
        self.assertEqual(events, ["layout", "layout"])

    def test_switch_replaces_section_without_second_paned(self):
        paned = FakePaned()
        clips = FakeWidget()
        concepts = FakeWidget()
        host = RightPanelHost(paned, lambda: None)
        host.register("clips", clips)
        host.register("concepts", concepts)
        host.show("clips")
        host.show("concepts")
        self.assertIs(paned.child2, concepts)
        self.assertEqual(paned.remove_calls, [clips])
        self.assertEqual(host.active_section, "concepts")

    def test_invalid_or_duplicate_sections_are_rejected(self):
        host = RightPanelHost(FakePaned(), lambda: None)
        with self.assertRaises(ValueError):
            host.register("", FakeWidget())
        host.register("clips", FakeWidget())
        with self.assertRaises(ValueError):
            host.register("clips", FakeWidget())
        with self.assertRaises(KeyError):
            host.show("missing")


if __name__ == "__main__":
    unittest.main()
