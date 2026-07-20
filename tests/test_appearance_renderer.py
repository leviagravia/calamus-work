import unittest

from calamus_appearance_preferences import APPEARANCE_DARK, APPEARANCE_LIGHT, APPEARANCE_SYSTEM
from calamus_appearance import (
    apply_line_gutter_typography,
    build_application_css,
    install_application_css,
)


class _Provider:
    def __init__(self):
        self.data = None

    def load_from_data(self, data):
        self.data = data


class _StyleContext:
    calls = []

    @classmethod
    def add_provider_for_screen(cls, screen, provider, priority):
        cls.calls.append((screen, provider, priority))


class AppearanceRendererTests(unittest.TestCase):
    def setUp(self):
        _StyleContext.calls = []

    def test_css_contains_font_and_white_palette(self):
        css = build_application_css("Literata", 17, APPEARANCE_LIGHT)
        self.assertIn('font-family: "Literata"', css)
        self.assertIn("font-size: 17pt", css)
        self.assertIn("background-color: #ffffff", css)
        self.assertIn("textview,\n    textview text", css)
        self.assertNotIn("textview text,\n    #line-numbers", css)
        self.assertEqual(css.count('font-family: "Literata"'), 1)
        self.assertEqual(css.count("font-size: 17pt"), 1)

    def test_editor_css_and_custom_gutter_typography_are_separate_boundaries(self):
        css = build_application_css("Serif", 18, APPEARANCE_SYSTEM)
        selector = "textview,\n    textview text"
        self.assertIn(selector, css)
        self.assertNotIn("#line-numbers {\n        font-family", css)
        self.assertIn('font-family: "Serif";', css)
        self.assertIn("font-size: 18pt;", css)

    def test_css_contains_dark_palette(self):
        css = build_application_css("Monospace", 12, APPEARANCE_DARK)
        self.assertIn("background-color: #1e1e1e", css)
        self.assertIn("color: #f5f5f5", css)

    def test_gutter_css_resets_theme_frame_and_shadow_chrome(self):
        css = build_application_css("Monospace", 12, APPEARANCE_SYSTEM)
        self.assertIn("#line-gutter {", css)
        self.assertIn("border: none;", css)
        self.assertIn("border-radius: 0;", css)
        self.assertIn("background-image: none;", css)
        self.assertIn("box-shadow: none;", css)
        self.assertIn("border-right: 1px solid rgba(128, 128, 128, 0.35);", css)

    def test_line_number_spacing_is_painted_padding_not_transparent_margin(self):
        css = build_application_css("Monospace", 12, APPEARANCE_LIGHT)
        self.assertIn("#line-numbers {", css)
        self.assertIn("padding-left: 2px;", css)
        self.assertIn("padding-right: 3px;", css)

    def test_gutter_css_neutralizes_internal_scrollbar_nodes(self):
        css = build_application_css("Monospace", 12, APPEARANCE_LIGHT)
        for selector in (
            "#line-gutter > border",
            "#line-gutter scrollbar",
            "#line-gutter scrollbar trough",
            "#line-gutter scrollbar slider",
            "#line-gutter overshoot",
            "#line-gutter undershoot",
        ):
            self.assertIn(selector, css)
        self.assertIn("opacity: 0;", css)
        self.assertIn("min-width: 0;", css)
        self.assertIn("background-color: transparent;", css)

    def test_light_and_dark_palettes_reassert_only_semantic_divider(self):
        light = build_application_css("Monospace", 12, APPEARANCE_LIGHT)
        dark = build_application_css("Monospace", 12, APPEARANCE_DARK)
        self.assertIn("border-right: 1px solid #d7d7d7;", light)
        self.assertIn("border-right: 1px solid #3b3b3b;", dark)
        self.assertGreaterEqual(light.count("border: none;"), 2)
        self.assertGreaterEqual(dark.count("border: none;"), 2)

    def test_neutral_palette_does_not_force_application_background(self):
        css = build_application_css("Monospace", 12, APPEARANCE_SYSTEM)
        self.assertIn('font-family: "Monospace"', css)
        self.assertNotIn("White mode", css)
        self.assertNotIn("background-color: #1e1e1e", css)

    def test_font_family_is_escaped_as_css_data(self):
        css = build_application_css('Family "Quoted" \\ Name', 12, APPEARANCE_SYSTEM)
        self.assertIn('font-family: "Family \\"Quoted\\" \\\\ Name"', css)

    def test_renderer_rejects_invalid_font_inputs(self):
        with self.assertRaises(ValueError):
            build_application_css("", 12, APPEARANCE_LIGHT)
        with self.assertRaises(TypeError):
            build_application_css("Monospace", True, APPEARANCE_LIGHT)
        with self.assertRaises(ValueError):
            build_application_css("Monospace", 12, "sepia")

    def test_installer_is_explicit_gtk_boundary(self):
        provider = _Provider()
        screen = object()
        install_application_css(
            provider,
            screen,
            "textview { font-size: 12pt; }",
            style_context=_StyleContext,
            priority=600,
        )
        self.assertEqual(provider.data, b"textview { font-size: 12pt; }")
        self.assertEqual(_StyleContext.calls, [(screen, provider, 600)])


class _FontDescription:
    def __init__(self, value):
        self.value = value


class _Pango:
    FontDescription = _FontDescription


class _LineNumbers:
    def __init__(self):
        self.description = None
        self.resize_calls = 0

    def override_font(self, description):
        self.description = description

    def queue_resize(self):
        self.resize_calls += 1


class LineGutterFontAdapterTests(unittest.TestCase):
    def test_custom_label_receives_exact_editor_font_description(self):
        label = _LineNumbers()
        description = apply_line_gutter_typography(
            label,
            "Serif",
            18,
            pango=_Pango,
        )
        self.assertIs(description, label.description)
        self.assertEqual(description.value, "Serif 18")
        self.assertEqual(label.resize_calls, 1)

    def test_adapter_strips_family_and_rejects_invalid_inputs(self):
        label = _LineNumbers()
        description = apply_line_gutter_typography(
            label,
            "  Literata  ",
            15,
            pango=_Pango,
        )
        self.assertEqual(description.value, "Literata 15")
        with self.assertRaises(ValueError):
            apply_line_gutter_typography(label, "", 15, pango=_Pango)
        with self.assertRaises(TypeError):
            apply_line_gutter_typography(label, "Serif", True, pango=_Pango)
        with self.assertRaises(ValueError):
            apply_line_gutter_typography(label, "Serif", 0, pango=_Pango)


if __name__ == "__main__":
    unittest.main()
