"""Real GTK/App proof for W97 Bibliography Manager Core."""
from __future__ import annotations

import faulthandler
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch

from calamus_reference_set_store import MarkdownReferenceSetStore, default_reference_sets_path
from calamus_reference_sets import ReferenceSet
from calamus_reference_store import MarkdownReferenceStore, default_references_path
from calamus_references import ReferenceRecord
from calamus_research_file import FileToken
from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
from calamus_source_notes import SourceNote
from tests.calamus_gtk_test_driver import (
    HAVE_GTK,
    Gtk,
    close_visible_dialogs,
    display_ready,
    named_widget,
    pump,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_REAL_GTK = os.environ.get("CALAMUS_W97_RUN_REAL_GTK") == "1"
faulthandler.enable(all_threads=True)


def _marker(name: str) -> None:
    print(f"W97_PRODUCT_STEP={name}", flush=True)


def _load_app_module():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = f"calamus_w97_bibliography_{uuid.uuid4().hex}"
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


def _environment(root: Path) -> dict[str, str]:
    return {
        "HOME": str(root),
        "XDG_DATA_HOME": str(root / "data"),
        "XDG_CONFIG_HOME": str(root / "config"),
        "XDG_CACHE_HOME": str(root / "cache"),
    }


def _text(view) -> str:
    buffer = view.get_buffer()
    start, end = buffer.get_bounds()
    return buffer.get_text(start, end, True)


def _visible_keys(listbox) -> list[str]:
    return [row.reference_key for row in listbox.get_children()]


def _until(predicate, *, timeout: float = 3.0, interval: float = 0.01) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pump()
        if predicate():
            return True
        time.sleep(interval)
    pump()
    return bool(predicate())


@unittest.skipUnless(
    RUN_REAL_GTK and HAVE_GTK and display_ready(),
    "set CALAMUS_W97_RUN_REAL_GTK=1 on a real GTK desktop",
)
class W97BibliographyAppDesktopE2E(unittest.TestCase):
    def test_real_app_list_detail_filters_context_file_actions_and_lifecycle(self):
        _marker("test-enter")
        with tempfile.TemporaryDirectory(prefix="calamus-w97-bibliography-") as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, _environment(root), clear=False):
                _set_isolated_config(root)
                document = root / "Article.md"
                document.write_text("# Article\nCited [@beta2021, p. 3].\n", encoding="utf-8")
                local_file = root / "alpha.pdf"
                local_file.write_bytes(
                    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                    b"2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\n"
                    b"trailer<</Root 1 0 R>>\n%%EOF\n"
                )
                _marker("fixture-files")

                reference_store = MarkdownReferenceStore(default_references_path())
                result = reference_store.save((
                    ReferenceRecord(
                        key="alpha2020", title="Alpha Book", type="book",
                        authors=("Rossi, Anna",), year="2020", tags=("theology",),
                        file_path=str(local_file), extra_fields=(("Custom", "Patristics"),),
                    ),
                    ReferenceRecord(
                        key="beta2021", title="Beta Article", type="journal-article",
                        authors=("Bianchi, Bruno",), year="2021", tags=("history",),
                        doi="10.1000/beta",
                    ),
                    ReferenceRecord(key="gamma2019", title="Gamma Thesis", type="thesis"),
                ), FileToken(False))
                self.assertTrue(result.saved)

                set_store = MarkdownReferenceSetStore(default_reference_sets_path())
                self.assertTrue(set_store.save(
                    (ReferenceSet("Core sources", members=("beta2021",)),),
                    FileToken(False),
                ).saved)
                note_store = MarkdownSourceNoteStore(source_notes_path(str(document)))
                self.assertTrue(note_store.save((
                    SourceNote(
                        id="note-1", kind="quote", text="Alpha quotation",
                        reference_key="alpha2020",
                    ),
                ), FileToken(False)).saved)

                _marker("authorities-saved")
                module = _load_app_module()
                _marker("app-module-loaded")
                win = module.App()
                _marker("app-constructed")
                try:
                    win.show_all()
                    _marker("app-shown")
                    pump()
                    self.assertTrue(win.open_path(str(document)))
                    pump()
                    _marker("document-opened")
                    self.assertTrue(win.show_references())
                    pump()
                    _marker("bibliography-activated")
                    self.assertEqual(win.research_panel_runtime.active_client, "references")

                    view = win.reference_panel_runtime._view
                    panel = named_widget(view.widget, "bibliography-panel", Gtk.Box)
                    self.assertIs(panel, view.widget)
                    search = named_widget(panel, "bibliography-search", Gtk.SearchEntry)
                    listbox = named_widget(panel, "bibliography-list", Gtk.ListBox)
                    detail = named_widget(panel, "bibliography-detail", Gtk.TextView)
                    type_filter = named_widget(panel, "bibliography-reference-type", Gtk.ComboBoxText)
                    use_filter = named_widget(panel, "bibliography-use", Gtk.ComboBoxText)
                    file_filter = named_widget(panel, "bibliography-file", Gtk.ComboBoxText)
                    _marker("widgets-resolved")
                    self.assertEqual(len(listbox.get_children()), 3)
                    self.assertEqual(view.selected_key(), "beta2021")
                    self.assertIn("Key: beta2021", _text(detail))
                    self.assertIn("Current Document: cited", _text(detail))
                    self.assertIn("Reference Sets: Core sources", _text(detail))

                    _marker("initial-state-verified")
                    deliveries_before = view.search_delivery_count
                    for partial in ("p", "pa", "pat", "patristics"):
                        search.set_text(partial)
                    _marker("search-requested")
                    self.assertTrue(_until(lambda: (
                        view.last_delivered_query == "patristics"
                        and _visible_keys(listbox) == ["alpha2020"]
                    )), "coalesced search was not published before timeout")
                    self.assertEqual(view.search_delivery_count, deliveries_before + 1)
                    _marker("search-delivered")
                    self.assertIn("Source Notes: used", _text(detail))

                    search.set_text("")
                    self.assertTrue(_until(lambda: view.last_delivered_query == ""))
                    type_filter.set_active_id("journal-article")
                    self.assertTrue(_until(lambda: _visible_keys(listbox) == ["beta2021"]))
                    _marker("type-filter-applied")

                    type_filter.set_active_id("all")
                    use_filter.set_active_id("source-notes")
                    self.assertTrue(_until(lambda: _visible_keys(listbox) == ["alpha2020"]))
                    _marker("use-filter-applied")

                    use_filter.set_active_id("all")
                    file_filter.set_active_id("present")
                    self.assertTrue(_until(lambda: _visible_keys(listbox) == ["alpha2020"]))
                    _marker("file-filter-applied")

                    # Hostile lifecycle loop: every transition replaces the visible
                    # Gtk.ListBoxRow generation while preserving one canonical
                    # selection/detail contract. A selected-row callback must never
                    # observe a removed row or a partially rebuilt list.
                    _marker("lifecycle-stress-begin")
                    for _cycle in range(12):
                        search.set_text("patristics")
                        self.assertTrue(_until(lambda: (
                            view.last_delivered_query == "patristics"
                            and _visible_keys(listbox) == ["alpha2020"]
                        )))
                        self.assertEqual(win.reference_panel_runtime.selected_key, "alpha2020")
                        self.assertIn("Key: alpha2020", _text(detail))

                        search.set_text("")
                        self.assertTrue(_until(lambda: view.last_delivered_query == ""))
                        file_filter.set_active_id("all")
                        type_filter.set_active_id("journal-article")
                        self.assertTrue(_until(lambda: _visible_keys(listbox) == ["beta2021"]))
                        self.assertEqual(win.reference_panel_runtime.selected_key, "beta2021")
                        self.assertIn("Key: beta2021", _text(detail))

                        type_filter.set_active_id("all")
                        use_filter.set_active_id("source-notes")
                        self.assertTrue(_until(lambda: _visible_keys(listbox) == ["alpha2020"]))
                        self.assertEqual(win.reference_panel_runtime.selected_key, "alpha2020")
                        self.assertIn("Key: alpha2020", _text(detail))

                        use_filter.set_active_id("all")
                        file_filter.set_active_id("present")
                        self.assertTrue(_until(lambda: _visible_keys(listbox) == ["alpha2020"]))
                        self.assertEqual(win.reference_panel_runtime.selected_key, "alpha2020")
                        self.assertIn("Key: alpha2020", _text(detail))
                    _marker("lifecycle-stress-complete")

                    opened = []
                    revealed = []
                    win.reference_panel_runtime._open_external = lambda path: opened.append(path) or True
                    win.reference_panel_runtime._reveal_external = lambda path: revealed.append(path) or True
                    self.assertTrue(win.reference_panel_runtime.on_open_file())
                    self.assertTrue(win.reference_panel_runtime.on_reveal_file())
                    self.assertEqual(opened, [str(local_file)])
                    self.assertEqual(revealed, [str(local_file)])
                    _marker("file-actions-verified")

                    before = Path(reference_store.path).read_bytes()
                    for _refresh in range(5):
                        self.assertTrue(win.reference_panel_runtime.on_refresh())
                        self.assertTrue(_until(lambda: _visible_keys(listbox) == ["alpha2020"]))
                        self.assertEqual(win.reference_panel_runtime.selected_key, "alpha2020")
                        self.assertIn("Key: alpha2020", _text(detail))
                    self.assertEqual(Path(reference_store.path).read_bytes(), before)
                    _marker("refresh-verified")

                    print("W97_REAL_BIBLIOGRAPHY_SINGLE_CLIENT=PASS")
                    print("W97_REAL_BIBLIOGRAPHY_LIST_DETAIL=PASS")
                    print("W97_REAL_BIBLIOGRAPHY_COMPLETE_SEARCH=PASS")
                    print("W97_REAL_BIBLIOGRAPHY_FILTERS=PASS")
                    print("W97_REAL_BIBLIOGRAPHY_CONTEXT=PASS")
                    print("W97_REAL_BIBLIOGRAPHY_FILE_ACTIONS=PASS")
                    print("W97_REAL_BIBLIOGRAPHY_REFRESH_READ_ONLY=PASS")
                finally:
                    _marker("cleanup-enter")
                    close_visible_dialogs()
                    win.destroy()
                    pump()
                    _marker("cleanup-complete")


if __name__ == "__main__":
    unittest.main(verbosity=2)
