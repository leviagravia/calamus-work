import unittest

from calamus_appearance import measure_line_gutter_width


class _Layout:
    def __init__(self, width, height=20):
        self.width = width
        self.height = height

    def get_pixel_size(self):
        return self.width, self.height


class _Label:
    def __init__(self, widths):
        self.widths = dict(widths)
        self.samples = []

    def create_pango_layout(self, sample):
        self.samples.append(sample)
        return _Layout(self.widths[sample])


class LineGutterTypographyTests(unittest.TestCase):
    def test_width_uses_effective_pango_metrics_and_digit_count(self):
        label = _Label({"888": 48})
        width = measure_line_gutter_width(
            label,
            725,
            minimum_width=30,
            horizontal_padding=12,
        )
        self.assertEqual(width, 60)
        self.assertEqual(label.samples, ["888"])

    def test_larger_font_metrics_expand_the_gutter(self):
        small = _Label({"88": 18})
        large = _Label({"88": 34})
        self.assertEqual(
            measure_line_gutter_width(small, 99, minimum_width=30),
            30,
        )
        self.assertEqual(
            measure_line_gutter_width(large, 99, minimum_width=30),
            46,
        )

    def test_empty_document_uses_one_digit_and_minimum_width(self):
        label = _Label({"8": 7})
        self.assertEqual(
            measure_line_gutter_width(label, 0, minimum_width=30),
            30,
        )
        self.assertEqual(label.samples, ["8"])

    def test_invalid_arguments_are_rejected(self):
        label = _Label({"8": 7})
        with self.assertRaises(TypeError):
            measure_line_gutter_width(label, True, minimum_width=30)
        with self.assertRaises(ValueError):
            measure_line_gutter_width(label, 1, minimum_width=0)
        with self.assertRaises(ValueError):
            measure_line_gutter_width(label, 1, minimum_width=30, horizontal_padding=-1)


if __name__ == "__main__":
    unittest.main()
