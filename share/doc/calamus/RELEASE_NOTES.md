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

W95 candidate correction:
- Repaired the Research client selector so the GtkPopover child hierarchy is explicitly visible and allocated before popup mapping.
- Strengthened the True GTK gate to require mapped, realized, positively allocated popup/list/row widgets and a real selector-to-stack activation effect.
- Preserved the mature-source history, caret, selection and viewport correction unchanged.

W95extra mature-source rebuilt candidate:
- Adds a bounded top-level Writing menu with Typewriter Mode, Insert Date, Insert Time, and Insert Date and Time.
- Reintroduces Typewriter Mode through a new single-owner, geometry-driven viewport runtime; the historically retired implementation is not reused.
- Preserves exact W95 caret/selection History while delegating all vertical projection to one runtime.
- Uses a natural-start latch, measured 50% working line, dynamic view-only bottom runway, pointer/selection/manual-scroll suppression, and semantic resume.
- Adds a real GTK/App gate for menu activation, midpoint geometry, manual-scroll resume, disable restore, date/time commands, and Help navigation.
- Repairs the historical W95 Research-selector gate race by waiting for positive allocation rather than mapped state alone.
- Separates the technical System Info work-item token `W95EXTRA` from the descriptive label `Typewriter Mode + Writing menu`, preserving the stable W89 identity contract without hiding current-build information.
- No canonical commit or push is included; True GTK and desktop validation remain required.
W95extra Mature-Source Rebuilt R2: Bookmarks are under Navigate; date/time commands exist only under Writing; PDF cleanup remains under Revise. The real GTK Help gate now validates the semantic wording instead of one brittle substring.
