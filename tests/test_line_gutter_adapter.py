import unittest

from calamus_line_numbers import LineGutterAdapter


class _Layout:
    def __init__(self, widths, text=""):
        self.widths = widths
        self.text = text

    def set_text(self, text, _length):
        self.text = text

    def get_pixel_size(self):
        return self.widths.get(self.text, len(self.text) * 10), 20


class _Gutter:
    def __init__(self, widths=None):
        self.widths = widths or {}
        self.visible = None
        self.size = None
        self.font = None
        self.resize_count = 0
        self.draw_count = 0
        self.samples = []
        self.allocated_width = 50
        self.style_context = object()

    def set_visible(self, visible):
        self.visible = visible

    def set_size_request(self, width, height):
        self.size = (width, height)
        self.allocated_width = width

    def create_pango_layout(self, sample):
        self.samples.append(sample)
        return _Layout(self.widths, sample)

    def override_font(self, description):
        self.font = description

    def queue_resize(self):
        self.resize_count += 1

    def queue_draw(self):
        self.draw_count += 1

    def get_allocated_width(self):
        return self.allocated_width

    def get_style_context(self):
        return self.style_context


class _Buffer:
    def __init__(self, line_count):
        self.line_count = line_count

    def get_line_count(self):
        return self.line_count


class _Rect:
    def __init__(self, y, height):
        self.y = y
        self.height = height


class _Iter:
    def __init__(self, view, index):
        self.view = view
        self.index = index

    def get_line(self):
        return self.index

    def is_end(self):
        return self.index >= len(self.view.rows) - 1

    def forward_line(self):
        if self.index >= len(self.view.rows) - 1:
            return False
        self.index += 1
        return True


class _TextView:
    def __init__(self, rows=None, *, visible_y=0, visible_height=100, line_count=None):
        # Each row is one logical GtkTextBuffer line: (buffer y, rendered height).
        self.rows = rows or [(0, 20)]
        self.visible = _Rect(visible_y, visible_height)
        self.buffer = _Buffer(line_count if line_count is not None else len(self.rows))

    def get_buffer(self):
        return self.buffer

    def get_visible_rect(self):
        return self.visible

    def get_line_at_y(self, y):
        for index, (line_y, height) in enumerate(self.rows):
            if y < line_y + height:
                return _Iter(self, index), line_y
        index = len(self.rows) - 1
        return _Iter(self, index), self.rows[index][0]

    def get_line_yrange(self, iterator):
        return self.rows[iterator.index]


class _Pango:
    @staticmethod
    def FontDescription(value):
        return ("font", value)


class _Renderer:
    def __init__(self):
        self.calls = []

    def __call__(self, style_context, cairo_context, x, y, layout):
        self.calls.append((style_context, cairo_context, x, y, layout.text))


class LineGutterAdapterTests(unittest.TestCase):
    def make_adapter(self, *, rows=None, visible_y=0, visible_height=100, line_count=None, widths=None):
        gutter = _Gutter(widths)
        view = _TextView(
            rows,
            visible_y=visible_y,
            visible_height=visible_height,
            line_count=line_count,
        )
        renderer = _Renderer()
        adapter = LineGutterAdapter(
            gutter,
            view,
            minimum_width=30,
            render_layout=renderer,
        )
        return adapter, gutter, view, renderer

    def test_visible_render_owns_width_visibility_and_draw_invalidation(self):
        adapter, gutter, _view, _renderer = self.make_adapter(
            line_count=725,
            widths={"888": 33},
        )

        result = adapter.render(True)

        self.assertTrue(result.visible)
        self.assertEqual(result.line_count, 725)
        self.assertEqual(result.text, "")
        self.assertEqual(result.width, 45)
        self.assertTrue(gutter.visible)
        self.assertEqual(gutter.size, (45, 1))
        self.assertEqual(gutter.samples, ["888"])
        self.assertEqual(gutter.resize_count, 1)
        self.assertEqual(gutter.draw_count, 1)

    def test_hidden_render_hides_entire_drawing_gutter(self):
        adapter, gutter, _view, _renderer = self.make_adapter(line_count=9)

        result = adapter.render(False)

        self.assertFalse(result.visible)
        self.assertEqual(result.text, "")
        self.assertEqual(result.width, 0)
        self.assertFalse(gutter.visible)
        self.assertEqual(gutter.samples, [])
        self.assertEqual(gutter.draw_count, 1)

    def test_current_line_count_comes_from_text_buffer(self):
        adapter, _gutter, view, _renderer = self.make_adapter(line_count=937)
        self.assertEqual(adapter.current_line_count(), 937)
        view.buffer.line_count = 0
        self.assertEqual(adapter.current_line_count(), 1)

    def test_visible_rows_use_textview_lines_and_wrapped_line_heights(self):
        # Logical line 1 wraps to 40px. It still receives one number only.
        adapter, _gutter, _view, _renderer = self.make_adapter(
            rows=[(0, 40), (40, 20), (60, 20), (80, 20)],
            visible_y=10,
            visible_height=70,
        )
        adapter.render(True)

        self.assertEqual(
            adapter.visible_line_rows(),
            ((1, -10), (2, 30), (3, 50)),
        )

    def test_draw_uses_authoritative_line_numbers_and_textview_y_positions(self):
        adapter, gutter, _view, renderer = self.make_adapter(
            rows=[(100, 20), (120, 20), (140, 20)],
            visible_y=110,
            visible_height=50,
            widths={"1": 8, "2": 8, "3": 8, "888": 24},
        )
        adapter.render(True, 3)
        cairo = object()

        self.assertFalse(adapter.draw(gutter, cairo))

        self.assertEqual([call[4] for call in renderer.calls], ["1", "2", "3"])
        self.assertEqual([call[3] for call in renderer.calls], [-10, 10, 30])
        self.assertTrue(all(call[0] is gutter.style_context for call in renderer.calls))
        self.assertTrue(all(call[1] is cairo for call in renderer.calls))
        self.assertTrue(all(call[2] >= 0 for call in renderer.calls))

    def test_draw_is_noop_when_hidden(self):
        adapter, gutter, _view, renderer = self.make_adapter()
        adapter.render(False)
        self.assertFalse(adapter.draw(gutter, object()))
        self.assertEqual(renderer.calls, [])

    def test_typography_uses_explicit_pango_boundary(self):
        adapter, gutter, _view, _renderer = self.make_adapter()
        description = adapter.apply_typography("Literata", 15, pango=_Pango)
        self.assertEqual(description, ("font", "Literata 15"))
        self.assertEqual(gutter.font, description)
        self.assertGreaterEqual(gutter.draw_count, 1)

    def test_same_line_count_reuses_geometry_but_repaints_viewport(self):
        adapter, gutter, _view, _renderer = self.make_adapter(
            line_count=725,
            widths={"888": 33},
        )
        first = adapter.render(True)
        second = adapter.render(True)
        self.assertEqual(second, first)
        self.assertEqual(gutter.samples, ["888"])
        self.assertEqual(gutter.resize_count, 1)
        self.assertEqual(gutter.draw_count, 2)

    def test_force_render_remeasures_after_map(self):
        adapter, gutter, _view, _renderer = self.make_adapter(
            line_count=725,
            widths={"888": 33},
        )
        first = adapter.render(True)
        second = adapter.render(True, force=True)
        self.assertEqual(second, first)
        self.assertEqual(gutter.samples, ["888", "888"])
        self.assertEqual(gutter.resize_count, 2)

    def test_typography_change_invalidates_cached_geometry(self):
        adapter, gutter, _view, _renderer = self.make_adapter(
            line_count=99,
            widths={"88": 20},
        )
        adapter.render(True)
        adapter.apply_typography("Literata", 15, pango=_Pango)
        adapter.render(True)
        self.assertEqual(gutter.samples, ["88", "88"])
        self.assertEqual(gutter.resize_count, 3)  # font queue + two measurements

    def test_invalid_arguments_and_protocols_are_rejected(self):
        adapter, _gutter, _view, _renderer = self.make_adapter()
        with self.assertRaises(TypeError):
            adapter.render(True, 1, force=1)
        with self.assertRaises(TypeError):
            adapter.render(False, True)
        with self.assertRaises(ValueError):
            adapter.render(False, -1)
        with self.assertRaises(TypeError):
            LineGutterAdapter(object(), _TextView(), minimum_width=30, render_layout=lambda *_: None)
        with self.assertRaises(TypeError):
            LineGutterAdapter(_Gutter(), object(), minimum_width=30, render_layout=lambda *_: None)
        with self.assertRaises(ValueError):
            LineGutterAdapter(_Gutter(), _TextView(), minimum_width=0, render_layout=lambda *_: None)
        with self.assertRaises(TypeError):
            LineGutterAdapter(_Gutter(), _TextView(), minimum_width=30, render_layout=object())


if __name__ == "__main__":
    unittest.main()
