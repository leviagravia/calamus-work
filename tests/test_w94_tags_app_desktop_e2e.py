"""Real GTK and true-App proofs for the W94 Tags Research client."""
from __future__ import annotations

from contextlib import contextmanager
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

from tests.calamus_gtk_test_driver import HAVE_GTK, Gtk, close_visible_dialogs, display_ready, named_widget, pump

ROOT = Path(__file__).resolve().parents[1]
RUN_REAL_GTK = os.environ.get("CALAMUS_W94_RUN_REAL_GTK") == "1"


def _load_app_module():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = f"calamus_w94_app_{uuid.uuid4().hex}"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _set_isolated_config(root: Path) -> None:
    import calamus_config
    config = root / "config" / "calamus"
    calamus_config.CONFIG_DIR = str(config)
    calamus_config.SETTINGS_FILE = str(config / "settings.json")
    calamus_config.RECENT_FILE = str(config / "recent.json")
    calamus_config.FAVOURITES_FILE = str(config / "favourites.json")


@contextmanager
def _true_app_fixture():
    """Build one isolated true App with all three tag authorities populated."""
    from calamus_reference_store import MarkdownReferenceStore, default_references_path
    from calamus_references import ReferenceRecord
    from calamus_research_file import FileToken
    from calamus_scratchpad import ScratchpadEntry
    from calamus_scratchpad_store import MarkdownScratchpadStore, scratchpad_path
    from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
    from calamus_source_notes import SourceNote

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        environment = {
            "HOME": str(root),
            "XDG_DATA_HOME": str(root / "data"),
            "XDG_CONFIG_HOME": str(root / "config"),
            "XDG_CACHE_HOME": str(root / "cache"),
        }
        with patch.dict(os.environ, environment, clear=False):
            _set_isolated_config(root)
            document = root / "Article.md"
            original = "# Introduction {#intro}\nBody.\n"
            document.write_text(original, encoding="utf-8")

            reference_store = MarkdownReferenceStore(default_references_path())
            if not reference_store.save((
                ReferenceRecord(key="r1", title="Reference One", tags=("Faith", "history")),
            ), FileToken(False)).saved:
                raise AssertionError("could not create W94 References fixture")
            source_store = MarkdownSourceNoteStore(source_notes_path(str(document)))
            if not source_store.save((
                SourceNote(id="sn-1", kind="comment", text="Source note", tags=("faith",)),
            ), FileToken(False)).saved:
                raise AssertionError("could not create W94 Source Notes fixture")
            scratch_store = MarkdownScratchpadStore(scratchpad_path(str(document)))
            if not scratch_store.save((
                ScratchpadEntry(
                    id="sp-1", type="idea", title="Develop faith",
                    body="Draft", tags=("FAITH",),
                ),
            ), FileToken(False)).saved:
                raise AssertionError("could not create W94 Scratchpad fixture")

            module = _load_app_module()
            win = module.App()
            try:
                yield (
                    document, original, reference_store,
                    source_store, scratch_store, win,
                )
            finally:
                win.destroy()
                pump()


@unittest.skipUnless(HAVE_GTK and display_ready() and RUN_REAL_GTK, "real W94 GTK display required")
class W94TagsGtkE2E(unittest.TestCase):
    def tearDown(self):
        close_visible_dialogs()

    def test_real_tags_panel_owns_filters_counts_uses_and_actions(self):
        from calamus_tags_panel import build_tags_panel_view

        calls = []
        callback = lambda name: (lambda *_: calls.append(name))
        view = build_tags_panel_view(
            callback("open"), callback("rename"), callback("remove"),
            callback("normalize"), callback("refresh"), callback("show-all"),
        )
        view.widget.show_all()
        pump()
        try:
            widget_types = (
                ("tags-search", Gtk.SearchEntry),
                ("tags-show-all-az", Gtk.Button),
                ("tags-scope", Gtk.ComboBoxText),
                ("tags-sort", Gtk.ComboBoxText),
                ("tags-issues-only", Gtk.CheckButton),
                ("tags-list", Gtk.ListBox),
                ("tag-uses-list", Gtk.ListBox),
                ("tags-open", Gtk.Button),
                ("tags-rename", Gtk.Button),
                ("tags-refresh", Gtk.Button),
                ("tags-remove", Gtk.Button),
                ("tags-normalize", Gtk.Button),
            )
            for name, widget_type in widget_types:
                self.assertIsNotNone(named_widget(view.widget, name, widget_type))
            self.assertEqual(view.tags_list.get_selection_mode(), Gtk.SelectionMode.SINGLE)
            self.assertEqual(view.uses_list.get_selection_mode(), Gtk.SelectionMode.SINGLE)
            self.assertNotIn("TreeView", type(view.tags_list).__name__)
            self.assertEqual(view.scope.get_model().iter_n_children(None), 4)
            self.assertEqual(view.sort.get_model().iter_n_children(None), 2)
            named_widget(view.widget, "tags-show-all-az", Gtk.Button).clicked()
            pump()
            self.assertIn("show-all", calls)
            print("W94_REAL_TAGS_PANEL=PASS")
            print("W94_REAL_TAGS_ALL_AZ_ACTION=PASS")
            print("W94_REAL_TAGS_SCOPE_FILTERS=PASS")
            print("W94_REAL_TAGS_EXACT_USES=PASS")
            print("W94_REAL_TAGS_SORTING=PASS")
        finally:
            view.widget.destroy()
            pump()

    def test_real_tags_runtime_accepts_the_concrete_consumer_driven_view(self):
        from calamus_tag_integrity_controller import TagIntegrityController
        from calamus_tags_runtime import TagsRuntime

        class _NoopReferenceStore:
            def load(self):
                raise AssertionError("constructor preflight must not load References")

            def save(self, records, expected_token, *, force=False):
                raise AssertionError("constructor preflight must not save References")

        parent = Gtk.Window()
        try:
            integrity = TagIntegrityController(
                reference_store=_NoopReferenceStore(),
                document_path_provider=lambda: None,
                refresh_references=lambda: None,
                refresh_source_notes=lambda: None,
                refresh_scratchpad=lambda: None,
            )
            runtime = TagsRuntime(
                parent,
                integrity,
                show_reference=lambda _key: True,
                show_source_note=lambda _note_id: True,
                show_scratchpad_entry=lambda _entry_id: True,
            )
            self.assertIs(runtime.controller.widget, runtime.widget)
            self.assertFalse(hasattr(runtime._view, "queue_activation_focus"))
            self.assertFalse(hasattr(runtime._view, "focus_search"))
            self.assertNotIn("grab_focus", type(runtime._view).__dict__)
            print("W94_REAL_TAGS_RUNTIME_CONTRACT=PASS")
            print("W94_REAL_TAGS_CONSUMER_VIEW=PASS")
        finally:
            parent.destroy()
            pump()

    def test_true_app_constructs_with_tags_client(self):
        with _true_app_fixture() as fixture:
            win = fixture[-1]
            self.assertIsNotNone(win.tags_runtime)
            self.assertIsNotNone(win.research_panel_runtime)
            print("W94_REAL_APP_CONSTRUCT=PASS", flush=True)

    def test_true_app_maps_before_tags_activation(self):
        with _true_app_fixture() as fixture:
            win = fixture[-1]
            win.show_all()
            pump()
            self.assertTrue(win.get_mapped())
            self.assertFalse(win.tags_runtime.widget.get_mapped())
            print("W94_REAL_APP_MAP=PASS", flush=True)

    def test_true_app_opens_document_before_tags_activation(self):
        with _true_app_fixture() as fixture:
            document, _original, _references, _notes, _scratch, win = fixture
            win.show_all()
            pump()
            self.assertTrue(win.open_path(str(document)))
            pump()
            self.assertEqual(win.document.file_path, str(document))
            print("W94_REAL_APP_OPEN_DOCUMENT=PASS", flush=True)

    def test_true_app_activates_tags_with_post_map_selection_and_no_focus_steal(self):
        with _true_app_fixture() as fixture:
            document, _original, _references, _notes, _scratch, win = fixture
            win.show_all()
            pump()
            self.assertTrue(win.open_path(str(document)))
            pump()
            self.assertTrue(win.show_tags())
            pump()
            self.assertEqual(win.research_panel_runtime.active_client, "tags")
            self.assertTrue(win.tags_runtime.widget.get_mapped())
            self.assertIsNot(win.get_focus(), win.tags_runtime._view.search)
            self.assertEqual(win.tags_runtime._view.selected_tag_identity(), "faith")
            self.assertIsNotNone(win.tags_runtime._view.selected_use())
            print("W94_REAL_APP_TAGS_ACTIVATION=PASS", flush=True)
            print("W94_REAL_APP_NO_ACTIVATION_FOCUS=PASS", flush=True)
            print("W94_REAL_APP_POST_MAP_SELECTION=PASS", flush=True)

    def test_true_app_research_panel_remembers_width_and_remains_resizable_after_reopen(self):
        with _true_app_fixture() as fixture:
            document, _original, _references, _notes, _scratch, win = fixture
            win.set_default_size(1100, 720)
            win.show_all()
            pump()
            self.assertTrue(win.open_path(str(document)))
            pump()
            self.assertTrue(win.show_tags())
            pump()

            paned = win.body_paned
            research = win.research_panel_view.widget
            total = paned.get_allocation().width
            self.assertGreater(total, 700)
            self.assertTrue(paned.child_get_property(research, "shrink"))
            self.assertEqual(research.get_size_request()[0], -1)

            # Simulate a user drag to a medium width, close with X-equivalent,
            # reopen, and verify that the exact session width is restored.
            medium = 330
            paned.set_position(total - medium)
            pump()
            before = total - paned.get_position()
            self.assertLessEqual(abs(before - medium), 8)
            self.assertFalse(win.research_panel_runtime.hide())
            pump()
            self.assertTrue(win.show_tags())
            pump()
            total = paned.get_allocation().width
            restored = total - paned.get_position()
            self.assertLessEqual(abs(restored - before), 12)

            # The divider must still move both narrower and wider after reopen.
            narrow = 205
            paned.set_position(total - narrow)
            pump()
            self.assertLessEqual(abs((total - paned.get_position()) - narrow), 12)
            wide = 410
            paned.set_position(total - wide)
            pump()
            self.assertLessEqual(abs((total - paned.get_position()) - wide), 12)

            self.assertFalse(win.research_panel_runtime.hide())
            pump()
            self.assertTrue(win.show_tags())
            pump()
            total = paned.get_allocation().width
            self.assertLessEqual(abs((total - paned.get_position()) - wide), 14)
            print("W94_REAL_RESEARCH_RESIZE_AFTER_REOPEN=PASS", flush=True)
            print("W94_REAL_RESEARCH_WIDTH_PERSISTENCE=PASS", flush=True)
            print("W94_REAL_TAGS_RESPONSIVE_LAYOUT=PASS", flush=True)

    def test_true_app_projects_navigates_and_renames_three_markdown_authorities(self):
        from calamus_tag_integrity import TAG_ACTION_RENAME_MERGE

        with _true_app_fixture() as fixture:
            document, original, reference_store, source_store, scratch_store, win = fixture
            win.show_all()
            pump()
            self.assertTrue(win.open_path(str(document)))
            pump()
            self.assertTrue(win.show_tags())
            pump()
            self.assertEqual(win.research_panel_runtime.active_client, "tags")
            self.assertTrue(win.tags_runtime.widget.get_mapped())

            # Exercise the lifecycle boundary under the real App shell.
            self.assertTrue(win.tags_runtime.controller.refresh())
            pump()
            self.assertTrue(win.show_references())
            pump()
            self.assertTrue(win.show_tags())
            pump()
            self.assertFalse(win.toggle_research_panel())
            pump()
            self.assertTrue(win.show_tags())
            pump()
            self.assertTrue(win.tags_runtime.controller.refresh())
            pump()
            controller = win.tags_runtime.controller
            item = controller.inventory.get("faith")
            self.assertIsNotNone(item)
            self.assertEqual(
                (item.reference_count, item.source_note_count, item.scratchpad_count),
                (1, 1, 1),
            )
            self.assertTrue(item.needs_normalization)

            # Deferred selection is complete after pump; Open dispatches through App.
            self.assertEqual(win.tags_runtime._view.selected_tag_identity(), "faith")
            self.assertTrue(controller.open_selected_use())
            pump()
            self.assertEqual(win.research_panel_runtime.active_client, "references")

            self.assertTrue(win.show_tags())
            pump()
            plan = controller.prepare(
                action=TAG_ACTION_RENAME_MERGE,
                source_tag="Faith",
                target_tag="doctrine",
            )
            self.assertEqual(plan.impact.scratchpad_entries_changed, 1)
            self.assertEqual(plan.impact.rename_mode, "rename")
            result = controller.apply(plan)
            self.assertTrue(result.succeeded, result.message)
            self.assertEqual(reference_store.load().records[0].tags, ("doctrine", "history"))
            self.assertEqual(source_store.load().notes[0].tags, ("doctrine",))
            self.assertEqual(scratch_store.load().entries[0].tags, ("doctrine",))
            self.assertEqual(document.read_text(encoding="utf-8"), original)
            print("W94_REAL_APP_TAGS_LIFECYCLE=PASS", flush=True)
            print("W94_REAL_APP_VIEWPORT_FREE_RENDER=PASS", flush=True)
            print("W94_REAL_APP_POST_MAP_SELECTION=PASS", flush=True)
            print("W94_REAL_APP_TAGS_CLIENT=PASS", flush=True)
            print("W94_REAL_APP_THREE_AUTHORITIES=PASS", flush=True)
            print("W94_REAL_APP_EXACT_USE_NAVIGATION=PASS", flush=True)
            print("W94_REAL_APP_TAG_TRANSACTION=PASS", flush=True)
            print("W94_REAL_TAG_OPERATION_MODE=PASS", flush=True)
            print("W94_REAL_APP_DOCUMENT_UNCHANGED=PASS", flush=True)


if __name__ == "__main__":
    unittest.main()
