import unittest

from calamus_research_panel import ResearchPanelRuntime


class FakeHost:
    def __init__(self):
        self.is_visible = False
        self.calls = []

    def show(self, section):
        self.calls.append(("show", section))
        self.is_visible = True

    def hide(self):
        self.calls.append(("hide", None))
        self.is_visible = False


class FakeView:
    def __init__(self):
        self.active_client = None
        self.shown = []

    def show_client(self, client):
        self.active_client = client
        self.shown.append(client)


class ResettingHost(FakeHost):
    """Simulate Gtk.show_all() restoring the first stack child."""

    def __init__(self, view):
        super().__init__()
        self._view = view

    def show(self, section):
        super().show(section)
        self._view.active_client = "clip-collection"


class FakeMenuItem:
    def __init__(self):
        self.active = False

    def get_active(self):
        return self.active

    def set_active(self, active):
        self.active = active


class ResearchPanelRuntimeTests(unittest.TestCase):
    def test_show_uses_one_research_host_section_and_syncs_menu(self):
        host, view = FakeHost(), FakeView()
        visibility = []
        runtime = ResearchPanelRuntime(
            host, view, lambda: None,
            on_visibility_changed=visibility.append,
        )
        self.assertTrue(runtime.show("references"))
        self.assertEqual(host.calls, [("show", "research")])
        self.assertEqual(view.active_client, "references")
        self.assertEqual(visibility, [True])

    def test_show_selects_requested_client_after_host_becomes_visible(self):
        view = FakeView()
        host = ResettingHost(view)
        runtime = ResearchPanelRuntime(host, view, lambda: None)
        self.assertTrue(runtime.show("scratchpad"))
        self.assertEqual(host.calls, [("show", "research")])
        self.assertEqual(view.shown, ["scratchpad"])
        self.assertEqual(view.active_client, "scratchpad")

    def test_hide_preserves_active_client_and_focuses_editor(self):
        host, view = FakeHost(), FakeView()
        focused = []
        visibility = []
        runtime = ResearchPanelRuntime(
            host, view, lambda: focused.append(True),
            on_visibility_changed=visibility.append,
        )
        runtime.show("references")
        self.assertFalse(runtime.hide())
        self.assertEqual(view.active_client, "references")
        self.assertEqual(visibility, [True, False])
        self.assertEqual(focused, [True])

    def test_toggle_and_menu_use_same_runtime(self):
        host, view = FakeHost(), FakeView()
        visibility = []
        runtime = ResearchPanelRuntime(
            host, view, lambda: None,
            on_visibility_changed=visibility.append,
        )
        self.assertTrue(runtime.toggle())
        self.assertEqual(view.active_client, "clip-collection")
        self.assertFalse(runtime.set_visible(False))
        self.assertFalse(host.is_visible)
        self.assertEqual(visibility, [True, False])
        self.assertFalse(hasattr(runtime, "on_menu_toggled"))


if __name__ == "__main__":
    unittest.main()
