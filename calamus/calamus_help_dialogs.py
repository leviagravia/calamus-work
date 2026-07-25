"""GTK presentation for the canonical Calamus user guide."""
from __future__ import annotations

from dataclasses import dataclass

from gi.repository import Gtk

from calamus_help import HelpSection, parse_user_guide_sections


@dataclass(frozen=True)
class UserGuideWidgets:
    dialog: Gtk.Dialog
    topics: Gtk.ListBox
    text_view: Gtk.TextView
    sections: tuple[HelpSection, ...]


def build_user_guide_dialog(parent, text: str) -> UserGuideWidgets:
    sections = parse_user_guide_sections(text)
    dialog = Gtk.Dialog(title="Calamus User Guide", transient_for=parent, modal=True)
    dialog.add_buttons("Close", Gtk.ResponseType.CLOSE)
    dialog.set_default_size(880, 620)

    content = dialog.get_content_area()
    content.set_spacing(8)
    content.set_border_width(10)

    paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
    paned.set_wide_handle(True)
    content.pack_start(paned, True, True, 0)

    topics = Gtk.ListBox()
    topics.set_selection_mode(Gtk.SelectionMode.SINGLE)
    topics.set_size_request(245, -1)
    for section in sections:
        row = Gtk.ListBoxRow()
        label = Gtk.Label(label=section.title)
        label.set_xalign(0)
        label.set_line_wrap(True)
        label.set_margin_start(10)
        label.set_margin_end(10)
        label.set_margin_top(7)
        label.set_margin_bottom(7)
        row.add(label)
        topics.add(row)

    topic_scroll = Gtk.ScrolledWindow()
    topic_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    topic_scroll.add(topics)
    paned.pack1(topic_scroll, resize=False, shrink=False)

    text_view = Gtk.TextView()
    text_view.set_editable(False)
    text_view.set_cursor_visible(False)
    text_view.set_wrap_mode(Gtk.WrapMode.WORD)
    text_view.set_left_margin(18)
    text_view.set_right_margin(18)
    text_view.set_top_margin(14)
    text_view.set_bottom_margin(14)

    text_scroll = Gtk.ScrolledWindow()
    text_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    text_scroll.add(text_view)
    paned.pack2(text_scroll, resize=True, shrink=True)

    def show_section(_box, row) -> None:
        if row is None:
            return
        index = row.get_index()
        if not 0 <= index < len(sections):
            return
        section = sections[index]
        body = f"{section.title}\n\n{section.body}".rstrip() + "\n"
        text_view.get_buffer().set_text(body)
        text_view.scroll_to_iter(text_view.get_buffer().get_start_iter(), 0.0, False, 0.0, 0.0)

    topics.connect("row-selected", show_section)
    dialog.show_all()
    topics.select_row(topics.get_row_at_index(0))
    return UserGuideWidgets(dialog, topics, text_view, sections)


def show_user_guide(parent, text: str) -> None:
    widgets = build_user_guide_dialog(parent, text)
    widgets.dialog.run()
    widgets.dialog.destroy()
