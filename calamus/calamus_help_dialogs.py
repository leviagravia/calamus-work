"""GTK presentation for the canonical Calamus user guide."""
from __future__ import annotations

from dataclasses import dataclass

from gi.repository import Gtk, Pango

from calamus_help import (
    HelpSection,
    HelpTopic,
    parse_user_guide_sections,
    parse_user_guide_topics,
)


@dataclass(frozen=True)
class UserGuideWidgets:
    dialog: Gtk.Dialog
    topics: Gtk.TreeView
    navigator: Gtk.TreeView
    text_view: Gtk.TextView
    sections: tuple[HelpSection, ...]
    help_topics: tuple[HelpTopic, ...]
    topic_paths: tuple[Gtk.TreePath, ...]


def _render_topic(text_view: Gtk.TextView, topic: HelpTopic) -> None:
    body = f"{topic.title}\n\n{topic.body}".rstrip() + "\n"
    buffer = text_view.get_buffer()
    buffer.set_text(body)
    text_view.scroll_to_iter(buffer.get_start_iter(), 0.0, False, 0.0, 0.0)


def select_help_topic(widgets: UserGuideWidgets, title: str) -> bool:
    """Select the first exact Navigator topic title; useful to GTK callers/tests."""
    for index, topic in enumerate(widgets.help_topics):
        if topic.title != title:
            continue
        path = widgets.topic_paths[index]
        parent = path.copy()
        while parent.up():
            widgets.navigator.expand_row(parent, False)
        widgets.navigator.expand_to_path(path)
        widgets.navigator.get_selection().select_path(path)
        widgets.navigator.scroll_to_cell(path, None, True, 0.35, 0.0)
        return True
    return False


def build_user_guide_dialog(parent, text: str) -> UserGuideWidgets:
    sections = parse_user_guide_sections(text)
    help_topics = parse_user_guide_topics(text)
    dialog = Gtk.Dialog(title="Calamus User Guide", transient_for=parent, modal=True)
    dialog.add_buttons("Close", Gtk.ResponseType.CLOSE)
    dialog.set_default_size(1040, 700)

    content = dialog.get_content_area()
    content.set_spacing(8)
    content.set_border_width(10)

    paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
    paned.set_wide_handle(True)
    paned.set_position(315)
    content.pack_start(paned, True, True, 0)

    navigator_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    navigator_title = Gtk.Label()
    navigator_title.set_markup("<b>Guide Navigator</b>")
    navigator_title.set_xalign(0)
    navigator_title.set_margin_start(6)
    navigator_title.set_margin_top(2)
    navigator_box.pack_start(navigator_title, False, False, 0)

    store = Gtk.TreeStore(str, int)
    topic_iters: dict[int, Gtk.TreeIter] = {}
    topic_paths: list[Gtk.TreePath] = []
    for index, topic in enumerate(help_topics):
        parent_iter = topic_iters.get(topic.parent_index)
        tree_iter = store.append(parent_iter, (topic.title, index))
        topic_iters[index] = tree_iter
        topic_paths.append(store.get_path(tree_iter))

    navigator = Gtk.TreeView(model=store)
    navigator.set_headers_visible(False)
    navigator.set_enable_search(True)
    navigator.set_search_column(0)
    navigator.set_tooltip_text(
        "Topics and subtopics from the User Guide. Use arrows to expand or collapse."
    )
    renderer = Gtk.CellRendererText()
    renderer.set_property("wrap-mode", Pango.WrapMode.WORD)
    renderer.set_property("wrap-width", 270)
    column = Gtk.TreeViewColumn("Guide Navigator", renderer, text=0)
    column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
    navigator.append_column(column)

    topic_scroll = Gtk.ScrolledWindow()
    topic_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    topic_scroll.add(navigator)
    navigator_box.pack_start(topic_scroll, True, True, 0)
    paned.pack1(navigator_box, resize=False, shrink=False)

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

    def show_topic(selection: Gtk.TreeSelection) -> None:
        model, tree_iter = selection.get_selected()
        if tree_iter is None:
            return
        index = int(model.get_value(tree_iter, 1))
        if not 0 <= index < len(help_topics):
            return
        _render_topic(text_view, help_topics[index])

    navigator.get_selection().connect("changed", show_topic)
    dialog.show_all()

    # Show the hierarchy immediately: H2 chapters are expanded to reveal H3
    # subtopics, while deeper H4 material remains available on demand.
    root_iter = store.get_iter_first()
    while root_iter is not None:
        navigator.expand_row(store.get_path(root_iter), False)
        root_iter = store.iter_next(root_iter)

    widgets = UserGuideWidgets(
        dialog=dialog,
        topics=navigator,
        navigator=navigator,
        text_view=text_view,
        sections=sections,
        help_topics=help_topics,
        topic_paths=tuple(topic_paths),
    )
    if not select_help_topic(widgets, "Current command menu (W92 candidate)"):
        navigator.get_selection().select_path(topic_paths[0])
    navigator.grab_focus()
    return widgets


def show_user_guide(parent, text: str) -> None:
    widgets = build_user_guide_dialog(parent, text)
    widgets.dialog.run()
    widgets.dialog.destroy()
