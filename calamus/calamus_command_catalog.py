"""Low-risk command catalog for the Calamus Command/Control Layer.

W8 registers command identity and metadata only.

No command in this catalog has an operational handler yet.  Existing Calamus
features remain wired exactly as before.  This file lets the layer know about
safe, writing-oriented commands before any dispatch migration begins.
"""

from __future__ import annotations

from calamus_command_registry import CommandRegistry, CommandSpec


LOW_RISK_COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec(
        "writing.statistics",
        "Document Statistics",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "read-only"),
        description="Show document statistics. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.insert-date-time",
        "Insert Date/Time",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-insertion"),
        description="Insert the current date/time. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.sort-lines",
        "Sort Lines",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-transform"),
        description="Sort selected/all lines. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.clean-pdf",
        "Clean PDF Text",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-transform"),
        description="Clean copied PDF text. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.remove-extra-spaces",
        "Remove Extra Spaces",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-transform"),
        description="Normalize extra internal spacing. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.remove-trailing-spaces",
        "Remove Trailing Spaces",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-transform"),
        description="Remove trailing whitespace. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.smart-typography",
        "Smart Typography",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-transform"),
        description="Apply simple typographic substitutions. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.reflow-paragraph",
        "Reflow Paragraph",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-transform"),
        description="Reflow paragraph text. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.join-lines",
        "Join Lines",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-transform"),
        description="Join selected/all lines. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.title-case",
        "Title Case",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-transform"),
        description="Convert text to title case. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "writing.sentence-case",
        "Sentence Case",
        menu_path="Writing",
        shortcut="",
        risk_class="low",
        flags=("metadata-only", "writing", "text-transform"),
        description="Convert text to sentence case. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "edit.uppercase",
        "Uppercase",
        menu_path="Edit",
        shortcut="<Control><Shift>U",
        risk_class="low",
        flags=("metadata-only", "edit", "text-transform"),
        description="Convert selected text to uppercase. Registered only; no layer handler yet.",
    ),
    CommandSpec(
        "edit.lowercase",
        "Lowercase",
        menu_path="Edit",
        shortcut="<Control><Shift>L",
        risk_class="low",
        flags=("metadata-only", "edit", "text-transform"),
        description="Convert selected text to lowercase. Registered only; no layer handler yet.",
    ),
)


def low_risk_command_specs() -> tuple[CommandSpec, ...]:
    """Return the W8 low-risk command specs."""

    return LOW_RISK_COMMANDS


def build_low_risk_registry() -> CommandRegistry:
    """Build a registry containing only W8 low-risk metadata commands."""

    return CommandRegistry(low_risk_command_specs())
