"""Application appearance CSS and the GTK CSS-provider boundary for Calamus."""
from __future__ import annotations

from typing import Any

from calamus_line_numbers import (
    apply_line_gutter_typography,
    measure_line_gutter_width,
)

from calamus_appearance_preferences import (
    APPEARANCE_DARK,
    APPEARANCE_LIGHT,
    APPEARANCE_MODES,
    APPEARANCE_SYSTEM,
)


LIGHT_EDITOR_BACKGROUND = "#ffffff"
DARK_EDITOR_BACKGROUND = "#1e1e1e"
EDITOR_SELECTION_BACKGROUND = "#2b62b8"
CURRENT_LINE_MIN_BACKGROUND_CONTRAST = 1.50


def _parse_hex_rgb(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        raise ValueError("RGB color must use #rrggbb form")
    try:
        return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError as exc:
        raise ValueError("RGB color must use #rrggbb form") from exc


def _rgb_hex(rgb: tuple[int, int, int]) -> str:
    if len(rgb) != 3 or any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 255 for v in rgb):
        raise ValueError("RGB components must be integers in 0..255")
    return "#%02x%02x%02x" % rgb


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for component in rgb:
        value = component / 255.0
        channels.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def background_contrast_ratio(first: str, second: str) -> float:
    """Return relative-luminance contrast between two background colors."""
    first_luminance = _relative_luminance(_parse_hex_rgb(first))
    second_luminance = _relative_luminance(_parse_hex_rgb(second))
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def _blend_rgb(base: tuple[int, int, int], accent: tuple[int, int, int], fraction: float) -> tuple[int, int, int]:
    return tuple(round(base[i] * (1.0 - fraction) + accent[i] * fraction) for i in range(3))


def semantic_current_line_background(
    base: str,
    accent: str,
    *,
    minimum_contrast: float = CURRENT_LINE_MIN_BACKGROUND_CONTRAST,
) -> str:
    """Derive a subordinate but perceptible row background from a palette.

    The current-line color is not selected by an arbitrary fixed literal. It is
    the first 1%-step blend from the editor base toward the active selection
    accent that reaches the requested background contrast. If a theme accent
    cannot reach that target, a neutral high-contrast pole is used as a
    deterministic fallback while preserving the same contrast target.
    """
    if isinstance(minimum_contrast, bool) or not isinstance(minimum_contrast, (int, float)):
        raise TypeError("minimum_contrast must be numeric")
    if minimum_contrast <= 1.0:
        raise ValueError("minimum_contrast must be greater than 1")
    base_rgb = _parse_hex_rgb(base)
    accent_rgb = _parse_hex_rgb(accent)

    def derive(toward: tuple[int, int, int]) -> str | None:
        for percent in range(1, 101):
            candidate = _rgb_hex(_blend_rgb(base_rgb, toward, percent / 100.0))
            if background_contrast_ratio(base, candidate) >= float(minimum_contrast):
                return candidate
        return None

    result = derive(accent_rgb)
    if result is not None:
        return result

    black = (0, 0, 0)
    white = (255, 255, 255)
    fallback = black if _relative_luminance(base_rgb) > 0.5 else white
    result = derive(fallback)
    if result is None:
        raise ValueError("cannot derive current-line background at requested contrast")
    return result


def current_line_background_for_appearance(
    appearance_mode: str,
    *,
    system_base: str | None = None,
    system_accent: str | None = None,
    system_prefers_dark: bool = False,
) -> str:
    """Resolve the semantic current-line row color for Light/Dark/System."""
    if appearance_mode == APPEARANCE_LIGHT:
        base = LIGHT_EDITOR_BACKGROUND
        accent = EDITOR_SELECTION_BACKGROUND
    elif appearance_mode == APPEARANCE_DARK:
        base = DARK_EDITOR_BACKGROUND
        accent = EDITOR_SELECTION_BACKGROUND
    elif appearance_mode == APPEARANCE_SYSTEM:
        base = system_base or (DARK_EDITOR_BACKGROUND if system_prefers_dark else LIGHT_EDITOR_BACKGROUND)
        accent = system_accent or EDITOR_SELECTION_BACKGROUND
    else:
        raise ValueError("appearance mode must be light, dark, or system")
    return semantic_current_line_background(base, accent)


def _rgba_to_hex(rgba: Any) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        round(max(0.0, min(1.0, float(rgba.red))) * 255),
        round(max(0.0, min(1.0, float(rgba.green))) * 255),
        round(max(0.0, min(1.0, float(rgba.blue))) * 255),
    )


def _lookup_theme_color(style_context: Any, name: str) -> str | None:
    try:
        found, rgba = style_context.lookup_color(name)
    except (AttributeError, TypeError, ValueError):
        return None
    return _rgba_to_hex(rgba) if found else None


def resolve_current_line_background_for_view(
    appearance_mode: str,
    text_view: Any,
    *,
    settings_api: Any,
) -> str:
    """Resolve the row background from explicit or active GTK presentation state."""
    if appearance_mode != APPEARANCE_SYSTEM:
        return current_line_background_for_appearance(appearance_mode)

    context = text_view.get_style_context()
    base = _lookup_theme_color(context, "theme_base_color")
    accent = _lookup_theme_color(context, "theme_selected_bg_color")
    settings = settings_api.get_default()
    prefer_dark = False
    if settings is not None:
        try:
            prefer_dark = bool(settings.get_property("gtk-application-prefer-dark-theme"))
        except (AttributeError, TypeError):
            pass
    return current_line_background_for_appearance(
        appearance_mode,
        system_base=base,
        system_accent=accent,
        system_prefers_dark=prefer_dark,
    )


def apply_current_line_tag_style(
    tag: Any,
    text_view: Any,
    appearance_mode: str,
    *,
    settings_api: Any,
) -> str:
    """Project semantic full-row current-line styling onto a GtkTextTag-like object."""
    background = resolve_current_line_background_for_view(
        appearance_mode,
        text_view,
        settings_api=settings_api,
    )
    # Paragraph background deliberately avoids competing with character-level
    # search backgrounds, spellcheck underline, and GTK-owned selection paint.
    tag.set_property("background-set", False)
    tag.set_property("paragraph-background", background)
    return background


def build_application_css(
    font_family: str,
    font_size: int,
    appearance_mode: str,
) -> str:
    """Build the current Calamus application CSS without touching GTK.

    Typography and palette rendering are kept outside the App monolith.  The
    palette mode is a canonical light/dark/system value; system delegates the
    palette to the desktop theme while retaining Calamus typography.
    """
    if not isinstance(font_family, str) or not font_family.strip():
        raise ValueError("font family must be a non-empty string")
    if isinstance(font_size, bool) or not isinstance(font_size, int):
        raise TypeError("font size must be an integer")
    if font_size <= 0:
        raise ValueError("font size must be positive")
    if not isinstance(appearance_mode, str) or appearance_mode not in APPEARANCE_MODES:
        raise ValueError("appearance mode must be light, dark, or system")
    # Pango family names are data, not CSS. Escape the two characters that can
    # terminate or alter a quoted CSS font-family value.
    font_family = font_family.strip().replace("\\", "\\\\").replace('"', '\\"')

    bg_css = ""
    if appearance_mode == APPEARANCE_LIGHT:
        bg_css = """
        /* White mode: keep editor and menus readable on dark GTK themes. */
        window, box, scrolledwindow, viewport, textview, textview text {
            background-color: #ffffff;
            color: #000000;
        }
        menubar, menubar > menuitem, menu, menuitem {
            background-color: #f5f5f5;
            color: #000000;
        }
        menubar > menuitem:hover, menubar > menuitem:prelight,
        menuitem:hover, menuitem:prelight {
            background-color: #dcdcdc;
            color: #000000;
        }
        menuitem label, menubar menuitem label, label {
            color: #000000;
        }
        #line-gutter {
            background-color: #f2f2f2;
            color: #555555;
            background-image: none;
            border: none;
            border-right: 1px solid #d7d7d7;
            box-shadow: none;
        }

        /* Dialogs and spellcheck controls: force a complete light palette so
           dark Mint themes cannot produce dark buttons with dark text. */
        dialog, messagedialog, dialog box, messagedialog box,
        notebook, notebook header, notebook stack, stack, frame,
        notebook > header, notebook > stack, notebook > frame,
        notebook tab, notebook tab label,
        #calamus-about-dialog, #calamus-about-dialog *,
        #calamus-about-notebook, #calamus-about-notebook *,
        #calamus-about-page, #calamus-about-page *,
        #calamus-license-view, #calamus-license-view text {
            background-color: #ffffff;
            color: #000000;
            background-image: none;
            text-shadow: none;
            box-shadow: none;
        }
        notebook tab {
            background-color: #e9e9e9;
            color: #000000;
            border-color: #b8b8b8;
            padding: 6px 10px;
        }
        notebook tab:checked, notebook tab:hover, notebook tab:prelight {
            background-color: #dcdcdc;
            color: #000000;
        }
        notebook tab label, notebook label,
        dialog label, messagedialog label,
        #calamus-about-dialog label {
            color: #000000;
            background-image: none;
            text-shadow: none;
        }
        button {
            color: #000000;
            background-color: #f7f7f7;
            background-image: none;
            border-color: #a8a8a8;
            text-shadow: none;
            box-shadow: none;
        }
        button:hover, button:prelight {
            color: #000000;
            background-color: #e9e9e9;
            background-image: none;
        }
        button:active, button:checked {
            color: #000000;
            background-color: #d8d8d8;
            background-image: none;
        }
        button, button *, button label,
        button:hover label, button:prelight label,
        button:active label, button:checked label {
            color: #000000;
            text-shadow: none;
            -gtk-icon-shadow: none;
        }
        entry {
            color: #000000;
            background-color: #ffffff;
            background-image: none;
            border-color: #9a9a9a;
            caret-color: #000000;
        }
        entry selection {
            color: #ffffff;
            background-color: #2b62b8;
        }
        list, listbox, row {
            color: #000000;
            background-color: #ffffff;
            background-image: none;
        }
        row label {
            color: #000000;
        }
        row:selected, row:selected label {
            color: #ffffff;
            background-color: #2b62b8;
            background-image: none;
        }
        #calamus-workspace-tree, #calamus-workspace-tree.view {
            color: #111111;
            background-color: #ffffff;
            background-image: none;
        }
        #calamus-workspace-tree:selected, #calamus-workspace-tree.view:selected {
            color: #ffffff;
            background-color: #2b62b8;
        }
        #calamus-workspace-root, #calamus-workspace-status, #calamus-workspace-hint {
            color: #111111;
        }
        scrolledwindow, viewport {
            background-color: #ffffff;
        }
        separator {
            background-color: #cfcfcf;
        }
        """
    elif appearance_mode == APPEARANCE_DARK:
        bg_css = """
        window, box, scrolledwindow, viewport, textview, textview text {
            background-color: #1e1e1e;
            color: #f5f5f5;
        }
        menubar, menubar > menuitem, menu, menuitem {
            background-color: #242424;
            color: #f5f5f5;
        }
        menubar > menuitem:hover, menubar > menuitem:prelight,
        menuitem:hover, menuitem:prelight {
            background-color: #3a3a3a;
            color: #ffffff;
        }
        menuitem label, menubar menuitem label, label {
            color: #f5f5f5;
        }
        #line-gutter {
            background-color: #252525;
            color: #bdbdbd;
            background-image: none;
            border: none;
            border-right: 1px solid #3b3b3b;
            box-shadow: none;
        }
        dialog, messagedialog, dialog box, messagedialog box,
        notebook, notebook header, notebook stack, stack, frame,
        notebook > header, notebook > stack, notebook > frame,
        notebook tab, notebook tab label,
        #calamus-about-dialog, #calamus-about-dialog *,
        #calamus-about-notebook, #calamus-about-notebook *,
        #calamus-about-page, #calamus-about-page *,
        #calamus-license-view, #calamus-license-view text {
            background-color: #1e1e1e;
            color: #f5f5f5;
            background-image: none;
            text-shadow: none;
            box-shadow: none;
        }
        notebook tab {
            background-color: #333333;
            color: #f5f5f5;
            border-color: #777777;
            padding: 6px 10px;
        }
        notebook tab:checked, notebook tab:hover, notebook tab:prelight {
            background-color: #444444;
            color: #ffffff;
        }
        notebook tab label, notebook label,
        dialog label, messagedialog label,
        #calamus-about-dialog label {
            color: #f5f5f5;
            background-image: none;
            text-shadow: none;
        }
        button {
            color: #f5f5f5;
            background-color: #333333;
            background-image: none;
            border-color: #777777;
            text-shadow: none;
            box-shadow: none;
        }
        button:hover, button:prelight {
            color: #ffffff;
            background-color: #444444;
            background-image: none;
        }
        button:active, button:checked {
            color: #ffffff;
            background-color: #555555;
            background-image: none;
        }
        button, button *, button label,
        button:hover label, button:prelight label,
        button:active label, button:checked label {
            color: #f5f5f5;
            text-shadow: none;
            -gtk-icon-shadow: none;
        }
        entry {
            color: #ffffff;
            background-color: #2a2a2a;
            background-image: none;
            border-color: #777777;
            caret-color: #ffffff;
        }
        entry selection, row:selected, row:selected label {
            color: #ffffff;
            background-color: #2b62b8;
            background-image: none;
        }
        list, listbox, row {
            color: #f5f5f5;
            background-color: #242424;
            background-image: none;
        }
        row label {
            color: #f5f5f5;
        }
        #calamus-workspace-tree, #calamus-workspace-tree.view {
            color: #f7f7f7;
            background-color: #242424;
            background-image: none;
        }
        #calamus-workspace-tree:selected, #calamus-workspace-tree.view:selected {
            color: #ffffff;
            background-color: #2b62b8;
        }
        #calamus-workspace-root, #calamus-workspace-status, #calamus-workspace-hint {
            color: #f7f7f7;
        }
        separator {
            background-color: #555555;
        }
        """
    css = f"""
    /* System-mode fallback: use GTK theme colors explicitly for the Workspace
       instead of inheriting disabled/insensitive colors from a surrounding
       chooser or generic tree rule. Explicit light/dark palettes below take
       precedence when Calamus owns the appearance mode. */
    #calamus-workspace-tree, #calamus-workspace-tree.view {{
        color: @theme_text_color;
        background-color: @theme_base_color;
        background-image: none;
    }}
    #calamus-workspace-tree:selected, #calamus-workspace-tree.view:selected {{
        color: @theme_selected_fg_color;
        background-color: @theme_selected_bg_color;
    }}
    #calamus-workspace-root, #calamus-workspace-status, #calamus-workspace-hint {{
        color: @theme_fg_color;
    }}

    /* The gutter is a viewport-sized drawing surface. Calamus owns one
       semantic divider; no second scroller, label or scrollbar exists. */
    #line-gutter {{
        border: none;
        border-radius: 0;
        border-right: 1px solid rgba(128, 128, 128, 0.35);
        background-image: none;
        box-shadow: none;
        padding: 0;
    }}
    textview,
    textview text {{
        font-family: "{font_family}";
        font-size: {font_size}pt;
    }}
    {bg_css}
    """
    return css



def install_application_css(
    provider: Any,
    screen: Any,
    css: str,
    *,
    style_context: Any,
    priority: int,
) -> None:
    """Install already-built CSS through an explicit GTK adapter."""
    if not isinstance(css, str):
        raise TypeError("css must be a string")
    provider.load_from_data(css.encode("utf-8"))
    style_context.add_provider_for_screen(screen, provider, priority)
