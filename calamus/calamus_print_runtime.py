"""GTK print adapter/runtime extracted from App by W107."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Pango, PangoCairo


class PrintRuntime:
    """Own GTK PrintOperation lifecycle and pagination for one editor window."""

    __slots__ = ("_parent", "_document_text", "_font", "_show_error", "_pages")

    def __init__(self, parent, *, document_text_provider, font_provider, show_error) -> None:
        if not callable(document_text_provider) or not callable(font_provider) or not callable(show_error):
            raise TypeError("print runtime providers must be callable")
        self._parent = parent
        self._document_text = document_text_provider
        self._font = font_provider
        self._show_error = show_error
        self._pages: list[str] = []

    @property
    def pages(self) -> tuple[str, ...]:
        return tuple(self._pages)

    def _run(self, action) -> None:
        operation = Gtk.PrintOperation()
        operation.set_job_name("Calamus")
        operation.connect("begin-print", self.on_begin_print)
        operation.connect("draw-page", self.on_draw_page)
        try:
            operation.run(action, self._parent)
        except Exception as error:
            self._show_error(str(error))

    def on_print_preview(self, *_):
        return self._run(Gtk.PrintOperationAction.PREVIEW)

    def on_print(self, *_):
        return self._run(Gtk.PrintOperationAction.PRINT_DIALOG)

    def on_begin_print(self, operation, context):
        text = self._document_text()
        lines = text.splitlines() or [""]
        lines_per_page = 54
        self._pages = [
            "\n".join(lines[index:index + lines_per_page])
            for index in range(0, len(lines), lines_per_page)
        ] or [""]
        operation.set_n_pages(len(self._pages))

    def on_draw_page(self, operation, context, page_nr):
        cr = context.get_cairo_context()
        layout = context.create_pango_layout()
        layout.set_text(self._pages[page_nr], -1)
        family, size = self._font()
        desc = Pango.FontDescription(f"{family} {size}")
        layout.set_font_description(desc)
        layout.set_width(int(context.get_width() * Pango.SCALE))
        cr.move_to(0, 0)
        PangoCairo.show_layout(cr, layout)
