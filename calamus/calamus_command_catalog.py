"""Low-risk command catalog for the Calamus Command/Control Layer.

W8 introduced metadata-only command identity.

W9 attaches pure, GTK-free handlers only to commands that can be tested in
isolation on explicit text supplied through CommandContext.  The catalog is
still not wired into ``bin/calamus`` and does not change GUI behaviour.
"""

from __future__ import annotations

from calamus_command_handlers import pure_handler_for
from calamus_command_registry import CommandRegistry, CommandSpec


LOW_RISK_COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec(
        "writing.statistics",
        "Document Statistics",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "read-only", "pure-handler"),
        description="Return document statistics for explicit context text.",
        handler=pure_handler_for("writing.statistics"),
    ),
    CommandSpec(
        "writing.insert-date-time",
        "Insert Date/Time",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-insertion"),
        description="Insert the current date/time. Kept metadata-only because it is time-dependent.",
    ),
    CommandSpec(
        "writing.sort-lines",
        "Sort Lines",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "text-transform", "pure-handler"),
        description="Sort explicit context text lines.",
        handler=pure_handler_for("writing.sort-lines"),
    ),
    CommandSpec(
        "writing.clean-pdf",
        "Clean PDF Text",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "text-transform", "pure-handler"),
        description="Clean explicit context PDF-copied text.",
        handler=pure_handler_for("writing.clean-pdf"),
    ),
    CommandSpec(
        "writing.remove-extra-spaces",
        "Remove Extra Spaces",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "text-transform", "pure-handler"),
        description="Normalize extra internal spacing in explicit context text.",
        handler=pure_handler_for("writing.remove-extra-spaces"),
    ),
    CommandSpec(
        "writing.remove-trailing-spaces",
        "Remove Trailing Spaces",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "text-transform", "pure-handler"),
        description="Remove trailing whitespace from explicit context text.",
        handler=pure_handler_for("writing.remove-trailing-spaces"),
    ),
    CommandSpec(
        "writing.smart-typography",
        "Smart Typography",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "text-transform", "pure-handler"),
        description="Apply simple typographic substitutions to explicit context text.",
        handler=pure_handler_for("writing.smart-typography"),
    ),
    CommandSpec(
        "writing.reflow-paragraph",
        "Reflow Paragraph",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "text-transform", "pure-handler"),
        description="Reflow explicit context paragraph text.",
        handler=pure_handler_for("writing.reflow-paragraph"),
    ),
    CommandSpec(
        "writing.join-lines",
        "Join Lines",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "text-transform", "pure-handler"),
        description="Join explicit context text lines.",
        handler=pure_handler_for("writing.join-lines"),
    ),
    CommandSpec(
        "writing.title-case",
        "Title Case",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "text-transform", "pure-handler"),
        description="Convert explicit context text to title case.",
        handler=pure_handler_for("writing.title-case"),
    ),
    CommandSpec(
        "writing.sentence-case",
        "Sentence Case",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("writing", "text-transform", "pure-handler"),
        description="Convert explicit context text to sentence case.",
        handler=pure_handler_for("writing.sentence-case"),
    ),
    CommandSpec(
        "edit.uppercase",
        "Uppercase",
        menu_path="Edit",
        shortcut="<Control><Shift>U",
        risk_class="low",
        flags=("edit", "text-transform", "pure-handler"),
        description="Convert explicit context text to uppercase.",
        handler=pure_handler_for("edit.uppercase"),
    ),
    CommandSpec(
        "edit.lowercase",
        "Lowercase",
        menu_path="Edit",
        shortcut="<Control><Shift>L",
        risk_class="low",
        flags=("edit", "text-transform", "pure-handler"),
        description="Convert explicit context text to lowercase.",
        handler=pure_handler_for("edit.lowercase"),
    ),
)


def low_risk_command_specs() -> tuple[CommandSpec, ...]:
    """Return the W8/W9 low-risk command specs."""

    return LOW_RISK_COMMANDS


def build_low_risk_registry() -> CommandRegistry:
    """Build a registry containing W8/W9 low-risk commands."""

    return CommandRegistry(low_risk_command_specs())
