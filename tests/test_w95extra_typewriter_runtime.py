from __future__ import annotations

import unittest

from calamus_typewriter import TypewriterEventKind, TypewriterSettings
from calamus_typewriter_runtime import TypewriterRuntime


class Buffer:
    def __init__(self): self.selected=False
    def get_has_selection(self): return self.selected


class View:
    def __init__(self): self.buffer=Buffer(); self.focus=True
    def get_buffer(self): return self.buffer
    def has_focus(self): return self.focus


class Viewport:
    def __init__(self):
        self.external={}; self.geometry={}; self.next_id=1; self.pending=False
        self.calls=[]; self.runway_owner=None
    def connect_external_adjustment(self, cb): i=self.next_id; self.next_id+=1; self.external[i]=cb; return i
    def connect_geometry_changed(self, cb): i=self.next_id; self.next_id+=1; self.geometry[i]=cb; return i
    def disconnect_callback(self, i): self.external.pop(i,None); self.geometry.pop(i,None)
    def cancel_projection(self): self.pending=False; self.calls.append(("cancel",))
    def acquire_runway(self, owner, settings): self.runway_owner=owner; self.calls.append(("acquire", settings))
    def release_runway(self, owner):
        if self.runway_owner is owner: self.runway_owner=None
        self.calls.append(("release",))
    def queue_typewriter_to_insert(self, settings, *, reached=False, on_reached=None):
        self.pending=True; self.calls.append(("queue", reached));
        if on_reached: on_reached(True)
    @property
    def has_pending_projection(self): return self.pending
    def emit_external(self):
        for cb in tuple(self.external.values()): cb()
    def emit_geometry(self):
        for cb in tuple(self.geometry.values()): cb()


class W95ExtraTypewriterRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.states=[]; self.view=View(); self.viewport=Viewport()
        self.runtime=TypewriterRuntime(self.view, self.viewport, on_state_changed=self.states.append)

    def test_enable_acquires_runway_and_disable_restores(self):
        self.assertTrue(self.runtime.set_enabled(True))
        self.assertIs(self.viewport.runway_owner, self.runtime)
        self.assertEqual(self.states, [True])
        self.assertFalse(self.runtime.set_enabled(False))
        self.assertIsNone(self.viewport.runway_owner)
        self.assertEqual(self.states, [True, False])

    def test_pointer_and_selection_are_authoritative(self):
        self.runtime.set_enabled(True); self.viewport.calls.clear()
        self.runtime.on_button_press(); self.assertFalse(self.runtime.on_edit())
        self.runtime.on_button_release(); self.assertFalse(self.runtime.request(TypewriterEventKind.RESIZE))
        self.assertTrue(self.runtime.on_edit())
        self.viewport.calls.clear()
        self.view.buffer.selected=True
        self.runtime.on_keyboard()
        self.assertFalse(any(call[0] == "queue" for call in self.viewport.calls))

    def test_manual_scroll_suspends_until_semantic_keyboard_or_edit(self):
        self.runtime.set_enabled(True); self.viewport.pending=False; self.viewport.calls.clear()
        self.runtime.on_scroll(); self.assertTrue(self.runtime.manual_scroll_suspended)
        self.assertFalse(self.runtime.request(TypewriterEventKind.RESIZE))
        self.assertTrue(self.runtime.on_keyboard())
        self.assertFalse(self.runtime.manual_scroll_suspended)
        self.assertTrue(any(call[0] == "queue" for call in self.viewport.calls))

    def test_external_adjustment_is_manual_only_without_owned_semantic_work(self):
        self.runtime.set_enabled(True); self.viewport.pending=False
        self.viewport.emit_external(); self.assertTrue(self.runtime.manual_scroll_suspended)
        self.runtime.on_key_press(); self.viewport.emit_external()
        self.assertFalse(self.runtime.manual_scroll_suspended)
        self.runtime.on_key_release()

    def test_history_allows_exact_selection_restore(self):
        self.runtime.set_enabled(True); self.view.buffer.selected=True; self.viewport.calls.clear()
        self.assertTrue(self.runtime.on_history())
        self.assertTrue(any(call[0] == "queue" for call in self.viewport.calls))

    def test_resize_reprojects_only_after_target_has_been_reached(self):
        self.runtime.set_enabled(True); self.viewport.calls.clear(); self.runtime.reached=False
        self.viewport.emit_geometry()
        self.assertFalse(any(call[0] == "queue" for call in self.viewport.calls))
        self.runtime.reached=True; self.viewport.emit_geometry()
        self.assertTrue(any(call[0] == "queue" for call in self.viewport.calls))

    def test_focus_loss_suppresses_nonforced_projection(self):
        self.runtime.set_enabled(True); self.viewport.calls.clear(); self.view.focus=False
        self.assertFalse(self.runtime.on_edit())
        self.assertFalse(any(call[0] == "queue" for call in self.viewport.calls))

    def test_shutdown_disconnects_and_releases(self):
        self.runtime.set_enabled(True); self.runtime.shutdown()
        self.assertFalse(self.runtime.enabled)
        self.assertIsNone(self.viewport.runway_owner)
        self.assertEqual(self.viewport.external, {})
        self.assertEqual(self.viewport.geometry, {})


if __name__ == "__main__":
    unittest.main()
