import unittest

from calamus_opacity import apply_widget_opacity


class _WidgetAPI:
    calls = []

    @staticmethod
    def set_opacity(widget, fraction):
        _WidgetAPI.calls.append((widget, fraction))


class _MissingAPI:
    pass


class OpacityAdapterTests(unittest.TestCase):
    def setUp(self):
        _WidgetAPI.calls = []

    def test_adapter_uses_explicit_widget_api_and_fraction(self):
        widget = object()
        apply_widget_opacity(widget, 88, widget_api=_WidgetAPI)
        self.assertEqual(_WidgetAPI.calls, [(widget, 0.88)])

    def test_adapter_rejects_invalid_percent_before_calling_gtk(self):
        with self.assertRaises(ValueError):
            apply_widget_opacity(object(), 101, widget_api=_WidgetAPI)
        self.assertEqual(_WidgetAPI.calls, [])

    def test_adapter_requires_set_opacity(self):
        with self.assertRaises(TypeError):
            apply_widget_opacity(object(), 88, widget_api=_MissingAPI)


if __name__ == "__main__":
    unittest.main()
