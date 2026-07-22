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
        self.focused = 0

    def show_client(self, client):
        self.active_client = client
        self.shown.append(client)

    def focus_active(self):
        self.focused += 1


class FakeMenuItem:
    def __init__(self):
        self.active = False

    def get_active(self):
        return self.active

    def set_active(self, active):
        self.active = active


class ResearchPanelRuntimeTests(unittest.TestCase):
    def test_show_uses_one_research_host_section_and_syncs_menu(self):
        host, view, item = FakeHost(), FakeView(), FakeMenuItem()
        runtime = ResearchPanelRuntime(host, view, item, lambda: None)
        self.assertTrue(runtime.show("references"))
        self.assertEqual(host.calls, [("show", "research")])
        self.assertEqual(view.active_client, "references")
        self.assertTrue(item.active)
        self.assertEqual(view.focused, 1)

    def test_hide_preserves_active_client_and_focuses_editor(self):
        host, view, item = FakeHost(), FakeView(), FakeMenuItem()
        focused = []
        runtime = ResearchPanelRuntime(host, view, item, lambda: focused.append(True))
        runtime.show("references")
        self.assertFalse(runtime.hide())
        self.assertEqual(view.active_client, "references")
        self.assertFalse(item.active)
        self.assertEqual(focused, [True])

    def test_toggle_and_menu_use_same_runtime(self):
        host, view, item = FakeHost(), FakeView(), FakeMenuItem()
        runtime = ResearchPanelRuntime(host, view, item, lambda: None)
        self.assertTrue(runtime.toggle())
        self.assertEqual(view.active_client, "clip-collection")
        item.active = False
        self.assertFalse(runtime.on_menu_toggled(item))
        self.assertFalse(host.is_visible)


if __name__ == "__main__":
    unittest.main()
