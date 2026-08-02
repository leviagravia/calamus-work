"""GTK-free coalesced query delivery for the Bibliography Manager.

The UI may receive many text changes while the user types.  This dispatcher
owns one pending delivery, cancels obsolete generations, and publishes only the
latest query after a quiet interval.  Scheduling is injected so the contract is
fully testable without GTK.
"""
from __future__ import annotations

from typing import Callable, Hashable


Schedule = Callable[[int, Callable[[], bool]], Hashable]
Cancel = Callable[[Hashable], None]
Deliver = Callable[[str], None]

DEFAULT_BIBLIOGRAPHY_SEARCH_DELAY_MS = 150


class CoalescedQueryDispatcher:
    def __init__(
        self,
        *,
        delay_ms: int,
        schedule: Schedule,
        cancel: Cancel,
        deliver: Deliver,
    ) -> None:
        if not isinstance(delay_ms, int) or delay_ms < 1:
            raise ValueError("delay_ms must be a positive integer")
        if not callable(schedule) or not callable(cancel) or not callable(deliver):
            raise TypeError("schedule, cancel and deliver must be callable")
        self._delay_ms = delay_ms
        self._schedule = schedule
        self._cancel = cancel
        self._deliver = deliver
        self._generation = 0
        self._pending: Hashable | None = None
        self._pending_query = ""
        self._last_delivered_query = ""
        self._delivery_count = 0
        self._disposed = False

    @property
    def delay_ms(self) -> int:
        return self._delay_ms

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def pending(self) -> bool:
        return self._pending is not None

    @property
    def pending_query(self) -> str:
        return self._pending_query

    @property
    def last_delivered_query(self) -> str:
        return self._last_delivered_query

    @property
    def delivery_count(self) -> int:
        return self._delivery_count

    def submit(self, query: str) -> int:
        if self._disposed:
            raise RuntimeError("dispatcher is disposed")
        if not isinstance(query, str):
            raise TypeError("query must be str")
        self._generation += 1
        generation = self._generation
        self._pending_query = query
        if self._pending is not None:
            self._cancel(self._pending)
            self._pending = None

        def publish() -> bool:
            if self._disposed or generation != self._generation:
                return False
            self._pending = None
            self._last_delivered_query = query
            self._delivery_count += 1
            self._deliver(query)
            return False

        self._pending = self._schedule(self._delay_ms, publish)
        return generation

    def cancel_pending(self) -> None:
        if self._pending is not None:
            self._cancel(self._pending)
            self._pending = None
        self._generation += 1
        self._pending_query = ""

    def dispose(self) -> None:
        if self._disposed:
            return
        self.cancel_pending()
        self._disposed = True
