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
)


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
            background-image: none;
            border: none;
            border-right: 1px solid #d7d7d7;
            box-shadow: none;
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
            background-image: none;
            border: none;
            border-right: 1px solid #3b3b3b;
            box-shadow: none;
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
    /* The gutter scroller must not inherit frame/scrollbar chrome from the
       desktop theme. Calamus owns one semantic divider and nothing else. */
    #line-gutter {{
        border: none;
        border-radius: 0;
        border-right: 1px solid rgba(128, 128, 128, 0.35);
        background-image: none;
        box-shadow: none;
        padding: 0;
    }}
    #line-numbers {{
        padding-left: 2px;
        padding-right: 3px;
    }}
    #line-gutter > border,
    #line-gutter scrollbar,
    #line-gutter scrollbar trough,
    #line-gutter scrollbar slider,
    #line-gutter overshoot,
    #line-gutter undershoot {{
        min-width: 0;
        min-height: 0;
        margin: 0;
        padding: 0;
        border: none;
        border-radius: 0;
        background-color: transparent;
        background-image: none;
        box-shadow: none;
        opacity: 0;
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
