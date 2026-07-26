# W89 About/System Info Dialog Identity — Mature-Source Audit

Status: **BINDING**
Date: 2026-07-26
Baseline: `569dd742abd607bb55a1e6bf9efbad1fdba1684c`

## Trigger

The reconstructed W89 candidate passed the Research, lifecycle, namespace and
case-preservation gates, then failed before manual validation because the
identity E2E called an unimported `visible_dialogs()` helper.  The attempted
`dialogs[0]` lookup would have remained architecturally invalid even after an
import repair.  Running System Info also exposed deprecated positional
`Gtk.MessageDialog` construction.

## Direct source evidence

- **Xed 3.8.9:** About metadata is explicit; structured dialogs retain exact
  GtkBuilder widget pointers; GUI tests use exact accessible identity.
- **Mousepad GTK 3:** About and message dialogs have explicit transient/modal/
  destruction ownership.
- **gedit 3.5.1:** product identity is explicit About metadata.
- **Zim 0.76.3:** typed About class, expected-dialog test seam, exact class
  assertions and keyword `Gtk.MessageDialog` construction.
- **GNOME Citations:** product/release/development identity is separated and
  dialogs return typed results with explicit cancellation.
- **FeatherPad:** a concrete owned About object is configured and executed;
  global window discovery is unnecessary.

## ADOPT

- exact owned dialog objects;
- typed builder result for About and System Info;
- GTK-free identity snapshot and renderer;
- semantic widget names;
- independent identity and Research true-App lanes;
- zero new deprecation warnings in changed identity paths.

## ADAPT

- retain the custom Calamus About content while splitting build and present;
- retain synchronous GTK 3 only behind the modal adapter;
- use exact-title top-level lookup only as final external smoke evidence.

## REJECT

- importing the missing helper as the sole fix;
- `visible_dialogs()[0]` or any reliance on top-level ordering;
- positional `Gtk.MessageDialog` constructors;
- global label scraping for identity content;
- rebuilding from a dirty failed tree.

## DEFER

- conversion of every historical dialog;
- complete asynchronous-dialog architecture;
- `Gtk.Application` migration;
- broad historical GTK-free extraction until the Research Panel is complete.
