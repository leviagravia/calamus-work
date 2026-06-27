"""Pure navigation helpers for Calamus.

These helpers intentionally do not import GTK and do not mutate buffers.
They only normalize line numbers for editor navigation commands.
"""


def _safe_int(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp_line_number(requested, total_lines):
    """Clamp a 1-based line number to the available 1-based line range."""
    total = max(1, _safe_int(total_lines, 1))
    line = _safe_int(requested, 1)
    if line < 1:
        return 1
    if line > total:
        return total
    return line


def line_to_buffer_index(line_no, line_count):
    """Convert a requested 1-based line number to a safe 0-based buffer line index."""
    return clamp_line_number(line_no, line_count) - 1
