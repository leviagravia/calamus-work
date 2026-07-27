"""Controlled GTK-free ownership for synchronous GTK 3 modal sessions.

Callers construct GTK widgets, but one small adapter owns the nested-loop
boundary and teardown ordering.  The adapter deliberately imports no GI
namespace, so models/controllers remain toolkit-free and the boundary can be
unit-tested with ordinary Python doubles.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


SourceRemover = Callable[[int], object]


def _callable_attribute(owner, name: str):
    value = getattr(owner, name, None)
    if not callable(value):
        raise TypeError(f"dialog must provide a callable {name}() method")
    return value


def _hide_if_possible(dialog) -> None:
    hider = getattr(dialog, "hide", None)
    if callable(hider):
        hider()


@dataclass
class ModalSession:
    """Own one modal loop, registered sources, and deterministic teardown.

    Registered GLib source identifiers are removed before widget destruction.
    The selected result must be copied by the caller after :meth:`run` returns
    and before :meth:`close` or context-manager exit destroys the dialog.
    """

    dialog: object
    _sources: list[tuple[int, SourceRemover]] = field(default_factory=list)
    _closed: bool = False
    _response: int | None = None

    @property
    def response(self) -> int | None:
        return self._response

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def source_count(self) -> int:
        return len(self._sources)

    def register_source(self, source_id: int, remover: SourceRemover) -> int:
        if self._closed:
            raise RuntimeError("modal session is already closed")
        if not isinstance(source_id, int) or isinstance(source_id, bool) or source_id <= 0:
            raise ValueError("source_id must be a positive integer")
        if not callable(remover):
            raise TypeError("source remover must be callable")
        self._sources.append((source_id, remover))
        return source_id

    def run(self) -> int:
        if self._closed:
            raise RuntimeError("modal session is already closed")
        runner = _callable_attribute(self.dialog, "run")
        try:
            self._response = int(runner())
            return self._response
        finally:
            # A hidden dialog cannot continue presenting stale controls while
            # the caller copies the semantic result and performs teardown.
            _hide_if_possible(self.dialog)

    def close(self) -> None:
        if self._closed:
            return
        cleanup_error: BaseException | None = None
        for source_id, remover in reversed(self._sources):
            try:
                remover(source_id)
            except BaseException as error:  # preserve cleanup evidence
                if cleanup_error is None:
                    cleanup_error = error
        self._sources.clear()
        try:
            _hide_if_possible(self.dialog)
            destroyer = _callable_attribute(self.dialog, "destroy")
            destroyer()
        finally:
            self._closed = True
        if cleanup_error is not None:
            raise cleanup_error

    def __enter__(self) -> "ModalSession":
        if self._closed:
            raise RuntimeError("modal session is already closed")
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        try:
            self.close()
        except BaseException:
            if exc is None:
                raise
        return False


def run_modal(dialog) -> int:
    """Compatibility facade: run one dialog and hide it before returning."""
    return ModalSession(dialog).run()


def destroy_modal(dialog) -> None:
    """Compatibility facade: hide and destroy one dialog in that order."""
    _hide_if_possible(dialog)
    destroyer = _callable_attribute(dialog, "destroy")
    destroyer()
