# W98 — mature-source decision audit

Prior direct source audits of Xed, gedit, Mousepad, Zim, Gnote, NoteKit, ghostwriter and IWE were re-evaluated for W98. The binding lessons are: application-owned close routing, explicit client activation/deactivation, semantic identity owned outside rows, deterministic navigation, explicit invalidation and cleanup in isolated true-App processes.

ADOPT: one lifecycle owner, stable client IDs, response-driven close and explicit cleanup. ADAPT: a small fixed coordinator around Calamus's seven existing clients, with active refresh and hidden dirty state. REJECT: plugin registry, generic event bus, watcher, database/cache authority, background index, eager refresh of every client on every keystroke and `Gtk.Application` migration inside W98.
