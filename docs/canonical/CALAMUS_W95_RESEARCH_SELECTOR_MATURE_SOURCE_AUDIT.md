# W95 Research Selector — Direct Mature-Source Audit and Repair Decision

## Scope

This audit addresses the remaining W95 desktop failure after the caret/history/viewport lane passed manual validation: the Research selector displayed only the dark GtkPopover arrow, while its client list was invisible and input appeared blocked.

The decision is based on direct source inspection of the uploaded archives and the exact Calamus R3 source. No web documentation or external repository substituted for source analysis.

## Calamus failure path

Read directly:

- `calamus/calamus_research_panel_view.py`
  - `ResearchClientSelector.__init__`
  - `ResearchClientSelector.append`
  - `ResearchClientSelector.popup`
  - `ResearchClientSelector._on_popover_show`
- `scripts/w95-true-gtk-app-gate.py`
  - `exercise_research_selector`

R3 created this hierarchy:

```text
Gtk.MenuButton
└── Gtk.Popover
    └── Gtk.ScrolledWindow
        └── Gtk.ListBox
            └── Gtk.ListBoxRow...
```

Rows were individually shown in `append()`, but the containing `Gtk.ScrolledWindow` and `Gtk.ListBox` were never explicitly shown. `GtkPopover.popup()` mapped the popover shell and arrow but did not override hidden descendant visibility. The previous gate checked model order, selected row and adjustment position; it did not require mapped/realized children, positive allocation, visible labels or an activation effect.

The user screenshot and diagnostic trace matched this architecture exactly: popover shell/arrow present, internal scroller/list absent.

## Xed — GTK3 primary precedent

Read directly:

- `xed/xed-window.c`, `create_statusbar()`
- `xed/resources/ui/xed-highlight-mode-selector.ui`
- `xed/xed-highlight-mode-selector.c`, `xed_highlight_mode_selector_init()`

Xed creates a `GtkPopover`, attaches a complex selector, and explicitly shows the attached selector. Its GTK3 UI template marks the selector, search entry, scrolled window and tree view `visible=True`. The key contract is not merely “child exists”; every widget in the popup hierarchy is visible before the menu button exposes the popover.

**ADOPT:** explicit descendant visibility before attachment/popup; desktop validation of the mapped selector, not only its data model.

## GtkSourceView — popover ownership precedent

Read directly:

- `gtksourceview/gtksourceassistant.c`, `_gtk_source_assistant_init()`
- `gtksourceview/gtksourceview-assistants.c`
- `gtksourceview/gtksourcecompletionlist.c`

GtkSourceView owns the popover child explicitly and presents the assistant only after child construction. It also separates the popover’s semantic placement from child rendering and geometry.

**ADAPT:** keep the existing Calamus MenuButton/Popover architecture, but make child visibility and useful allocation an invariant of the selector boundary.

## GNOME Text Editor — menu-button lifecycle precedent

Read directly:

- `src/editor-window.ui`
- `src/editor-window.c`
- `src/editor-window-actions.c`
- `src/editor-open-popover.c`

GNOME Text Editor treats menu-button popup/popdown as an explicit lifecycle and verifies behavior through the active menu surface, rather than assuming that a model-backed menu is usable merely because it was attached.

**ADAPT:** the Calamus gate must open through the actual `Gtk.MenuButton`, verify the visible hierarchy, activate a row, observe the Research stack change, and verify popdown.

## Repair

`ResearchClientSelector` now:

1. calls `self._scroll.show_all()` after constructing and attaching the child hierarchy;
2. calls `_ensure_popup_children_visible()` before every popup;
3. repeats that invariant in the popover `show` callback;
4. gives the scroller a minimum content width equal to the allocated selector width when available;
5. retains `Gtk.PositionType.BOTTOM`, first-row selection and top adjustment reset;
6. preserves active-row check visibility through `set_no_show_all(True)`.

No history, caret, clip expansion, editor viewport or command code is changed by this repair.

## Gate correction

The True GTK gate now requires:

- opening through `Gtk.MenuButton.set_active(True)`;
- popover, scrolled window and list box mapped and realized;
- positive width and height for popup, list, first row, target row and target label;
- row count equal to the Research client model;
- first row selected and vertical adjustment at the top;
- activation of a mapped second row through the production `row-activated` signal;
- exact selector active ID and Research runtime client change;
- popover unmapped after activation;
- restoration of Clip Collection before later W95 tests.

The previous marker is retained for continuity, but publication additionally requires:

`W95_TRUE_RESEARCH_SELECTOR_VISIBLE_ACTIVATION=PASS`

## Decision matrix

### ADOPT

- explicit visibility of every popup descendant;
- menu-button-driven opening;
- mapped/realized/allocation assertions;
- activation-effect and popdown assertions;
- one semantic selector boundary.

### REJECT

- treating `GtkPopover.popup()` as equivalent to showing hidden children;
- model-only selector gates;
- tests that pass when only the popover arrow is visible;
- returning to `Gtk.ComboBoxText`, whose active-row alignment caused the original upward occlusion problem;
- touching the now-validated caret/history/viewport lane.

## Future editor rewrite relevance

The selector audit reinforces a general Calamus UI rule for a future editor rewrite: a controller-level model contract is necessary but insufficient for GTK certification. Every transient surface—popover, completion list, snippet chooser, search result panel, command palette—needs a lifecycle contract covering construction, visibility, mapping, allocation, activation, focus/grab release and destruction. These checks belong to a real desktop gate and must remain separate from GTK-free model tests.
