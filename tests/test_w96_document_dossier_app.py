from __future__ import annotations

from datetime import datetime, timezone
import tempfile
from pathlib import Path
import unittest

from calamus_document_dossier_app import (
    build_document_dossier_inputs,
    navigate_document_overview_offset,
    navigate_document_overview_range,
)
from calamus_reference_set_store import ReferenceSetSnapshot
from calamus_reference_store import ReferenceLibrarySnapshot
from calamus_research_file import FileToken
from calamus_source_note_store import SourceNoteSnapshot, source_notes_path


class StaticStore:
    def __init__(self, value):
        self.value = value
        self.loads = 0

    def load(self):
        self.loads += 1
        return self.value




class FakeTextView:
    def __init__(self, events):
        self.events = events

    def grab_focus(self):
        self.events.append(("focus",))
        return True


class FakeNavigationApp:
    def __init__(self, text="0123456789"):
        self._text = text
        self._cursor = 0
        self.selection = None
        self.events = []
        self.text = FakeTextView(self.events)

    def buffer_text(self):
        return self._text

    def set_cursor_offset(self, offset):
        self._cursor = offset
        self.events.append(("cursor", offset))

    def get_cursor_offset(self):
        return self._cursor

    def select_range(self, start, end):
        self.selection = (start, end)
        self.events.append(("selection", start, end))

    def present(self):
        self.events.append(("present",))
        return True


class DocumentDossierAppBoundaryTests(unittest.TestCase):
    def test_untitled_document_uses_explicit_empty_sidecar_snapshot(self):
        refs = StaticStore(ReferenceLibrarySnapshot((), FileToken(False), ()))
        sets = StaticStore(ReferenceSetSnapshot((), FileToken(False), ()))
        value = build_document_dossier_inputs(
            document_text="# Draft",
            document_path=None,
            modified=True,
            bookmarks=(0,),
            reference_store=refs,
            reference_set_store=sets,
            now_provider=lambda: datetime(2026, 7, 31, 21, 0, tzinfo=timezone.utc),
        )
        self.assertEqual("", value.document_path)
        self.assertTrue(value.modified)
        self.assertEqual((0,), value.bookmarks)
        self.assertEqual((), value.source_note_snapshot.notes)
        self.assertFalse(value.source_note_snapshot.token.exists)
        self.assertEqual("2026-07-31T21:00:00+00:00", value.refreshed_at)
        self.assertEqual(1, refs.loads)
        self.assertEqual(1, sets.loads)

    def test_saved_document_loads_exact_sidecar_and_file_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = Path(tmp) / "article.md"
            document.write_text("# Article\n", encoding="utf-8")
            expected_sidecar = source_notes_path(str(document))
            seen = []
            snapshot = SourceNoteSnapshot((), FileToken(False), ())

            def factory(path):
                seen.append(path)
                return StaticStore(snapshot)

            value = build_document_dossier_inputs(
                document_text=document.read_text(encoding="utf-8"),
                document_path=str(document),
                modified=False,
                bookmarks=(),
                reference_store=StaticStore(ReferenceLibrarySnapshot((), FileToken(False), ())),
                reference_set_store=StaticStore(ReferenceSetSnapshot((), FileToken(False), ())),
                source_note_store_factory=factory,
            )
            self.assertEqual([expected_sidecar], seen)
            self.assertTrue(value.document_token.exists)
            self.assertEqual(str(document), value.document_path)


    def test_offset_navigation_owns_cursor_window_presentation_and_editor_focus(self):
        app = FakeNavigationApp()
        self.assertTrue(navigate_document_overview_offset(app.buffer_text, app.set_cursor_offset, app.get_cursor_offset, app.present, app.text.grab_focus, 7))
        self.assertEqual(7, app.get_cursor_offset())
        self.assertEqual([("cursor", 7), ("present",), ("focus",)], app.events)

    def test_range_navigation_owns_selection_window_presentation_and_editor_focus(self):
        app = FakeNavigationApp()
        self.assertTrue(navigate_document_overview_range(app.buffer_text, app.select_range, app.present, app.text.grab_focus, 2, 6))
        self.assertEqual((2, 6), app.selection)
        self.assertEqual([("selection", 2, 6), ("present",), ("focus",)], app.events)

    def test_navigation_fails_closed_without_presentable_editor_toplevel(self):
        app = FakeNavigationApp()
        app.present = None
        self.assertFalse(navigate_document_overview_offset(app.buffer_text, app.set_cursor_offset, app.get_cursor_offset, app.present, app.text.grab_focus, 4))
        self.assertEqual([("cursor", 4)], app.events)

    def test_invalid_authority_snapshot_fails_closed(self):
        with self.assertRaises(TypeError):
            build_document_dossier_inputs(
                document_text="Text",
                document_path=None,
                modified=False,
                bookmarks=(),
                reference_store=StaticStore(()),
                reference_set_store=StaticStore(ReferenceSetSnapshot((), FileToken(False), ())),
            )


if __name__ == "__main__":
    unittest.main()
