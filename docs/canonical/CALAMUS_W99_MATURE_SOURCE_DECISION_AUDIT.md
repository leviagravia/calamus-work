# Calamus W99 — Mature-Source Decision Audit

## Evidence status

No raw mature-source archive is embedded in the W98 handover bundle used to
construct W99. W99 therefore does not claim a new extraction or fresh reading of
those trees. It reuses the already certified direct-source records preserved in
the canonical Calamus history, especially the W89 GTK boundary/lifecycle audit
and the W98 Research lifecycle decision audit. No web source was substituted.

The earlier certified audit recorded exact uploaded archives and hashes for Xed
3.8.9, Mousepad GTK3, gedit 3.5.1 and FeatherPad, and directly examined the
following source areas:

- Xed: `xed-app.c`, `xed-commands-file.c`, close-confirmation dialog and GUI tests;
- Mousepad: `mousepad-application.c`, `mousepad-window.c`, dialog helpers;
- gedit: `gedit-app.c`, file commands, session handling and close-confirmation dialog;
- GNOME Citations: application-owned lifecycle, semantic template children and
  explicit asynchronous cancellation;
- FeatherPad: differentiated interactive close and termination cleanup.

## Questions derived from the W98 Calamus audit

1. Who owns interactive close routing?
2. May a failed subsystem prevent unrelated cleanup?
3. Who terminates the raw GTK main loop?
4. Must delayed/asynchronous work have explicit cancellation?
5. Should W99 migrate the application framework or introduce a generic registry?

## ADOPT

- application-owned canonical close routing;
- save/discard/cancel before window destruction;
- explicit last-window/main-loop termination;
- named lifecycle owners and deterministic order;
- explicit cancellation of asynchronous work;
- isolated true-App identity and lifecycle processes;
- unconditional cleanup after true-App assertions.

## ADAPT

- Calamus remains a single-window raw `Gtk.main()` application, so W99 uses a
  deterministic `Gtk.main_level()`/`Gtk.main_quit()` bridge rather than copying
  `GtkApplication` window tracking;
- mature applications own shutdown at application level; Calamus implements the
  same principle with a small GTK-free coordinator plus boundary callbacks;
- subsystem-specific cleanup remains local, while registration and final
  attempt/report ownership become global.

## REJECT

- `Gtk.Application` migration inside W99;
- plugin registry or generic event bus;
- dynamic runtime discovery of owners;
- background supervisor/index/watchers;
- treating watchdog termination, skipped GTK tests or missing display as PASS;
- broad subsystem rewrites where existing boundaries are already correct.

## Binding conclusion

The mature-source evidence and the direct W98 Calamus audit converge on the same
minimal repair: one application close authority, explicit source cancellation,
fail-complete deterministic final shutdown and toolkit-free coordination. W99
implements only that repair.
