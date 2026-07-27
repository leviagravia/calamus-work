# Calamus GTK Boundary and Compatibility Policy

Status: **ACTIVE / BINDING**
Effective from: W89 reconstruction after the protected rollback to published W88H.
Mature references: Xed 3.8.9, Mousepad GTK 3, gedit 3.5.1, Zim 0.76.3, GNOME Citations, with FeatherPad as toolkit-independent lifecycle evidence.

## 1. Purpose

GTK is an external, stateful boundary. GTK 3 and GTK 4 differ in namespaces,
signals, ownership, dialog and application lifecycle. PyGObject can select an
unintended typelib when a directly imported namespace is not versioned first.
Themes, compositors and window managers can expose different rendering,
shortcut and close behaviour. Calamus therefore treats GTK like the filesystem
or subprocess boundary: narrow, explicit, tested and reversible.

## 2. Supported runtime lane

- Python: **3.10 through 3.12** (`>=3.10,<3.13`)
- PyGObject: **3.42 through 3.50** (`>=3.42,<3.51`)
- GTK: **GTK 3.24**, micro version **30 or newer**, always `<4.0`
- Gtk typelib: **3.0**
- Gdk typelib: **3.0**
- Pango typelib: **1.0**
- PangoCairo typelib: **1.0**
- GTK 4: **not a supported runtime**

Every directly imported versioned GI namespace must be declared before import.
Declaring Gtk does not implicitly authorize an unversioned direct Gdk import.
GTK 3 and GTK 4 must never be probed in the same Python interpreter. Runtime
probing always runs in a fresh subprocess.

## 3. Architectural boundary

For every new work item:

- domain models, parsers, planners, stores and controllers remain GTK-free;
- GTK construction and signal wiring belong in `*_view.py`, `*_dialogs.py`,
  panel view modules or a thin `*_runtime.py` adapter;
- `App` remains composition and canonical application/window lifecycle wiring;
- no dialog becomes a data authority;
- controllers own validation, stale-token decisions and persistence;
- semantic widget names or explicit widget bundles are mandatory for true GTK tests;
- generic widget-tree position assumptions are forbidden;
- synchronous nested loops are permitted only through the single
  `calamus_modal_dialog.py` adapter;
- every real-GTK component workflow and every true-App workflow runs in a
  fresh subprocess with an isolated HOME/XDG environment and
  `G_DEBUG=fatal-criticals`;
- the complete pure/static regression runs without a display and must never be
  used as an accidental container for modal GTK workflows.

For W89, these modules must remain GTK-free:

- `calamus_related_references.py`
- `calamus_reference_sets.py`
- `calamus_reference_set_store.py`
- `calamus_reference_set_controller.py`
- `calamus_reference_integrity.py`
- `calamus_research_integrity_controller.py`
- `calamus_modal_dialog.py`

The modal adapter itself is GTK-free because it receives an already constructed
dialog. `ModalSession` owns the response boundary, hide-before-destroy ordering,
registered GLib source identifiers, deterministic cleanup and one testable closed
postcondition. Compatibility `run_modal()` / `destroy_modal()` facades remain for
historical W89 dialog code.

For W90, the same policy additionally requires these modules to remain GTK-free:

- `calamus_pandoc.py`
- `calamus_pandoc_process.py`
- `calamus_pandoc_controller.py`

`calamus_pandoc_dialogs.py` owns widgets and modal presentation.
`calamus_pandoc_runtime.py` is the thin GTK/thread adapter; it imports GTK lazily,
uses the canonical modal adapter and owns no export validation or persistence.
It exposes only typed semantic boundaries for options, destination, preview
acknowledgement, result presentation and operation execution. Production defaults
remain the real GTK adapters; integrated tests may replace those boundaries while
retaining the real App, controller, stores and external Pandoc child.
`PandocWorkflowOutcome` is the durable terminal state. Progress visibility is a
presentation detail and cannot be used as an operation-completion contract.
The external Pandoc child is part of the lifecycle boundary: accepted close must
cancel the exact child, join the worker and leave no surviving process.

## 4. Test tiers

### Layer 1 — focused GTK-free gate

- models, planners, stores, controllers, migration and real filesystem tests;
- no `gi` import through the tested domain path;
- no modal true-App test module;
- suitable for a headless builder.

### Layer 2 — dialog component gate

- real dialog construction in a fresh subprocess where a display is available;
- one builder or one modal workflow per named lane;
- semantic controls, explicit response and typed result;
- no recursive text scraping and no dependency on GTK child order;
- nested loop only through the canonical modal session owner;
- every registered GLib source is removed or proven naturally completed before
  the dialog is destroyed.

### Layer 3 — true-App/GTK E2E

- fresh subprocess for every separately named workflow;
- real display and real App wiring;
- bounded semantic modal driver plus external `timeout` watchdog;
- assertion failures preserved for the test thread;
- dialogs and windows cleaned in `finally`;
- `G_DEBUG=fatal-criticals` makes GTK/GLib criticals blockers.

### Layer 4 — lifecycle

The candidate must prove:

- X / `delete-event` close;
- File → Quit;
- `Ctrl+Q` canonical wiring;
- cancel of an unsaved close;
- accepted close destroys the window;
- destruction of the final window terminates `Gtk.main()`;
- no visible window and no surviving working-copy process after normal close;
- watchdog termination is reported as failure, never as a successful close.

## 5. Canonical lifecycle contract

Direct audit of Xed, Mousepad and gedit established the binding pattern:

1. `delete-event`, File → Quit and `Ctrl+Q` call one `request_application_close()` gateway;
2. the gateway asks the unsaved-document question once;
3. after acceptance it saves settings and destroys the window itself;
4. `delete-event` returns `TRUE`, preventing a second default close path;
5. the final window's `destroy` signal terminates the active `Gtk.main()` loop;
6. cancellation preserves the window and process;
7. re-entrant close requests are idempotent.

The current single-window launcher may use this deterministic transitional
Mousepad/gedit pattern. A future dedicated work item may migrate lifecycle
ownership to `Gtk.Application`, following Xed and GNOME Citations.

## 6. Modal-dialog contract

- historical W89 dialogs may use `run_modal()` / `destroy_modal()`;
- W90 dialogs and progress sessions use `ModalSession`;
- a modal session owns response, hide, registered source ids, loop return and
  destroy ordering; callers copy semantic results before context exit;
- component tests identify real controls by semantic names;
- complete `Gtk.Label` strings may be inspected, never character-by-character recursion;
- integrated true-App tests use typed semantic boundaries and terminal outcomes,
  not a polling driver over a chain of native dialogs;
- the complete native-dialog chain is manual desktop validation;
- one modal workflow per test method and one fresh subprocess per real-GTK lane;
- repeated `Gtk.ComboBoxText` mutation inside an idle callback while
  `Gtk.Dialog.run()` is active is forbidden;
- unexpected dialogs, callback tracebacks and timeouts fail immediately;
- a test timeout must not close a product dialog before its diagnostic state is
  asserted, because that would convert test-driver failure into product cancel;
- cleanup executes even after an assertion failure;
- modal E2E is never included in the focused or pure/static regression command.

## 7. Warning policy

Blocking:

- `Gtk-CRITICAL`, `Gdk-CRITICAL`, `GLib-CRITICAL`, `GLib-GObject-CRITICAL`;
- traceback or unhandled callback exception;
- unversioned direct GI namespace import;
- mixed GTK 3/GTK 4 probing;
- a new deprecation warning caused by changed paths;
- a new theme parse error caused by changed CSS;
- modal, main-loop or process timeout;
- a process surviving after a normal accepted close.

Known pre-existing debt, recorded separately and not expanded by W89 or W90:

- GTK CSS `:prelight` selectors;
- `Gtk.Widget.override_font` in the line-number boundary;
- historical opacity API deprecations.

W89 requires Gtk, Gdk, Pango and PangoCairo explicitly and promotes the old
shutdown-lifecycle debt to a blocking normal-close postcondition. W90 preserves
that gate and extends it to the tracked external Pandoc process and worker.

## 8. Desktop and rendering matrix

Before a stable release, evidence must cover at least:

- Linux Mint XFCE and a second session, normally Cinnamon;
- default/light and dark appearance modes;
- 1366×768 and 1920×1080-class resolutions;
- shortcuts, default buttons, focus, selection, scrolling, truncation and close behaviour.

A work-item candidate may be certified on the primary lane, but the record must
state which cells were tested. Theme-specific or window-manager-specific hacks
are forbidden.

## 9. Reproducibility and rollback

Every GTK-bearing candidate retains:

- published baseline hash;
- complete patch and source bundle;
- path hashes and executable modes;
- focused, full-suite, boundary, true-App and warning logs;
- Python/PyGObject/GTK/display evidence;
- protected rollback for a withdrawn dirty set.

Repeated modal or desktop failures require withdrawal, exact rollback, direct
mature-source audit and unitary reconstruction. Incremental repair after the
allowed failure cycle is forbidden.
