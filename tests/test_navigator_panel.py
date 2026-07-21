import unittest

from calamus_document_structure import build_document_structure
from calamus_navigator_panel import (
    NavigatorPanelHost,
    NavigatorPanelPresenter,
    NavigatorPanelRuntime,
    calculate_navigator_panel_width,
)


class FakeAllocation:
    width = 900


class FakeWidget:
    def __init__(self):
        self.parent = None
        self.size = None
        self.hexpand = None
        self.vexpand = None
        self.shown = 0
        self.hidden = 0

    def get_parent(self):
        return self.parent

    def show_all(self):
        self.shown += 1

    def hide(self):
        self.hidden += 1

    def set_size_request(self, width, height):
        self.size = (width, height)

    def set_hexpand(self, value):
        self.hexpand = value

    def set_vexpand(self, value):
        self.vexpand = value


class FakePaned:
    def __init__(self):
        self.child = None
        self.position = None
        self.pack_calls = 0
        self.remove_calls = 0

    def get_allocation(self):
        return FakeAllocation()

    def pack1(self, widget, resize, shrink):
        self.child = widget
        widget.parent = self
        self.pack_calls += 1
        self.policy = (resize, shrink)

    def remove(self, widget):
        if widget is not self.child:
            raise ValueError("foreign widget")
        self.child = None
        widget.parent = None
        self.remove_calls += 1

    def set_position(self, value):
        self.position = value


class FakeController:
    def __init__(self):
        self.structure = build_document_structure("# One\ntext\n## Two\ntext\n")
        self.cursor = self.structure.headings[1].start_offset
        self.navigated = None

    def headings(self, query=""):
        return self.structure.filtered(query)

    def current_heading(self):
        return self.structure.current_heading(self.cursor)

    def navigate_heading(self, heading):
        self.navigated = heading
        return heading


class FakeView:
    def __init__(self):
        self.rendered = None
        self.selected = None

    def render(self, headings, current):
        self.rendered = (headings, current)

    def select_heading(self, heading):
        self.selected = heading


class FakeMenuItem:
    def __init__(self):
        self.active = False
        self.set_calls = []

    def get_active(self):
        return self.active

    def set_active(self, value):
        self.active = bool(value)
        self.set_calls.append(bool(value))


class FakeRuntimeView:
    def __init__(self):
        self.calls = []

    def refresh(self):
        self.calls.append("refresh")

    def schedule_cursor_sync(self):
        self.calls.append("sync")

    def focus_filter(self):
        self.calls.append("filter")

    def cancel_pending(self):
        self.calls.append("cancel")


class FakeRuntimeHost:
    def __init__(self):
        self.is_visible = False
        self.calls = []

    def show(self):
        self.is_visible = True
        self.calls.append("show")

    def hide(self):
        self.is_visible = False
        self.calls.append("hide")


class NavigatorPanelHostTests(unittest.TestCase):
    def test_width_is_compact_and_bounded(self):
        self.assertGreaterEqual(calculate_navigator_panel_width(520), 1)
        self.assertLessEqual(calculate_navigator_panel_width(2000), 220)

    def test_show_hide_owns_one_outer_paned_slot(self):
        paned = FakePaned()
        widget = FakeWidget()
        layouts = []
        host = NavigatorPanelHost(paned, widget, lambda: layouts.append(True))
        self.assertFalse(host.is_visible)
        host.show()
        self.assertTrue(host.is_visible)
        self.assertIs(paned.child, widget)
        self.assertEqual(paned.policy, (False, False))
        self.assertEqual(widget.size[0], paned.position)
        self.assertFalse(widget.hexpand)
        self.assertTrue(widget.vexpand)
        host.hide()
        self.assertFalse(host.is_visible)
        self.assertIsNone(widget.parent)
        self.assertEqual(len(layouts), 2)

    def test_toggle_preserves_widget_and_does_not_duplicate_pack(self):
        paned = FakePaned()
        widget = FakeWidget()
        host = NavigatorPanelHost(paned, widget, lambda: None)
        self.assertTrue(host.toggle())
        host.show()
        self.assertEqual(paned.pack_calls, 1)
        self.assertFalse(host.toggle())
        self.assertEqual(paned.remove_calls, 1)


class NavigatorPanelPresenterTests(unittest.TestCase):
    def test_refresh_filters_through_canonical_controller(self):
        controller = FakeController()
        view = FakeView()
        presenter = NavigatorPanelPresenter(controller, view)
        headings = presenter.refresh("two")
        self.assertEqual([heading.title for heading in headings], ["Two"])
        self.assertEqual(view.rendered[1].title, "Two")

    def test_sync_cursor_and_activate_delegate(self):
        controller = FakeController()
        view = FakeView()
        presenter = NavigatorPanelPresenter(controller, view)
        current = presenter.sync_cursor()
        self.assertEqual(view.selected, current)
        presenter.activate(current)
        self.assertEqual(controller.navigated, current)


class NavigatorPanelRuntimeTests(unittest.TestCase):
    def test_one_runtime_owns_visibility_menu_and_focus(self):
        host = FakeRuntimeHost()
        view = FakeRuntimeView()
        item = FakeMenuItem()
        focus = []
        runtime = NavigatorPanelRuntime(host, view, item, lambda: focus.append(True))
        self.assertTrue(runtime.toggle())
        self.assertTrue(host.is_visible)
        self.assertTrue(item.active)
        self.assertEqual(view.calls, ["refresh", "sync", "filter"])
        self.assertFalse(runtime.hide())
        self.assertFalse(host.is_visible)
        self.assertFalse(item.active)
        self.assertEqual(view.calls[-1], "cancel")
        self.assertEqual(focus, [True])

    def test_menu_toggled_uses_same_runtime_gateway(self):
        host = FakeRuntimeHost()
        view = FakeRuntimeView()
        item = FakeMenuItem()
        runtime = NavigatorPanelRuntime(host, view, item, lambda: None)
        item.active = True
        runtime.on_menu_toggled(item)
        self.assertTrue(runtime.is_visible)
        item.active = False
        runtime.on_menu_toggled(item)
        self.assertFalse(runtime.is_visible)


if __name__ == "__main__":
    unittest.main()
