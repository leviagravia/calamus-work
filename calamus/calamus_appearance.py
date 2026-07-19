"""Application appearance CSS and the GTK CSS-provider boundary for Calamus."""
from __future__ import annotations

from typing import Any


def build_application_css(
    font_family: str,
    font_size: int,
    white_background: bool,
    dark_mode: bool,
) -> str:
    """Build the current Calamus application CSS without touching GTK.

    Typography and palette rendering are kept outside the App monolith.  The
    white/dark booleans remain backward compatible with the current settings
    format; when both are false the desktop theme supplies the palette.
    """
    if not isinstance(font_family, str) or not font_family.strip():
        raise ValueError("font family must be a non-empty string")
    if isinstance(font_size, bool) or not isinstance(font_size, int):
        raise TypeError("font size must be an integer")
    if font_size <= 0:
        raise ValueError("font size must be positive")
    if not isinstance(white_background, bool) or not isinstance(dark_mode, bool):
        raise TypeError("appearance mode flags must be booleans")
    # Pango family names are data, not CSS. Escape the two characters that can
    # terminate or alter a quoted CSS font-family value.
    font_family = font_family.strip().replace("\\", "\\\\").replace('"', '\\"')

    bg_css = ""
    if white_background:
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
        #line-numbers {
            background-color: #f2f2f2;
            color: #555555;
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
        scrolledwindow, viewport {
            background-color: #ffffff;
        }
        separator {
            background-color: #cfcfcf;
        }
        """
    elif dark_mode:
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
        #line-numbers {
            background-color: #252525;
            color: #bdbdbd;
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
        separator {
            background-color: #555555;
        }
        """
    css = f"""
    textview,
    textview text {{
        font-family: "{font_family}";
        font-size: {font_size}pt;
    }}
    {bg_css}
    """
    return css



def apply_line_gutter_typography(
    line_numbers: Any,
    font_family: str,
    font_size: int,
    *,
    pango: Any,
) -> Any:
    """Apply the editor font explicitly to Calamus' custom Gtk.Label gutter.

    GtkSourceView-based editors inherit gutter typography inside one editor
    widget. Calamus uses a separate Gtk.Label, so a screen-level CSS selector
    is not a reliable authority for its Pango layout. The gutter therefore
    receives the same concrete Pango.FontDescription as the editor preference.
    """
    if not isinstance(font_family, str) or not font_family.strip():
        raise ValueError("font family must be a non-empty string")
    if isinstance(font_size, bool) or not isinstance(font_size, int):
        raise TypeError("font size must be an integer")
    if font_size <= 0:
        raise ValueError("font size must be positive")
    if not hasattr(line_numbers, "override_font"):
        raise TypeError("line number widget must support override_font")
    if not hasattr(pango, "FontDescription"):
        raise TypeError("pango boundary must provide FontDescription")

    description = pango.FontDescription(f"{font_family.strip()} {font_size}")
    line_numbers.override_font(description)
    if hasattr(line_numbers, "queue_resize"):
        line_numbers.queue_resize()
    return description

def measure_line_gutter_width(
    line_numbers: Any,
    line_count: int,
    *,
    minimum_width: int,
    horizontal_padding: int = 12,
) -> int:
    """Measure gutter geometry from the widget's effective editor font.

    The line-number label receives the same CSS typography as the TextView.
    Its width must therefore come from a Pango layout created by that widget,
    not from a fixed pixels-per-digit approximation that becomes stale after
    a font change.
    """
    if isinstance(line_count, bool) or not isinstance(line_count, int):
        raise TypeError("line_count must be an integer")
    if isinstance(minimum_width, bool) or not isinstance(minimum_width, int):
        raise TypeError("minimum_width must be an integer")
    if isinstance(horizontal_padding, bool) or not isinstance(horizontal_padding, int):
        raise TypeError("horizontal_padding must be an integer")
    if minimum_width <= 0:
        raise ValueError("minimum_width must be positive")
    if horizontal_padding < 0:
        raise ValueError("horizontal_padding cannot be negative")

    digits = max(1, len(str(max(1, line_count))))
    layout = line_numbers.create_pango_layout("8" * digits)
    text_width, _text_height = layout.get_pixel_size()
    return max(minimum_width, int(text_width) + horizontal_padding)


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
