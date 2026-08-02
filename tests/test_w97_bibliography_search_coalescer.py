"""Exact contract tests for W97 explicit coalesced search delivery."""
from __future__ import annotations

import unittest

from calamus_bibliography_search import CoalescedQueryDispatcher


class FakeScheduler:
    def __init__(self):
        self.next_id = 1
        self.pending = {}
        self.cancelled = []

    def schedule(self, delay, callback):
        identity = self.next_id
        self.next_id += 1
        self.pending[identity] = (delay, callback)
        return identity

    def cancel(self, identity):
        self.cancelled.append(identity)
        self.pending.pop(identity, None)

    def fire(self, identity):
        _, callback = self.pending.pop(identity)
        return callback()


class W97BibliographySearchCoalescerTests(unittest.TestCase):
    def make(self):
        scheduler = FakeScheduler()
        delivered = []
        dispatcher = CoalescedQueryDispatcher(
            delay_ms=150,
            schedule=scheduler.schedule,
            cancel=scheduler.cancel,
            deliver=delivered.append,
        )
        return dispatcher, scheduler, delivered

    def test_only_latest_generation_is_delivered_after_quiet_period(self):
        dispatcher, scheduler, delivered = self.make()
        first = dispatcher.submit("p")
        second = dispatcher.submit("pa")
        third = dispatcher.submit("patristics")
        self.assertEqual((first, second, third), (1, 2, 3))
        self.assertEqual(scheduler.cancelled, [1, 2])
        self.assertEqual(tuple(scheduler.pending), (3,))
        self.assertTrue(dispatcher.pending)
        self.assertFalse(scheduler.fire(3))
        self.assertEqual(delivered, ["patristics"])
        self.assertEqual(dispatcher.delivery_count, 1)
        self.assertEqual(dispatcher.last_delivered_query, "patristics")
        self.assertFalse(dispatcher.pending)

    def test_cancel_pending_prevents_stale_delivery(self):
        dispatcher, scheduler, delivered = self.make()
        dispatcher.submit("stale")
        dispatcher.cancel_pending()
        self.assertEqual(delivered, [])
        self.assertFalse(dispatcher.pending)
        self.assertEqual(scheduler.pending, {})

    def test_dispose_is_idempotent_and_rejects_new_work(self):
        dispatcher, scheduler, _ = self.make()
        dispatcher.submit("one")
        dispatcher.dispose()
        dispatcher.dispose()
        self.assertEqual(scheduler.pending, {})
        with self.assertRaisesRegex(RuntimeError, "disposed"):
            dispatcher.submit("two")

    def test_invalid_dependencies_and_query_types_fail_closed(self):
        with self.assertRaises(ValueError):
            CoalescedQueryDispatcher(delay_ms=0, schedule=lambda *_: 1, cancel=lambda *_: None, deliver=lambda *_: None)
        dispatcher, _, _ = self.make()
        with self.assertRaises(TypeError):
            dispatcher.submit(None)


if __name__ == "__main__":
    unittest.main()
