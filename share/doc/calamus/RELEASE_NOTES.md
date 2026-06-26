# Calamus 1.7.0-rc3-stable4.3

Targeted UI correction release for Calamus Standard Edition.

Fixed / hardened:
- Reduced the line-number gutter and made it dynamic by line-count digit width.
- Kept line numbers inside a contained scroller so line count cannot drive top-level window height.
- Reduced Clip Collection panel width to the button-row footprint.
- Prevented Clip Collection list content from expanding the panel horizontally or vertically.
- Stabilized the main geometry chain: GtkWindow -> root box -> Gtk.Paned -> contained editor scrollers -> direct-child Gtk.TextView.
- Replaced implicit Gtk.Paned add1/add2 child behavior with explicit pack1/pack2 resize/shrink policy.
- Applied minimum-only window geometry hints; no maximum-size hints or size-allocate resize clamps.
- Hardened Go to Line: clamp target line, place caret, focus editor, reveal line after GTK idle.
- Verified that execute_command calls finalize_command_edit only once per command mutation.

Validation:
- `PYTHONPATH=calamus python3 -m pytest -q`
- Result: 53 passed, 1 skipped.

Note:
- Manual GTK interaction tests still require a desktop environment with PyGObject installed.
- No tabs, split-view, workspace, command-palette, plugin, or Calamus Plus changes are included.
