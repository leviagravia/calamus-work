"""GTK dialogs for W86 Tag Integrity maintenance."""
from __future__ import annotations

from dataclasses import dataclass

from calamus_tag_integrity import (
    TAG_ACTION_NORMALIZE_ALL,
    TAG_ACTION_REMOVE,
    TAG_ACTION_RENAME_MERGE,
    TAG_RENAME_MODE_MERGE,
    TAG_RENAME_MODE_NORMALIZE,
    TAG_RENAME_MODE_RENAME,
    TAG_SCOPE_ALL,
    TAG_SCOPE_BOTH,
    TAG_SCOPE_REFERENCES,
    TAG_SCOPE_SCRATCHPAD,
    TAG_SCOPE_SOURCE_NOTES,
    TagInventory,
    TagInventoryItem,
    TagMutationPlan,
    tag_identity,
)
from calamus_tag_integrity_controller import TagCommandResult

_RESPONSE_SHOW_USES = 101
_RESPONSE_RENAME = 102
_RESPONSE_REMOVE = 103
_RESPONSE_NORMALIZE = 104


@dataclass(frozen=True)
class TagIntegrityRequest:
    action: str
    scope: str
    source_tag: str = ""
    target_tag: str = ""


@dataclass(frozen=True)
class TagIntegrityDialogWidgets:
    dialog: object
    scope: object
    tree: object
    store: object


def build_tag_integrity_dialog(parent, inventory: TagInventory) -> TagIntegrityDialogWidgets:
    from gi.repository import Gtk, Pango

    if not isinstance(inventory, TagInventory):
        raise TypeError("inventory must be TagInventory")

    dialog = Gtk.Dialog(title="Tag Integrity", transient_for=parent, modal=True)
    dialog.add_button("Close", Gtk.ResponseType.CLOSE)
    dialog.add_button("Show Uses", _RESPONSE_SHOW_USES)
    dialog.add_button("Rename / Merge…", _RESPONSE_RENAME)
    dialog.add_button("Remove Everywhere…", _RESPONSE_REMOVE)
    dialog.add_button("Normalize All…", _RESPONSE_NORMALIZE)
    dialog.set_default_size(800, 520)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    outer.set_border_width(12)
    dialog.get_content_area().pack_start(outer, True, True, 0)

    heading = Gtk.Label(label="Maintain tags across References and the current Source Notes sidecar")
    heading.set_xalign(0)
    heading.get_style_context().add_class("heading")
    outer.pack_start(heading, False, False, 0)

    note = Gtk.Label(
        label=(
            "The inventory is derived from Markdown authorities. Colours are stable visual "
            "swatches only and are not stored. Every write is previewed and cancelled if "
            "References or Source Notes changes after the preview."
        )
    )
    note.set_xalign(0)
    note.set_line_wrap(True)
    outer.pack_start(note, False, False, 0)

    scope_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    scope_label = Gtk.Label(label="Operation scope:")
    scope_label.set_xalign(0)
    scope = Gtk.ComboBoxText()
    scope.append(TAG_SCOPE_BOTH, "References and current Source Notes")
    scope.append(TAG_SCOPE_REFERENCES, "References only")
    scope.append(TAG_SCOPE_SOURCE_NOTES, "Current Source Notes only")
    scope.set_active_id(TAG_SCOPE_BOTH)
    scope_row.pack_start(scope_label, False, False, 0)
    scope_row.pack_start(scope, False, False, 0)
    outer.pack_start(scope_row, False, False, 0)

    # color, display, variants, references, notes, logical identity
    store = Gtk.ListStore(str, str, str, int, int, str)
    for item in inventory.items:
        variants = " · ".join(item.variants)
        store.append([
            item.color,
            item.canonical,
            variants,
            item.reference_count,
            item.source_note_count,
            item.identity,
        ])

    tree = Gtk.TreeView(model=store)
    tree.set_headers_visible(True)
    tree.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

    swatch = Gtk.CellRendererText()
    swatch.set_property("text", "●")
    column = Gtk.TreeViewColumn("", swatch)
    column.add_attribute(swatch, "foreground", 0)
    tree.append_column(column)

    for title, index, expand in (
        ("Tag", 1, False),
        ("Recorded variants", 2, True),
        ("References", 3, False),
        ("Source Notes", 4, False),
    ):
        renderer = Gtk.CellRendererText()
        if index == 2:
            renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn(title, renderer, text=index)
        column.set_resizable(True)
        column.set_expand(expand)
        tree.append_column(column)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(tree)
    outer.pack_start(scroll, True, True, 0)

    summary = Gtk.Label(
        label=(
            f"{len(inventory.items)} logical tag(s); "
            f"{inventory.issue_count} identity group(s) need normalization."
        )
    )
    summary.set_xalign(0)
    outer.pack_start(summary, False, False, 0)

    dialog.show_all()
    normalize_button = dialog.get_widget_for_response(_RESPONSE_NORMALIZE)
    normalize_button.set_sensitive(inventory.issue_count > 0)
    has_items = bool(inventory.items)
    for response in (_RESPONSE_SHOW_USES, _RESPONSE_RENAME, _RESPONSE_REMOVE):
        dialog.get_widget_for_response(response).set_sensitive(has_items)
    if has_items:
        tree.get_selection().select_path(0)
    return TagIntegrityDialogWidgets(dialog, scope, tree, store)


def run_tag_integrity_dialog(parent, inventory: TagInventory) -> TagIntegrityRequest | None:
    from gi.repository import Gtk

    widgets = build_tag_integrity_dialog(parent, inventory)
    dialog, scope, tree = widgets.dialog, widgets.scope, widgets.tree
    result: TagIntegrityRequest | None = None
    while True:
        response = dialog.run()
        if response in {Gtk.ResponseType.CLOSE, Gtk.ResponseType.CANCEL, Gtk.ResponseType.DELETE_EVENT}:
            break
        selected = _selected_item(tree, inventory)
        selected_scope = scope.get_active_id() or TAG_SCOPE_BOTH
        if response == _RESPONSE_SHOW_USES:
            if selected is None:
                _message(dialog, "Select a tag", "Select one tag before showing its uses.", error=True)
            else:
                show_tag_uses(dialog, selected)
            continue
        if response == _RESPONSE_RENAME:
            if selected is None:
                _message(dialog, "Select a tag", "Select one tag before renaming it.", error=True)
                continue
            target = run_tag_target_dialog(dialog, selected, inventory)
            if target is None:
                continue
            result = TagIntegrityRequest(
                TAG_ACTION_RENAME_MERGE,
                selected_scope,
                selected.canonical,
                target,
            )
            break
        if response == _RESPONSE_REMOVE:
            if selected is None:
                _message(dialog, "Select a tag", "Select one tag before removing it.", error=True)
                continue
            result = TagIntegrityRequest(
                TAG_ACTION_REMOVE,
                selected_scope,
                selected.canonical,
                "",
            )
            break
        if response == _RESPONSE_NORMALIZE:
            result = TagIntegrityRequest(TAG_ACTION_NORMALIZE_ALL, selected_scope)
            break
    dialog.destroy()
    return result


def _selected_item(tree, inventory: TagInventory) -> TagInventoryItem | None:
    model, iterator = tree.get_selection().get_selected()
    if iterator is None:
        return None
    identity = model.get_value(iterator, 5)
    return inventory.get(identity)


def run_tag_target_dialog(
    parent,
    item: TagInventoryItem,
    inventory: TagInventory | None = None,
) -> str | None:
    from gi.repository import Gtk

    dialog = Gtk.Dialog(title="Rename or Merge Tag", transient_for=parent, modal=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Preview Impact", Gtk.ResponseType.OK)
    dialog.set_default_size(520, -1)

    grid = Gtk.Grid(column_spacing=10, row_spacing=10)
    grid.set_border_width(12)
    dialog.get_content_area().pack_start(grid, True, True, 0)

    old_label = Gtk.Label(label="Current logical tag")
    old_label.set_xalign(0)
    old_value = Gtk.Label(label=item.canonical)
    old_value.set_xalign(0)
    target_label = Gtk.Label(label="Target display")
    target_label.set_xalign(0)
    target = Gtk.Entry()
    target.set_text(item.canonical)
    target.set_activates_default(True)
    explanation = Gtk.Label(
        label=(
            "A new logical identity renames the tag. An existing logical identity merges into "
            "that tag. A different spelling of the same identity normalizes its display."
        )
    )
    explanation.set_xalign(0)
    explanation.set_line_wrap(True)
    mode = Gtk.Label()
    mode.set_name("tag-target-mode")
    mode.set_xalign(0)
    mode.set_line_wrap(True)

    def update_mode(entry) -> None:
        value = entry.get_text().strip()
        logical = tag_identity(value)
        if not logical:
            text = "Mode: enter a target tag."
        elif logical == item.identity:
            text = "Mode: normalize the spelling of the selected logical tag."
        elif inventory is not None and inventory.get(value) is not None:
            existing = inventory.get(value)
            text = f"Mode: merge into existing tag ‘{existing.canonical}’."
        else:
            text = "Mode: rename to a new logical tag."
        mode.set_text(text)

    target.connect("changed", update_mode)
    update_mode(target)

    grid.attach(old_label, 0, 0, 1, 1)
    grid.attach(old_value, 1, 0, 1, 1)
    grid.attach(target_label, 0, 1, 1, 1)
    grid.attach(target, 1, 1, 1, 1)
    grid.attach(mode, 0, 2, 2, 1)
    grid.attach(explanation, 0, 3, 2, 1)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()
    result = None
    while True:
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            break
        value = target.get_text().strip()
        if not value:
            _message(dialog, "Target tag required", "Enter a non-empty target tag.", error=True)
            continue
        result = value
        break
    dialog.destroy()
    return result


def show_tag_uses(parent, item: TagInventoryItem) -> None:
    from gi.repository import Gtk, Pango

    dialog = Gtk.Dialog(title=f"Tag Uses — {item.canonical}", transient_for=parent, modal=True)
    dialog.add_button("Close", Gtk.ResponseType.CLOSE)
    dialog.set_default_size(700, 480)

    view = Gtk.TextView()
    view.set_editable(False)
    view.set_cursor_visible(False)
    view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    view.modify_font(Pango.FontDescription("Monospace 10"))
    lines = [
        f"Logical identity: {item.identity}",
        f"Recorded variants: {', '.join(item.variants)}",
        f"References: {item.reference_count}",
        f"Source Notes: {item.source_note_count}",
        f"Scratchpad: {item.scratchpad_count}",
        "",
    ]
    for use in item.uses:
        label = {
            TAG_SCOPE_REFERENCES: "REFERENCE",
            TAG_SCOPE_SOURCE_NOTES: "SOURCE NOTE",
            TAG_SCOPE_SCRATCHPAD: "SCRATCHPAD",
        }.get(use.authority, use.authority.upper())
        lines.append(f"[{label}] {use.owner_label}")
        lines.append(f"  stored as: {use.variant}")
        lines.append("")
    view.get_buffer().set_text("\n".join(lines).rstrip())

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(view)
    area = dialog.get_content_area()
    area.set_border_width(10)
    area.pack_start(scroll, True, True, 0)
    dialog.show_all()
    dialog.run()
    dialog.destroy()


def confirm_tag_mutation(parent, plan: TagMutationPlan) -> bool:
    from gi.repository import Gtk

    impact = plan.impact
    action_button = "Apply Tag Changes"
    if impact.action == TAG_ACTION_RENAME_MERGE:
        if impact.rename_mode == TAG_RENAME_MODE_MERGE:
            title = f"Merge {impact.source_display} into {impact.target_display}?"
            action_button = "Merge Tags"
        elif impact.rename_mode == TAG_RENAME_MODE_NORMALIZE:
            title = f"Normalize {impact.source_display} as {impact.target_display}?"
            action_button = "Normalize Spelling"
        else:
            title = f"Rename {impact.source_display} to {impact.target_display}?"
            action_button = "Rename Tag"
    elif impact.action == TAG_ACTION_REMOVE:
        title = f"Remove {impact.source_display} everywhere in the selected scope?"
        action_button = "Remove Tag"
    else:
        title = "Normalize all tag identities in the selected scope?"
        action_button = "Normalize All"

    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text=title,
    )
    lines = [
        f"Scope: {_scope_label(impact.scope)}",
        f"References changed: {impact.reference_records_changed}",
        f"Source Notes changed: {impact.source_notes_changed}",
        f"Scratchpad entries changed: {impact.scratchpad_entries_changed}",
        f"Tag occurrences changed or deduplicated: {impact.occurrences_changed}",
        f"Recorded variants involved: {impact.variants_merged}",
        "",
        "The operation will be cancelled if any selected Markdown authority changes after this preview.",
    ]
    dialog.format_secondary_text("\n".join(lines))
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button(action_button, Gtk.ResponseType.OK)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK


def show_tag_result(parent, result: TagCommandResult) -> None:
    if result.succeeded:
        _message(parent, "Tag Integrity completed", result.message, error=False)
        return
    detail = result.message
    if result.recovery_errors:
        detail += "\n\nManual recovery required:\n- " + "\n- ".join(result.recovery_errors)
    title = {
        "stale": "Tag operation cancelled safely",
        "recovery-required": "Tag operation needs manual recovery",
    }.get(result.status, "Tag operation failed")
    _message(parent, title, detail, error=True)


def show_tag_error(parent, title: str, message: str) -> None:
    _message(parent, title, message, error=True)


def _scope_label(scope: str) -> str:
    return {
        TAG_SCOPE_ALL: "References, current Source Notes and current Scratchpad",
        TAG_SCOPE_BOTH: "References and current Source Notes",
        TAG_SCOPE_REFERENCES: "References only",
        TAG_SCOPE_SOURCE_NOTES: "Current Source Notes only",
        TAG_SCOPE_SCRATCHPAD: "Current Scratchpad only",
    }[scope]


def _message(parent, title: str, detail: str, *, error: bool) -> None:
    from gi.repository import Gtk

    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.ERROR if error else Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(detail)
    dialog.run()
    dialog.destroy()
