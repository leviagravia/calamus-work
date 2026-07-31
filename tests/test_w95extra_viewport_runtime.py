from __future__ import annotations

import unittest

from calamus_typewriter import TypewriterSettings
from calamus_viewport_runtime import EditorViewportRuntime


class Rect:
    def __init__(self, x=0, y=0, width=800, height=600):
        self.x, self.y, self.width, self.height = x, y, width, height


class Iter:
    def __init__(self, offset=0): self.offset = offset
    def get_offset(self): return self.offset


class Buffer:
    def __init__(self): self.offset = 0
    def get_insert(self): return object()
    def get_iter_at_mark(self, _mark): return Iter(self.offset)


class SignalObject:
    def __init__(self): self.handlers = {}; self.next_id = 1
    def connect(self, name, callback):
        ident = self.next_id; self.next_id += 1; self.handlers[ident] = (name, callback); return ident
    def disconnect(self, ident): self.handlers.pop(ident, None)
    def emit(self, name):
        for signal, callback in list(self.handlers.values()):
            if signal == name: callback(self)


class Adjustment(SignalObject):
    def __init__(self, *, value=0, lower=0, upper=3000, page_size=600):
        super().__init__(); self.value=value; self.lower=lower; self.upper=upper; self.page_size=page_size
    def get_value(self): return self.value
    def set_value(self, value): self.value=float(value); self.emit("value-changed")
    def get_lower(self): return self.lower
    def get_upper(self): return self.upper
    def get_page_size(self): return self.page_size


class TextView(SignalObject):
    def __init__(self, adjustment):
        super().__init__(); self.buffer=Buffer(); self.adjustment=adjustment
        self.caret=Rect(y=500, height=20); self.visible=Rect(y=200, height=600)
        self.top_margin=0; self.bottom_margin=12; self.resize_count=0
    def get_buffer(self): return self.buffer
    def get_iter_location(self, _iter): return self.caret
    def get_visible_rect(self): return self.visible
    def get_top_margin(self): return self.top_margin
    def get_bottom_margin(self): return self.bottom_margin
    def set_bottom_margin(self, value): self.bottom_margin=int(value)
    def queue_resize(self): self.resize_count += 1


class Scroller:
    def __init__(self, adjustment): self.adjustment=adjustment
    def get_vadjustment(self): return self.adjustment


class GLib:
    PRIORITY_LOW = 300
    def __init__(self): self.sources={}; self.next_id=1
    def idle_add(self, callback, **_kwargs):
        ident=self.next_id; self.next_id+=1; self.sources[ident]=callback; return ident
    def source_remove(self, ident): self.sources.pop(ident, None)
    def run_all(self):
        while self.sources:
            ident=sorted(self.sources)[0]; callback=self.sources.pop(ident); callback()


class W95ExtraViewportRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.errors=[]; self.glib=GLib(); self.adjustment=Adjustment()
        self.view=TextView(self.adjustment); self.scroller=Scroller(self.adjustment)
        self.runtime=EditorViewportRuntime(self.view, self.scroller, self.glib, lambda m,e:self.errors.append((m,e)))

    def tearDown(self): self.runtime.shutdown()

    def test_single_replaceable_request_owns_adjustment_write(self):
        self.view.caret.y=1200
        self.runtime.queue_visible_to_insert(0.15, center_if_outside=True)
        first=self.runtime.scroll_source
        self.runtime.queue_visible_to_insert(0.02, center_if_outside=False)
        self.assertNotEqual(first, self.runtime.scroll_source)
        self.glib.run_all()
        self.assertFalse(self.runtime.reveal_pending)
        self.assertGreater(self.adjustment.value, 0)
        self.assertEqual(self.errors, [])

    def test_geometry_not_ready_keeps_request_until_real_layout_signal(self):
        self.view.caret.y=1800; self.adjustment.upper=1000
        self.runtime.queue_visible_to_insert(0.15, center_if_outside=True)
        self.glib.run_all()
        self.assertTrue(self.runtime.reveal_pending)
        self.adjustment.upper=3000
        self.adjustment.emit("changed")
        self.glib.run_all()
        self.assertFalse(self.runtime.reveal_pending)

    def test_owned_adjustment_is_not_reported_as_manual_scroll(self):
        calls=[]; self.runtime.connect_external_adjustment(lambda: calls.append("external"))
        self.view.caret.y=1200
        self.runtime.queue_visible_to_insert(0.15, center_if_outside=True)
        self.glib.run_all()
        self.assertEqual(calls, [])
        self.adjustment.set_value(self.adjustment.value + 20)
        self.assertEqual(calls, ["external"])

    def test_runway_has_one_owner_and_restores_exact_margin(self):
        owner=object(); settings=TypewriterSettings()
        self.runtime.acquire_runway(owner, settings)
        self.assertEqual(self.view.bottom_margin, 342)
        with self.assertRaises(RuntimeError): self.runtime.acquire_runway(object(), settings)
        self.runtime.release_runway(owner)
        self.assertEqual(self.view.bottom_margin, 12)

    def test_typewriter_projection_uses_measured_caret_and_no_horizontal_authority(self):
        reached=[]; self.view.caret.y=800; self.view.visible.y=0
        self.runtime.queue_typewriter_to_insert(TypewriterSettings(), on_reached=reached.append)
        self.glib.run_all()
        self.assertEqual(self.adjustment.value, 510)
        self.assertEqual(reached, [True])
        self.assertFalse(hasattr(self.runtime, "_hadjustment"))


    def test_projection_request_does_not_create_a_self_induced_resize_loop(self):
        before = self.view.resize_count
        self.view.caret.y = 1200
        self.runtime.queue_typewriter_to_insert(TypewriterSettings(), reached=True)
        self.assertEqual(self.view.resize_count, before)
        self.glib.run_all()
        self.assertEqual(self.view.resize_count, before)

    def test_shutdown_disconnects_and_restores_runway(self):
        owner=object(); self.runtime.acquire_runway(owner, TypewriterSettings())
        self.runtime.shutdown()
        self.assertEqual(self.view.bottom_margin, 12)
        self.assertEqual(self.adjustment.handlers, {})
        self.assertEqual(self.view.handlers, {})


if __name__ == "__main__":
    unittest.main()
