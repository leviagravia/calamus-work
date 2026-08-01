from __future__ import annotations

import unittest

from calamus_document_dossier import DocumentDossierInputs
from calamus_document_dossier_controller import DocumentDossierController
from calamus_document_overview_runtime import DocumentOverviewRuntime


class FakeWindow:
    def __init__(self):
        self.destroy_callback = None
        self.destroyed = False

    def connect(self, signal, callback):
        if signal == "destroy":
            self.destroy_callback = callback
        return 1

    def destroy(self):
        if self.destroyed:
            return
        self.destroyed = True
        if self.destroy_callback:
            self.destroy_callback(self)


class FakeView:
    def __init__(self):
        self.window = FakeWindow()
        self.callbacks = {}
        self.present_count = 0
        self.hide_count = 0
        self.headers = []
        self.categories = []
        self.items = []
        self.details = []
        self.stale = False

    def bind(self, **callbacks):
        self.callbacks = callbacks

    def render_header(self, **values):
        self.headers.append(values)

    def render_categories(self, selected, counts):
        self.categories.append((selected, counts))

    def render_items(self, heading, rows, selected):
        self.items.append((heading, rows, selected))

    def render_detail(self, **values):
        self.details.append(values)

    def set_stale(self, stale):
        self.stale = stale

    def present(self):
        self.present_count += 1

    def hide(self):
        self.hide_count += 1

    def destroy(self):
        self.window.destroy()


class DocumentOverviewRuntimeTests(unittest.TestCase):
    def make_runtime(self, text="# One {#one}\nText [@missing].\n"):
        state = {"inputs": DocumentDossierInputs(text, bookmarks=(0,))}
        controller = DocumentDossierController(lambda: state["inputs"])
        views = []
        calls = []

        def factory(_parent):
            view = FakeView()
            views.append(view)
            return view

        runtime = DocumentOverviewRuntime(
            object(),
            controller,
            navigate_offset=lambda offset: calls.append(("offset", offset)) or True,
            select_range=lambda start, end: calls.append(("range", start, end)) or True,
            show_reference=lambda key: calls.append(("reference", key)) or True,
            show_source_note=lambda note_id: calls.append(("note", note_id)) or True,
            show_reference_set=lambda name: calls.append(("set", name)) or True,
            run_research_check=lambda: calls.append(("check",)) or True,
            focus_document=lambda: calls.append(("focus",)) or True,
            show_error=lambda message: calls.append(("error", message)),
            show_notice=lambda message: calls.append(("notice", message)),
            view_factory=factory,
        )
        return runtime, controller, state, views, calls

    def test_open_is_single_instance_and_refreshes_on_each_request(self):
        runtime, controller, _state, views, _calls = self.make_runtime()
        self.assertTrue(runtime.open())
        first_window = runtime.window
        self.assertEqual(1, len(views))
        self.assertEqual(1, controller.refresh_count)
        self.assertTrue(runtime.open())
        self.assertIs(first_window, runtime.window)
        self.assertEqual(1, len(views))
        self.assertEqual(2, controller.refresh_count)
        self.assertEqual(2, views[0].present_count)

    def test_five_categories_and_structure_navigation_are_semantic(self):
        runtime, _controller, _state, views, calls = self.make_runtime()
        runtime.open()
        view = views[0]
        self.assertEqual("overview", view.categories[-1][0])
        self.assertEqual(
            {"overview", "structure", "research", "integrity", "statistics"},
            set(view.categories[-1][1]),
        )
        runtime.select_category("structure")
        heading, rows, _selected = view.items[-1]
        self.assertEqual("Structure", heading)
        section = next(row for row in rows if row.kind == "section")
        runtime.select_item(section.id)
        self.assertTrue(runtime.activate_primary())
        self.assertEqual(("offset", section.payload.start_offset), calls[-1])

    def test_citation_navigation_selects_exact_range(self):
        runtime, _controller, _state, views, calls = self.make_runtime()
        runtime.open()
        runtime.select_category("research")
        citation = next(row for row in views[0].items[-1][1] if row.kind == "citation")
        runtime.select_item(citation.id)
        self.assertTrue(runtime.activate_primary())
        self.assertEqual(("range", citation.payload.start_offset, citation.payload.end_offset), calls[-1])

    def test_document_navigation_hides_tool_window_but_preserves_single_instance(self):
        runtime, _controller, _state, views, calls = self.make_runtime()
        runtime.open()
        view = views[0]
        first_window = runtime.window
        runtime.select_category("structure")
        section = next(row for row in view.items[-1][1] if row.kind == "section")
        runtime.select_item(section.id)
        self.assertTrue(runtime.activate_primary())
        self.assertEqual(1, view.hide_count)
        self.assertTrue(runtime.is_open)
        self.assertIs(first_window, runtime.window)
        self.assertEqual(("offset", section.payload.start_offset), calls[-1])
        self.assertTrue(runtime.open())
        self.assertIs(first_window, runtime.window)
        self.assertEqual(2, view.present_count)

    def test_failed_document_navigation_restores_tool_window(self):
        runtime, _controller, _state, views, _calls = self.make_runtime()
        runtime.open()
        view = views[0]
        runtime.select_category("structure")
        section = next(row for row in view.items[-1][1] if row.kind == "section")
        runtime.select_item(section.id)
        runtime._navigate_offset = lambda _offset: False
        self.assertFalse(runtime.activate_primary())
        self.assertEqual(1, view.hide_count)
        self.assertEqual(2, view.present_count)
        self.assertTrue(runtime.is_open)

    def test_mark_stale_does_not_refresh_or_destroy_window(self):
        runtime, controller, _state, views, _calls = self.make_runtime()
        runtime.open()
        runtime.mark_stale()
        self.assertTrue(views[0].stale)
        self.assertEqual(1, controller.refresh_count)
        self.assertTrue(runtime.is_open)

    def test_close_releases_instance_and_returns_focus(self):
        runtime, _controller, _state, views, calls = self.make_runtime()
        runtime.open()
        self.assertTrue(runtime.close())
        self.assertFalse(runtime.is_open)
        self.assertIsNone(runtime.snapshot)
        self.assertEqual("overview", runtime.selected_category)
        self.assertIn(("focus",), calls)
        runtime.open()
        self.assertEqual(2, len(views))

    def test_shutdown_does_not_refocus_destroying_parent(self):
        runtime, _controller, _state, _views, calls = self.make_runtime()
        runtime.open()
        runtime.shutdown()
        self.assertFalse(runtime.is_open)
        self.assertNotIn(("focus",), calls)


if __name__ == "__main__":
    unittest.main()
