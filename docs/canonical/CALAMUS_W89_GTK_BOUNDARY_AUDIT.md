# W89 GTK Boundary, Modal Test and Lifecycle Audit

Status: **COMPLETE**
Date: 2026-07-26
Baseline: `569dd742abd607bb55a1e6bf9efbad1fdba1684c`

## Trigger

Two withdrawn W89 candidates exposed two independent test-boundary defects:

1. a true-App modal test leaked into the focused gate and an assertion left a
   nested dialog loop alive until timeout;
2. the runtime gate imported Gdk without first requiring Gdk 3.0, allowing
   Gdk 4 to load before a later GTK 3 request.

The repository was rolled back exactly to the published W88H baseline and the
full baseline suite passed before this contract was re-frozen.

## Direct mature-source audit

### Xed 3.8.9 — primary reference

Files read included `xed-app.c`, `xed-commands-file.c`, the close-confirmation
dialog and GUI tests. Xed uses `GtkApplication`, routes `delete-event` through
the canonical quit command, returns `TRUE`, performs response-driven
save/discard/cancel, destroys windows only after document close completes and
shuts down after the application window list reaches zero.

### Mousepad GTK 3 — transitional reference

Files read included `mousepad-application.c`, `mousepad-window.c` and dialog
helpers. Mousepad confirms that X and menu close must invoke one action and that
last-window destruction must terminate a raw `gtk_main()` loop. Its hybrid
manual window list and broad synchronous-dialog style are not the final target.

### gedit 3.5.1 — historical lifecycle reference

Files read included `gedit-app.c`, file commands, session handling and the
close-confirmation dialog. gedit confirms application-owned window tracking,
an explicit last-window hook and response-driven close state machines.

### Zim 0.76.3 — dialog-test reference

Zim explicitly requires Gdk 3.0 and Gtk 3.0 before import. Its tests use an
ordered expected-dialog seam, semantic form controls, immediate failure for an
unexpected dialog and cleanup/restoration through a context boundary.

### GNOME Citations — GTK 4 architectural reference

Citations uses application-owned lifecycle, semantic template children,
explicit asynchronous results and unambiguous cancellation. Its GTK 4 APIs are
not copied into GTK 3, but the ownership principles are adopted.

### FeatherPad — toolkit-independent evidence

FeatherPad distinguishes interactive close from signal termination and performs
explicit cleanup in both paths. Qt implementation details are rejected.

## ADOPT

- version every directly imported GI namespace;
- one GTK generation per interpreter;
- fresh-process runtime probing;
- GTK-free model/store/controller tests;
- semantic controls and complete label strings;
- one canonical close gateway;
- final-window-to-main-loop termination;
- separate true-App and lifecycle processes;
- watchdog plus unconditional cleanup.

## ADAPT

- use the deterministic final-window `Gtk.main_quit()` bridge while Calamus
  remains a single-window raw-`Gtk.main()` application;
- keep synchronous GTK 3 dialogs only behind one controlled adapter;
- retain external GUI automation but strengthen it with exact state assertions.

## REJECT

- mixed GTK 3/GTK 4 probing;
- unversioned Gdk/Gtk/Pango/PangoCairo import;
- modal E2E in focused tests;
- recursive generic widget scanning or child-order assumptions;
- character-splitting rendered-text assertions;
- exceptions that leave a dialog alive;
- theme/window-manager-specific hacks;
- treating watchdog termination as PASS;
- another incremental repair of a withdrawn candidate.

## Final identity-dialog audit after the reconstructed candidate failed

The later About/System Info true-App lane failed because it called an unimported
helper and attempted to select `dialogs[0]` from the global top-level list.  The
same run exposed deprecated positional `Gtk.MessageDialog` construction.

Direct re-audit of Xed, Mousepad, gedit, Zim, GNOME Citations and FeatherPad
requires the following additional boundary:

- identity data and System Info rendering are GTK-free;
- About and System Info builders return exact typed widget bundles;
- presenters own run/destroy through the modal adapter;
- component tests call the exact builder;
- true-App identity smoke resolves exact titles and semantic widget names;
- identity smoke is a separate subprocess/lane from Research workflows;
- no changed identity path may emit `PyGTKDeprecationWarning`;
- `visible_dialogs()[0]`, top-level ordering and positional MessageDialog
  constructors are rejected.
