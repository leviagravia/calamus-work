# W107 Mature Source Comparison

All comparisons are direct source-code comparisons from archives supplied by
the user.

## gedit — `gedit-window-private.h`, `gedit-window.c`

gedit's window private structure owns explicit settings/action/panel objects,
and window functions operate on those concrete owners.

ADAPT:
- explicit component ownership;
- dedicated panel/settings/action collaborators;
- lifecycle ownership close to the concrete object.

REJECT:
- large window-private bag as W107 endpoint;
- plugin extension/message-bus complexity.

Calamus should take the explicit-owner principle but continue further toward
narrow subsystem ports.

## Pluma — `pluma-window-private.h`, `pluma-window.c`

Pluma mirrors the older gedit architecture: concrete editor/pane/action objects
are explicit, but much behavior remains window-centric.

ADAPT:
- stable object ownership and lifecycle.

REJECT:
- reproducing a broad window-private god object.

## GNOME Text Editor — `editor-window.c`, `editor-page.c`,
`editor-page-gsettings.c`

GNOME Text Editor separates application, window, page, document and settings
provider responsibilities. `EditorPage` receives an `EditorDocument`; page
settings are supplied through a settings abstraction. Window actions update
against the active page rather than handing the entire application to page
logic.

STRONGLY ADAPT:
- explicit document/page/settings dependencies;
- action logic targets the smallest meaningful owner;
- subsystem objects do not receive a generic application context.

Do not copy GTK4 APIs directly; Calamus remains GTK3 and keeps core ports GTK-free.

## NotepadNext — `NotepadNextApplication.h`, `MainWindow.cpp`,
`RecentFilesListManager.cpp`

Positive:
- application exposes explicit `ApplicationSettings` and
  `RecentFilesListManager`;
- recent files have a dedicated manager.

Negative:
- `MainWindow` keeps an application pointer and performs very broad orchestration.

ADAPT the explicit managers.
REJECT passing the whole app/window into Calamus subsystem controllers.

## Geany — `geanyobject.c`, `main.h`

Geany exposes a broad signal/event surface, especially for plugins.

REJECT for W107:
- global event bus;
- application-wide service access;
- plugin-driven generic context.

Calamus's roadmap explicitly forbids solving host-port migration with a generic
event bus/service locator.

## Airpad — `options.c`, main/window wiring

Airpad is intentionally simple but strongly window/callback-centric.

NEGATIVE precedent:
useful as proof that small code can still retain architectural coupling.
W107 should not merely move callbacks into another large file.

## Convergent rule

The mature-source direction useful to Calamus is:

1. own concrete collaborators explicitly;
2. pass document/settings/manager dependencies at the narrowest scope;
3. keep window/application objects as composition/lifecycle owners;
4. do not use a whole-app argument as a subsystem service registry;
5. do not replace direct coupling with a global event bus.

## Post-R2 FAIL 2/2 — construction ownership comparison

The second desktop failure required a narrower comparison of construction and
ownership, not another feature-oriented pass.

### GNOME Text Editor

`editor_page_new_for_document()` constructs `EditorPage` with the concrete
`EditorDocument` dependency through the `document` property.  Page settings are
then derived/bound from that document.  The page does not receive a higher-level
window/application ownership aggregate.

**ADAPT:** give WorkspaceHostRuntime the concrete Workspace collaborators it
uses.

### NotepadNext

`MainWindow` obtains the concrete `RecentFilesListManager`; the recent-file menu
builder is constructed with that manager directly.  Although MainWindow itself
is broad and therefore not a Calamus endpoint, this ownership edge is explicit
and does not require an aggregate record containing both manager and consumer.

**ADAPT:** direct collaborator ownership.
**REJECT:** whole-window/application reach-through.

### gedit / Pluma

Their window-private structures make concrete collaborators explicit.  They are
a negative precedent for one broad bag, but a positive precedent for stable
concrete owner identity.

**ADAPT:** stable concrete collaborator references.
**REJECT:** an aggregate back-reference from a runtime to the record that also
owns that runtime.

### W107 post-failure matrix delta

- **ADOPT:** W101 named SetOnceReference for the bounded Workspace callback cycle.
- **ADAPT:** GNOME Text Editor / NotepadNext direct concrete dependency edges.
- **REJECT:** WorkspaceHostRuntime -> WorkspaceComponents aggregate back-reference.
- **REJECT:** solving immutable-record identity drift by weakening the true-App assertion.
- **DEFER:** Research bundle simplification; its bundle is not replaced after
  binding and no current failing invariant demonstrates the Workspace defect
  there.  Do not expand the post-FAIL2 repair beyond the proven boundary.
