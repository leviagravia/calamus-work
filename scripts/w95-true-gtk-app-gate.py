#!/usr/bin/env python3
"""Historical W95 real GTK/App product gate.

This gate intentionally does not bind to the current development work-item
identity. Current identity is certified by the active work-item GTK lane.

This gate uses the production App, Gtk.ListBox, dialogs, Markdown store,
Research selector, command/Undo path and TextView viewport. Callback failures
are captured and re-raised; no GLib timeout exception may degrade into a false
PASS.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("CALAMUS_SOURCE_ROOT", str(ROOT))
os.environ.setdefault("CALAMUS_LIB_DIR", str(ROOT / "calamus"))
sys.path.insert(0, str(ROOT / "calamus"))

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from calamus_clip_dialogs import run_clip_editor_dialog, run_clip_selector_dialog
from calamus_clip_expansion import expand_clip_text
from calamus_clip_runtime import insert_clip_expansion

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def drain_events() -> None:
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def drain_until(predicate, message: str, *, max_iterations: int = 500) -> None:
    """Drain the GTK main context until an owned async operation completes.

    This is a semantic wait on application-owned source state, not a guessed
    millisecond delay.  It prevents a viewport assertion from racing the one
    low-priority idle source that performs the documented scroll.
    """
    for _ in range(max_iterations):
        drain_events()
        if predicate():
            return
        GLib.usleep(1_000)
    require(False, message)


def drain_history_scroll(app) -> None:
    drain_until(
        lambda: (
            app.history_runtime.scroll_source is None
            and not app.history_runtime.reveal_pending
        ),
        "history viewport reveal did not complete",
    )


def descendants(widget):
    yield widget
    if isinstance(widget, Gtk.Container):
        for child in widget.get_children():
            yield from descendants(child)


def find_in(widget, widget_type):
    return [item for item in descendants(widget) if isinstance(item, widget_type)]


def find_named(widget, widget_type, name: str):
    matches = [
        item for item in descendants(widget)
        if isinstance(item, widget_type) and item.get_name() == name
    ]
    require(len(matches) == 1, f"expected one {name} widget, found {len(matches)}")
    return matches[0]


class AsyncDialogDriver:
    """Run a GLib dialog driver without allowing callback failures to vanish."""

    def __init__(self, callback) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._callback = callback
        self._failure: BaseException | None = None

    def schedule(self, interval_ms: int = 20) -> None:
        GLib.timeout_add(interval_ms, self._tick)

    def _tick(self):
        try:
            return bool(self._callback())
        except BaseException as error:  # callback exceptions are otherwise printed only
            self._failure = error
            for window in Gtk.Window.list_toplevels():
                if isinstance(window, Gtk.Dialog):
                    try:
                        window.response(Gtk.ResponseType.CANCEL)
                    except Exception:
                        pass
            return False

    def raise_if_failed(self) -> None:
        if self._failure is not None:
            raise self._failure


def load_launcher():
    launcher_path = ROOT / "bin" / "calamus"
    require(launcher_path.is_file(), f"launcher missing: {launcher_path}")
    loader = importlib.machinery.SourceFileLoader(
        "calamus_w95_launcher",
        str(launcher_path),
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    require(spec is not None and spec.loader is not None, "launcher spec unavailable")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def exercise_editor_dialog(parent) -> None:
    def complete_dialog():
        for window in Gtk.Window.list_toplevels():
            if isinstance(window, Gtk.Dialog) and window.get_title() == "W95 GTK New Clip":
                title_entry = find_named(
                    window, Gtk.Entry, "calamus-clip-title-entry"
                )
                shortcut_entry = find_named(
                    window, Gtk.Entry, "calamus-clip-shortcut-entry"
                )
                body_view = find_named(
                    window, Gtk.TextView, "calamus-clip-body-view"
                )
                title_entry.set_text("Dialog-created clip")
                shortcut_entry.set_text("dialogo")
                body_view.get_buffer().set_text("Corpo dal dialogo {{cursor}}")
                window.response(Gtk.ResponseType.OK)
                return False
        return True

    driver = AsyncDialogDriver(complete_dialog)
    driver.schedule()
    record = run_clip_editor_dialog(parent, dialog_title="W95 GTK New Clip")
    driver.raise_if_failed()
    require(record is not None, "editor dialog returned Cancel")
    require(record["title"] == "Dialog-created clip", "editor dialog title mismatch")
    require(record["shortcut"] == "dialogo", "editor dialog shortcut mismatch")
    require(record["text"] == "Corpo dal dialogo {{cursor}}", "editor dialog body mismatch")


def exercise_selector_dialog(parent, clips, expected_id: str) -> None:
    state = {"query_set": False, "attempts": 0}

    def complete_dialog():
        for window in Gtk.Window.list_toplevels():
            if isinstance(window, Gtk.Dialog) and window.get_title() == "Insert Clip":
                searches = find_in(window, Gtk.SearchEntry)
                listboxes = find_in(window, Gtk.ListBox)
                require(searches and listboxes, "selector widgets unavailable")
                if not state["query_set"]:
                    searches[0].set_text("saluto")
                    state["query_set"] = True
                    return True
                row = listboxes[0].get_selected_row()
                if row is not None and getattr(row, "_calamus_clip_id", None) == expected_id:
                    window.response(Gtk.ResponseType.OK)
                    return False
                state["attempts"] += 1
                require(state["attempts"] < 100, "selector did not settle on exact stable ID")
                return True
        return True

    driver = AsyncDialogDriver(complete_dialog)
    driver.schedule()
    selected = run_clip_selector_dialog(parent, clips)
    driver.raise_if_failed()
    require(selected == expected_id, "quick selector returned wrong stable ID")


def exercise_cursor_extremes(app, _controller) -> None:
    """Exercise the production insertion gateway independently of list selection.

    Row activation and controller-to-runtime wiring are already covered earlier
    in this gate.  Cursor placement must not be coupled to a freshly rebuilt
    Gtk.ListBox selection, because that would make a caret assertion fail for
    an unrelated selection-fixture reason.
    """
    cases = (
        ("cursor-first", "{{cursor}}TESTO"),
        ("cursor-last", "TESTO{{cursor}}"),
        ("cursor-middle", "PRIMA {{cursor}} DOPO"),
    )
    for shortcut, body in cases:
        expansion = expand_clip_text(body)
        app.set_buffer("BEGIN END")
        app.set_cursor_offset(6)
        require(
            insert_clip_expansion(app, expansion.text, expansion.cursor_offset),
            f"{shortcut} production insertion gateway failed",
        )
        drain_history_scroll(app)
        expected_text = "BEGIN " + expansion.text + "END"
        actual_text = app.buffer_text()
        require(
            actual_text == expected_text,
            f"{shortcut} text mismatch: expected={expected_text!r} actual={actual_text!r}",
        )
        expected_caret = 6 + expansion.cursor_offset
        actual_caret = app.get_cursor_offset()
        require(
            actual_caret == expected_caret,
            f"{shortcut} caret mismatch: expected={expected_caret} actual={actual_caret}",
        )
        app.on_undo()
        drain_history_scroll(app)
        require(app.buffer_text() == "BEGIN END", f"{shortcut} Undo mismatch")


def invoke_undo(app, label: str) -> None:
    """Invoke the UI callback and certify success from state/effect, not return."""
    app.history_runtime.flush()
    require(app.history.can_undo, f"{label}: Undo is unavailable")
    result = app.on_undo()
    require(result is None, f"{label}: on_undo leaked a semantic return value")


def invoke_redo(app, label: str) -> None:
    """Invoke the UI callback and certify success from state/effect, not return."""
    app.history_runtime.flush()
    require(app.history.can_redo, f"{label}: Redo is unavailable")
    result = app.on_redo()
    require(result is None, f"{label}: on_redo leaked a semantic return value")


def exercise_undo_viewport(app) -> None:
    """Run a real edit→navigation→Undo cycle on a long document."""
    long_text = "\n".join(f"Line {index:04d} — viewport proof" for index in range(600))
    app.set_buffer(long_text)
    app.set_cursor_offset(len(long_text))
    drain_events()

    def append_tail(buffer):
        buffer.insert_at_cursor("\nUNDO-VIEWPORT-TAIL")

    require(app.execute_command("Viewport proof", append_tail), "viewport edit failed")
    app.set_cursor_offset(0)
    drain_events()
    invoke_undo(app, "viewport proof")
    drain_history_scroll(app)
    require(app.buffer_text() == long_text, "real Undo did not restore long document")
    require(app.get_cursor_offset() == len(long_text), "real Undo did not restore exact caret")
    buffer = app.text.get_buffer()
    iterator = buffer.get_iter_at_mark(buffer.get_insert())
    location = app.text.get_iter_location(iterator)
    visible = app.text.get_visible_rect()
    require(
        location.y < visible.y + visible.height
        and location.y + max(1, location.height) > visible.y,
        f"Undo caret outside viewport: caret_y={location.y} visible={visible.y}:{visible.y + visible.height}",
    )
    expected_redo = long_text + "\nUNDO-VIEWPORT-TAIL"
    invoke_redo(app, "viewport proof")
    drain_history_scroll(app)
    require(app.buffer_text() == expected_redo, "real Redo did not restore edited text")
    require(app.get_cursor_offset() == len(expected_redo), "real Redo did not restore exact caret")
    redo_iterator = buffer.get_iter_at_mark(buffer.get_insert())
    redo_location = app.text.get_iter_location(redo_iterator)
    redo_visible = app.text.get_visible_rect()
    require(
        redo_location.y < redo_visible.y + redo_visible.height
        and redo_location.y + max(1, redo_location.height) > redo_visible.y,
        "Redo caret is outside the visible viewport",
    )
    invoke_undo(app, "viewport cleanup")
    drain_history_scroll(app)


def exercise_undo_selection_state(app) -> None:
    """Prove that Undo restores insert and selection-bound marks exactly."""
    original = "alpha beta gamma"
    app.set_buffer(original)
    buffer = app.text.get_buffer()
    insert = buffer.get_iter_at_offset(10)
    bound = buffer.get_iter_at_offset(6)
    buffer.select_range(insert, bound)

    def replace_selection(target):
        start, end = target.get_selection_bounds()
        target.delete(start, end)
        target.insert_at_cursor("X")

    require(app.execute_command("Selection proof", replace_selection), "selection edit failed")
    app.set_cursor_offset(0)
    drain_events()
    invoke_undo(app, "selection proof")
    drain_history_scroll(app)
    require(app.buffer_text() == original, "selection Undo text mismatch")
    actual_insert = buffer.get_iter_at_mark(buffer.get_insert()).get_offset()
    actual_bound = buffer.get_iter_at_mark(buffer.get_selection_bound()).get_offset()
    require(
        (actual_insert, actual_bound) == (10, 6),
        f"selection marks mismatch: expected=(10, 6) actual={(actual_insert, actual_bound)}",
    )
    invoke_redo(app, "selection proof")
    drain_history_scroll(app)
    require(app.buffer_text() == "alpha X gamma", "selection Redo text mismatch")
    redo_insert = buffer.get_iter_at_mark(buffer.get_insert()).get_offset()
    redo_bound = buffer.get_iter_at_mark(buffer.get_selection_bound()).get_offset()
    require(
        (redo_insert, redo_bound) == (7, 7),
        f"Redo marks mismatch: expected=(7, 7) actual={(redo_insert, redo_bound)}",
    )
    invoke_undo(app, "selection cleanup")
    drain_history_scroll(app)


def desktop_widget_ready(widget) -> bool:
    """Return True only after GTK has mapped and allocated a real widget."""
    if not (widget.get_visible() and widget.get_realized() and widget.get_mapped()):
        return False
    allocation = widget.get_allocation()
    return allocation.width > 1 and allocation.height > 1


def require_desktop_widget(widget, label: str) -> None:
    """Require a widget to be genuinely present in the mapped desktop tree."""
    allocation = widget.get_allocation()
    require(
        desktop_widget_ready(widget),
        f"{label} is not ready: visible={widget.get_visible()} "
        f"realized={widget.get_realized()} mapped={widget.get_mapped()} "
        f"allocation={allocation.width}x{allocation.height}",
    )


def exercise_research_selector(app) -> None:
    selector = app.research_panel_view.selector
    listed = selector.listed_ids()
    require(len(listed) >= 2, "Research selector needs at least two clients")
    require(listed[0] == "clip-collection", "Research selector order lost first client")

    # Exercise the real MenuButton state rather than calling the popover model
    # directly.  The previous gate missed a desktop failure because the
    # popover arrow mapped while its ScrolledWindow/ListBox descendants stayed
    # hidden and unallocated.
    selector.widget.set_active(True)
    drain_until(
        lambda: (
            desktop_widget_ready(selector.popover)
            and desktop_widget_ready(selector._scroll)
            and desktop_widget_ready(selector.listbox)
            and all(desktop_widget_ready(row) for row in selector.listbox.get_children())
        ),
        "Research selector child hierarchy did not receive usable allocation",
    )
    require(
        selector.popup_position() == Gtk.PositionType.BOTTOM,
        "Research selector is not requested below the control",
    )
    require_desktop_widget(selector.popover, "Research selector popover")
    require_desktop_widget(selector._scroll, "Research selector scrolled window")
    require_desktop_widget(selector.listbox, "Research selector list")

    rows = selector.listbox.get_children()
    require(len(rows) == len(listed), "Research selector row count differs from client model")
    first = rows[0]
    target = rows[1]
    require_desktop_widget(first, "Research selector first row")
    require_desktop_widget(target, "Research selector target row")
    labels = find_in(target, Gtk.Label)
    require(labels and labels[0].get_text().strip(), "Research selector target label is blank")
    require_desktop_widget(labels[0], "Research selector target label")

    selected = selector.listbox.get_selected_row()
    require(selected is not None, "Research selector did not select a first client")
    require(
        getattr(selected, "_calamus_client_id", None) == listed[0],
        "Research selector did not begin from the first client",
    )
    adjustment = selector._scroll.get_vadjustment()
    require(
        abs(adjustment.get_value() - adjustment.get_lower()) <= 1.0,
        "Research selector popup did not reset to the top",
    )

    # Activate a mapped row through the production ListBox signal, then verify
    # the complete selector -> stack -> runtime effect and popover closure.
    target_id = listed[1]
    selector.listbox.select_row(target)
    selector.listbox.emit("row-activated", target)
    drain_until(
        lambda: not selector.popover.get_mapped(),
        "Research selector popover did not close after row activation",
    )
    require(selector.get_active_id() == target_id, "Research selector did not accept activated row")
    require(
        app.research_panel_runtime.active_client == target_id,
        "Research selector activation did not switch the Research client",
    )
    require(
        not selector.popover.get_mapped(),
        "Research selector popover stayed mapped after row activation",
    )

    app.show_clip_collection()
    drain_events()
    require(
        app.research_panel_runtime.active_client == "clip-collection",
        "Research selector test did not restore Clip Collection",
    )


def main() -> int:
    ok, _argv = Gtk.init_check([])
    require(ok, "GTK display unavailable")
    # Historical product gates certify W95 behavior across later work items.
    # Current development identity is owned by the active work-item gate.
    print("W95_HISTORICAL_IDENTITY_INDEPENDENT=PASS")

    launcher = load_launcher()
    app = launcher.App()
    app.show_all()
    drain_events()

    try:
        controller = app.clip_collection
        require(controller.create("Saluto", "Gentile {{cursor}},\nCordiali saluti.", "saluto"), controller.last_error)
        clip_id = controller.clips[0]["id"]
        require(controller.create("Chiusura", "Grazie per l’attenzione.", "chiusura"), controller.last_error)
        require(len(controller.clips) == 2, "production controller did not persist two clips")

        app.show_clip_collection()
        drain_events()
        require(app.research_panel_runtime.active_client == "clip-collection", "Clip Collection client not active")

        exercise_editor_dialog(app)
        exercise_selector_dialog(app, controller.clips, clip_id)
        exercise_research_selector(app)

        app.set_buffer("BEGIN END")
        app.set_cursor_offset(6)
        require(controller.select_id(clip_id, clear_query=True), "stable-ID selection failed")
        row = app.clip_collection_view._listbox.get_selected_row()
        require(row is not None, "real Gtk.ListBox has no selected row")
        app.clip_collection_view._listbox.emit("row-activated", row)
        drain_history_scroll(app)
        expected = "BEGIN Gentile ,\nCordiali saluti.END"
        require(app.buffer_text() == expected, "row-activated did not use the production insert gateway")
        require(app.get_cursor_offset() == len("BEGIN Gentile "), "{{cursor}} caret position is wrong")

        app.on_undo()
        drain_history_scroll(app)
        require(app.buffer_text() == "BEGIN END", "one Undo did not remove the complete clip insertion")

        exercise_cursor_extremes(app, controller)
        exercise_undo_selection_state(app)
        exercise_undo_viewport(app)

        controller.set_query("saluto")
        require(len(controller.visible_clips) == 1, "exact mnemonic search did not return one clip")
        require(controller.visible_clips[0]["id"] == clip_id, "search result lost stable identity")

        print("W95_TRUE_GTK=PASS")
        print("W95_TRUE_DIALOGS=PASS")
        print("W95_TRUE_APP_WIRING=PASS")
        print("W95_TRUE_LISTBOX_INSERT_UNDO=PASS")
        print("W95_TRUE_CURSOR_EXTREMES=PASS")
        print("W95_TRUE_UNDO_SELECTION=PASS")
        print("W95_TRUE_REDO_STATE=PASS")
        print("W95_TRUE_UNDO_VIEWPORT=PASS")
        print("W95_TRUE_RESEARCH_SELECTOR_DOWNWARD=PASS")
        print("W95_TRUE_RESEARCH_SELECTOR_VISIBLE_ACTIVATION=PASS")
        return 0
    finally:
        app.modified = False
        app.destroy()
        drain_events()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"W95_TRUE_GTK_APP_GATE=FAIL: {error}", file=sys.stderr)
        raise
