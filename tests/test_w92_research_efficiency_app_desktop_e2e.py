"""Real GTK proofs for W92 Research activation and Scratchpad controls."""
from __future__ import annotations

import os
import unittest

RUN_REAL_GTK = os.environ.get("CALAMUS_W92_RUN_REAL_GTK") == "1"


@unittest.skipUnless(RUN_REAL_GTK, "set CALAMUS_W92_RUN_REAL_GTK=1")
class W92ResearchEfficiencyGtkE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        ok, _argv = Gtk.init_check([])
        if not ok:
            raise unittest.SkipTest("real GTK display is unavailable")

    @staticmethod
    def _drain_events():
        from gi.repository import Gtk
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)

    def test_real_research_selector_activates_each_semantic_change_once(self):
        from gi.repository import Gtk
        from calamus_research_panel_view import ResearchPanelViewAdapter

        activations = []
        view = ResearchPanelViewAdapter(lambda: None)
        view.register_client(
            "clip-collection", "Clip Collection", Gtk.Box(),
            lambda: activations.append("clip-collection"),
        )
        view.register_client(
            "scratchpad", "Scratchpad", Gtk.Box(),
            lambda: activations.append("scratchpad"),
        )
        view.widget.show_all()
        self._drain_events()
        activations.clear()

        view.show_client("scratchpad")
        self._drain_events()
        self.assertEqual(view.active_client, "scratchpad")
        self.assertEqual(activations, ["scratchpad"])

        activations.clear()
        view.selector.set_active_id("clip-collection")
        self._drain_events()
        self.assertEqual(view.active_client, "clip-collection")
        self.assertEqual(activations, ["clip-collection"])

        view.widget.destroy()
        self._drain_events()
        print("W92_REAL_RESEARCH_SINGLE_ACTIVATION=PASS")
        print("W92_REAL_RESEARCH_SELECTOR_STACK_SYNC=PASS")

    def test_real_scratchpad_refresh_button_and_list_keys_are_owned(self):
        from gi.repository import Gtk
        from calamus_scratchpad_panel import (
            _dispatch_scratchpad_list_key,
            build_scratchpad_panel_view,
        )

        calls = []
        callback = lambda name: (lambda *_: calls.append(name))
        view = build_scratchpad_panel_view(
            callback("new"),
            callback("edit"),
            callback("archive"),
            callback("delete"),
            callback("open"),
            callback("insert"),
            callback("copy"),
            callback("all"),
            callback("refresh"),
        )
        view.widget.show_all()
        self._drain_events()

        def descendants(widget):
            result = []
            if isinstance(widget, Gtk.Container):
                for child in widget.get_children():
                    result.append(child)
                    result.extend(descendants(child))
            return result

        refresh = next(
            item for item in descendants(view.widget)
            if isinstance(item, Gtk.Button) and item.get_label() == "Refresh"
        )
        refresh.clicked()
        self.assertEqual(calls, ["refresh"])

        for key, expected in (
            ("Insert", "new"),
            ("Delete", "delete"),
            ("F5", "refresh"),
        ):
            self.assertTrue(
                _dispatch_scratchpad_list_key(
                    key, callback("new"), callback("delete"), callback("refresh")
                )
            )
            self.assertEqual(calls[-1], expected)

        view.widget.destroy()
        self._drain_events()
        print("W92_REAL_SCRATCHPAD_REFRESH=PASS")
        print("W92_REAL_SCRATCHPAD_LIST_KEYS=PASS")


if __name__ == "__main__":
    unittest.main()
