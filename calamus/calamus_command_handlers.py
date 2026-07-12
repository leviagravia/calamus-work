"""Pure low-risk command handlers for the Calamus Command/Control Layer.

W9 handlers are intentionally pure and GTK-free.

They operate only on explicit text supplied through CommandContext.data.
They do not read or write files.
They do not access GUI editor buffer objects.
They do not touch undo/redo, dirty state, session state, or application lifecycle.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calamus_command_context import CommandContext, CommandResult
from calamus_writing import (
    clean_pdf_text,
    document_statistics,
    join_lines,
    reflow_paragraph,
    remove_extra_spaces,
    remove_trailing_spaces,
    sentence_case,
    smart_typography,
    sort_lines,
    title_case,
)


TextTransform = Callable[[str], str]


def _context_text(context: CommandContext) -> str:
    text = context.get("text", "")
    if text is None:
        return ""
    if not isinstance(text, str):
        raise TypeError("CommandContext data['text'] must be a string")
    return text


def _text_result(original: str, transformed: str) -> CommandResult:
    return CommandResult.ok(
        changed=(transformed != original),
        value={"text": transformed},
    )


def _transform_text(context: CommandContext, transform: TextTransform) -> CommandResult:
    original = _context_text(context)
    transformed = transform(original)
    return _text_result(original, transformed)


def handle_uppercase(context: CommandContext) -> CommandResult:
    return _transform_text(context, str.upper)


def handle_lowercase(context: CommandContext) -> CommandResult:
    return _transform_text(context, str.lower)


def handle_sort_lines(context: CommandContext) -> CommandResult:
    original = _context_text(context)
    reverse = context.get("reverse", False)
    if not isinstance(reverse, bool):
        raise TypeError("CommandContext data['reverse'] must be a boolean")
    transformed = sort_lines(original, reverse=reverse)
    return _text_result(original, transformed)


def handle_clean_pdf(context: CommandContext) -> CommandResult:
    return _transform_text(context, clean_pdf_text)


def handle_remove_extra_spaces(context: CommandContext) -> CommandResult:
    return _transform_text(context, remove_extra_spaces)


def handle_remove_trailing_spaces(context: CommandContext) -> CommandResult:
    return _transform_text(context, remove_trailing_spaces)


def handle_smart_typography(context: CommandContext) -> CommandResult:
    return _transform_text(context, smart_typography)


def handle_join_lines(context: CommandContext) -> CommandResult:
    return _transform_text(context, join_lines)


def handle_title_case(context: CommandContext) -> CommandResult:
    return _transform_text(context, title_case)


def handle_sentence_case(context: CommandContext) -> CommandResult:
    return _transform_text(context, sentence_case)


def handle_reflow_paragraph(context: CommandContext) -> CommandResult:
    original = _context_text(context)
    width = context.get("width", 72)
    if not isinstance(width, int):
        raise TypeError("CommandContext data['width'] must be an integer")
    transformed = reflow_paragraph(original, width=width)
    return _text_result(original, transformed)


def handle_statistics(context: CommandContext) -> CommandResult:
    text = _context_text(context)
    return CommandResult.ok(
        changed=False,
        value={"statistics": document_statistics(text)},
    )


PURE_HANDLER_BY_COMMAND_ID: dict[str, Callable[[CommandContext], CommandResult]] = {
    "edit.lowercase": handle_lowercase,
    "edit.uppercase": handle_uppercase,
    "writing.clean-pdf": handle_clean_pdf,
    "writing.join-lines": handle_join_lines,
    "writing.reflow-paragraph": handle_reflow_paragraph,
    "writing.remove-extra-spaces": handle_remove_extra_spaces,
    "writing.remove-trailing-spaces": handle_remove_trailing_spaces,
    "writing.sentence-case": handle_sentence_case,
    "writing.smart-typography": handle_smart_typography,
    "writing.sort-lines": handle_sort_lines,
    "writing.statistics": handle_statistics,
    "writing.title-case": handle_title_case,
}


def pure_handler_for(command_id: str) -> Callable[[CommandContext], CommandResult] | None:
    """Return a pure handler for a command id, if W9 provides one."""

    return PURE_HANDLER_BY_COMMAND_ID.get(command_id)


def handled_command_ids() -> tuple[str, ...]:
    """Return command ids that have pure W9 handlers."""

    return tuple(sorted(PURE_HANDLER_BY_COMMAND_ID))
