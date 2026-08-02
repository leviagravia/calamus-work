"""Hostile GTK-lifecycle simulation for W97 Bibliography row replacement."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from calamus_reference_panel import ReferencePanelViewAdapter
from calamus_references import ReferenceRecord


class _Style:
    def add_class(self, _name):
        return None


class _Label:
    def __init__(self, label=""):
        self.label = label
        self._style = _Style()

    def set_markup(self, value):
        self.label = value

    def set_xalign(self, _value):
        return None

    def set_ellipsize(self, _value):
        return None

    def get_style_context(self):
        return self._style


class _Box:
    def __init__(self, **_kwargs):
        self.children = []

    def set_margin_top(self, _value): pass
    def set_margin_bottom(self, _value): pass
    def set_margin_start(self, _value): pass
    def set_margin_end(self, _value): pass
    def pack_start(self, child, *_args): self.children.append(child)


class _Row:
    def __init__(self):
        self.reference_key = None
        self.child = None

    def add(self, child):
        self.child = child


class _Gtk:
    class Orientation:
        VERTICAL = 1
    ListBoxRow = _Row
    Box = _Box
    Label = _Label


class _Pango:
    class EllipsizeMode:
        END = 1


class _Status:
    def __init__(self): self.text = ""
    def set_text(self, value): self.text = value


class _ListBox:
    def __init__(self):
        self.children = []
        self.selected = None
        self.callback = None
        self.handler_id = 41
        self.blocked = set()
        self.block_calls = []
        self.unblock_calls = []

    def connect(self, signal, callback):
        if signal != "row-selected":
            raise AssertionError(signal)
        self.callback = callback
        return self.handler_id

    def handler_block(self, handler):
        self.blocked.add(handler)
        self.block_calls.append(handler)

    def handler_unblock(self, handler):
        self.blocked.remove(handler)
        self.unblock_calls.append(handler)

    def _emit(self):
        if self.callback is not None and self.handler_id not in self.blocked:
            self.callback(self, self.selected)

    def get_children(self):
        return tuple(self.children)

    def remove(self, child):
        self.children.remove(child)
        if self.selected is child:
            self.selected = None
            # Model the synchronous GTK lifecycle emission caused by removing
            # the selected row. It must be blocked by the adapter transaction.
            self._emit()

    def add(self, row):
        self.children.append(row)

    def show_all(self):
        return None

    def select_row(self, row):
        self.selected = row
        self._emit()

    def get_selected_row(self):
        return self.selected

    def unselect_all(self):
        self.selected = None
        self._emit()


class W97BibliographyViewLifecycleTests(unittest.TestCase):
    def test_row_replacement_is_one_selection_silent_transaction(self):
        listbox = _ListBox()
        old = _Row()
        old.reference_key = "old"
        listbox.children.append(old)
        listbox.selected = old
        status = _Status()
        adapter = ReferencePanelViewAdapter(
            widget=object(), search=object(), listbox=listbox,
            status=status, detail=object(), filters={},
        )
        callbacks = []
        adapter.bind_selection(lambda: callbacks.append(adapter.selected_key()))
        records = (
            ReferenceRecord(key="alpha2020", title="Alpha"),
            ReferenceRecord(key="beta2021", title="Beta"),
        )
        with patch("calamus_reference_panel._gtk_pango", return_value=(_Gtk, _Pango)), \
             patch("calamus_reference_panel._escape", side_effect=lambda value: value):
            adapter.render(records, "beta2021", "2 references")

        self.assertEqual(callbacks, [])
        self.assertEqual(adapter.selected_key(), "beta2021")
        self.assertEqual([row.reference_key for row in listbox.children], ["alpha2020", "beta2021"])
        self.assertEqual(listbox.block_calls, [41])
        self.assertEqual(listbox.unblock_calls, [41])
        self.assertEqual(status.text, "2 references")

        # A real user selection after the transaction must still emit once.
        listbox.select_row(listbox.children[0])
        self.assertEqual(callbacks, ["alpha2020"])


    def test_row_construction_failure_preserves_previous_stable_generation(self):
        class FailingRow:
            calls = 0

            def __new__(cls):
                cls.calls += 1
                if cls.calls == 2:
                    raise RuntimeError("synthetic row construction failure")
                return _Row()

        class FailingGtk(_Gtk):
            ListBoxRow = FailingRow

        listbox = _ListBox()
        old = _Row()
        old.reference_key = "old"
        listbox.children.append(old)
        listbox.selected = old
        adapter = ReferencePanelViewAdapter(
            widget=object(), search=object(), listbox=listbox,
            status=_Status(), detail=object(), filters={},
        )
        callbacks = []
        adapter.bind_selection(lambda: callbacks.append(adapter.selected_key()))
        records = (
            ReferenceRecord(key="alpha2020", title="Alpha"),
            ReferenceRecord(key="beta2021", title="Beta"),
        )
        with patch("calamus_reference_panel._gtk_pango", return_value=(FailingGtk, _Pango)),              patch("calamus_reference_panel._escape", side_effect=lambda value: value):
            with self.assertRaisesRegex(RuntimeError, "synthetic row construction failure"):
                adapter.render(records, "beta2021", "2 references")

        self.assertEqual([row.reference_key for row in listbox.children], ["old"])
        self.assertIs(listbox.selected, old)
        self.assertEqual(callbacks, [])
        self.assertEqual(listbox.block_calls, [])
        self.assertEqual(listbox.unblock_calls, [])

    def test_selection_binding_is_single_owner(self):
        adapter = ReferencePanelViewAdapter(
            widget=object(), search=object(), listbox=_ListBox(),
            status=_Status(), detail=object(), filters={},
        )
        adapter.bind_selection(lambda: None)
        with self.assertRaises(RuntimeError):
            adapter.bind_selection(lambda: None)


if __name__ == "__main__":
    unittest.main()
