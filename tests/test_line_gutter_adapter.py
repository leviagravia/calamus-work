import unittest

from calamus_line_numbers import LineGutterAdapter


class _Layout:
    def __init__(self, width, height=20):
        self.width = width
        self.height = height

    def get_pixel_size(self):
        return self.width, self.height


class _Container:
    def __init__(self):
        self.visible = None
        self.size = None
        self.resize_count = 0

    def set_visible(self, visible):
        self.visible = visible

    def set_size_request(self, width, height):
        self.size = (width, height)

    def queue_resize(self):
        self.resize_count += 1


class _Label:
    def __init__(self, widths=None):
        self.widths = widths or {"8": 8, "88": 20, "888": 33}
        self.visible = None
        self.text = None
        self.text_updates = 0
        self.size = None
        self.samples = []
        self.font = None
        self.resize_count = 0

    def set_visible(self, visible):
        self.visible = visible

    def set_text(self, text):
        self.text = text
        self.text_updates += 1

    def set_size_request(self, width, height):
        self.size = (width, height)

    def create_pango_layout(self, sample):
        self.samples.append(sample)
        return _Layout(self.widths[sample])

    def override_font(self, description):
        self.font = description

    def queue_resize(self):
        self.resize_count += 1


class _Pango:
    @staticmethod
    def FontDescription(value):
        return ("font", value)


class LineGutterAdapterTests(unittest.TestCase):
    def test_visible_render_owns_text_geometry_and_visibility(self):
        container = _Container()
        label = _Label({"888": 33})
        adapter = LineGutterAdapter(container, label, minimum_width=30)

        result = adapter.render(True, 725)

        self.assertTrue(result.visible)
        self.assertEqual(result.line_count, 725)
        self.assertTrue(result.text.startswith("1\n2\n3"))
        self.assertTrue(result.text.endswith("725"))
        self.assertEqual(result.width, 45)
        self.assertEqual(container.visible, True)
        self.assertEqual(label.visible, True)
        self.assertEqual(container.size, (45, 1))
        self.assertEqual(label.size, (40, 1))
        self.assertEqual(label.samples, ["888"])
        self.assertEqual(container.resize_count, 1)
        self.assertEqual(label.resize_count, 1)

    def test_hidden_render_hides_entire_container_and_clears_text(self):
        container = _Container()
        label = _Label()
        adapter = LineGutterAdapter(container, label, minimum_width=30)

        result = adapter.render(False, 9)

        self.assertFalse(result.visible)
        self.assertEqual(result.text, "")
        self.assertEqual(result.width, 0)
        self.assertEqual(container.visible, False)
        self.assertEqual(label.visible, False)
        self.assertEqual(label.text, "")
        self.assertEqual(label.samples, [])

    def test_empty_document_renders_line_one_at_minimum_width(self):
        container = _Container()
        label = _Label({"8": 7})
        adapter = LineGutterAdapter(container, label, minimum_width=30)
        result = adapter.render(True, 0)
        self.assertEqual(result.line_count, 1)
        self.assertEqual(result.text, "1")
        self.assertEqual(result.width, 30)

    def test_typography_uses_explicit_pango_boundary(self):
        container = _Container()
        label = _Label()
        adapter = LineGutterAdapter(container, label, minimum_width=30)
        description = adapter.apply_typography("Literata", 15, pango=_Pango)
        self.assertEqual(description, ("font", "Literata 15"))
        self.assertEqual(label.font, description)

    def test_same_line_count_does_not_rebuild_large_label_text(self):
        container = _Container()
        label = _Label({"888": 33})
        adapter = LineGutterAdapter(container, label, minimum_width=30)
        first = adapter.render(True, 725)
        second = adapter.render(True, 725)
        self.assertEqual(second, first)
        self.assertEqual(label.text_updates, 1)
        self.assertEqual(label.samples, ["888"])
        self.assertEqual(container.resize_count, 1)


    def test_force_render_reapplies_text_and_geometry_after_map(self):
        container = _Container()
        label = _Label({"888": 33})
        adapter = LineGutterAdapter(container, label, minimum_width=30)
        first = adapter.render(True, 725)
        second = adapter.render(True, 725, force=True)
        self.assertEqual(second, first)
        self.assertEqual(label.text_updates, 2)
        self.assertEqual(label.samples, ["888", "888"])
        self.assertEqual(container.resize_count, 2)

    def test_force_flag_must_be_boolean(self):
        adapter = LineGutterAdapter(_Container(), _Label(), minimum_width=30)
        with self.assertRaises(TypeError):
            adapter.render(True, 1, force=1)

    def test_typography_change_invalidates_cached_geometry(self):
        container = _Container()
        label = _Label({"88": 20})
        adapter = LineGutterAdapter(container, label, minimum_width=30)
        adapter.render(True, 99)
        adapter.apply_typography("Literata", 15, pango=_Pango)
        adapter.render(True, 99)
        self.assertEqual(label.samples, ["88", "88"])
        self.assertEqual(container.resize_count, 2)

    def test_hidden_render_still_validates_line_count(self):
        adapter = LineGutterAdapter(_Container(), _Label(), minimum_width=30)
        with self.assertRaises(TypeError):
            adapter.render(False, True)
        with self.assertRaises(ValueError):
            adapter.render(False, -1)

    def test_adapter_validates_widget_protocol_and_dimensions(self):
        with self.assertRaises(TypeError):
            LineGutterAdapter(object(), _Label(), minimum_width=30)
        with self.assertRaises(TypeError):
            LineGutterAdapter(_Container(), object(), minimum_width=30)
        with self.assertRaises(ValueError):
            LineGutterAdapter(_Container(), _Label(), minimum_width=0)
        with self.assertRaises(ValueError):
            LineGutterAdapter(_Container(), _Label(), minimum_width=30, horizontal_padding=-1)


if __name__ == "__main__":
    unittest.main()
