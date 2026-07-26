"""Single controlled adapter for synchronous GTK 3 modal loops.

The adapter is GTK-free: callers own dialog construction, semantic controls and
response handling.  Keeping the nested-loop call in one module makes it easy to
replace or instrument without leaking modal ownership into models/controllers.
"""
from __future__ import annotations


def run_modal(dialog) -> int:
    runner = getattr(dialog, "run", None)
    if not callable(runner):
        raise TypeError("dialog must provide a callable run() method")
    return int(dialog.run())


def destroy_modal(dialog) -> None:
    destroyer = getattr(dialog, "destroy", None)
    if not callable(destroyer):
        raise TypeError("dialog must provide a callable destroy() method")
    dialog.destroy()
