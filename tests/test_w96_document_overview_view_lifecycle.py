"""Headless lifecycle contracts for the GTK Document Overview category selector."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from calamus_document_overview_view import DocumentOverviewViewAdapter


class _Dummy:
    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


class _FakeLabel:
    def __init__(self, label=""):
        self.text = label

    def set_text(self, text):
        self.text = text

    def set_xalign(self, _value): pass
    def set_margin_start(self, _value): pass
    def set_margin_end(self, _value): pass
    def set_margin_top(self, _value): pass
    def set_margin_bottom(self, _value): pass


class _FakeRow:
    def __init__(self):
        self.child = None

    def add(self, child):
        self.child = child


class _FakeListBox:
    def __init__(self):
        self.children = []
        self.selected = None
        self.remove_calls = 0
        self.show_all_calls = 0

    def add(self, row):
        self.children.append(row)

    def get_children(self):
        return list(self.children)

    def remove(self, row):
        self.remove_calls += 1
        self.children.remove(row)

    def show_all(self):
        self.show_all_calls += 1

    def select_row(self, row):
        self.selected = row


class _FakeGtk:
    ListBoxRow = _FakeRow
    Label = _FakeLabel


class DocumentOverviewCategoryLifecycleTests(unittest.TestCase):
    def make_view(self):
        categories = _FakeListBox()
        adapter = DocumentOverviewViewAdapter(
            _Dummy(), _Dummy(), _Dummy(), categories, _Dummy(), _Dummy(),
            _Dummy(), _Dummy(), _Dummy(), _Dummy(), _Dummy(), _Dummy(),
        )
        return adapter, categories

    def test_category_rows_are_created_once_and_keep_identity_across_render(self):
        adapter, categories = self.make_view()
        with patch("calamus_document_overview_view._gtk_pango", return_value=(_FakeGtk, object())):
            adapter.render_categories("overview", {"research": 2})
            first = dict(adapter._category_rows)
            adapter.render_categories("research", {"research": 9, "integrity": 1})

        self.assertEqual(5, len(categories.children))
        self.assertEqual(first, adapter._category_rows)
        self.assertIs(first["research"], categories.selected)
        self.assertEqual(0, categories.remove_calls)
        self.assertEqual(1, categories.show_all_calls)

    def test_category_refresh_updates_labels_without_replacing_selected_event_source(self):
        adapter, categories = self.make_view()
        with patch("calamus_document_overview_view._gtk_pango", return_value=(_FakeGtk, object())):
            adapter.render_categories("research", {"research": 3})
            event_source = categories.selected
            adapter.render_categories("research", {"research": 7})

        self.assertIs(event_source, categories.selected)
        self.assertIs(event_source, adapter._category_rows["research"])
        self.assertEqual("Research  (7)", adapter._category_labels["research"].text)
        self.assertEqual(0, categories.remove_calls)


if __name__ == "__main__":
    unittest.main()
