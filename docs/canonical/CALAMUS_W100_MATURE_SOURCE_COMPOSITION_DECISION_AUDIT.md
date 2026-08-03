# Calamus W100 — Mature-source composition decision audit

## Evidence status

W100 does not claim a fresh extraction of mature-source archives from the W99
handover, because those archives are not embedded there. It re-evaluates the
previously certified direct-source audit of the uploaded corpus, whose report
records the exact files read. This is source-derived evidence, not web research.

## Directly audited precedents and decisions

### Xed
Files: `xed/xed-app.c`, `xed/xed-window.c`, `xed/xed-document.c`.

- **ADOPT:** application-level concrete window creation and explicit window/document disposal.
- **ADAPT:** Calamus remains single-window; use one typed composer rather than Xed's broader application/plugin machinery.
- **REJECT:** plugin engine and extension-set access as composition infrastructure.

### gedit
Files: `gedit/gedit-app.c`, `gedit/gedit-window.c`, `gedit/gedit-document.c`, command-family and loader/saver sources.

- **ADOPT:** explicit Application/Window/Document boundaries and command-family separation.
- **ADAPT:** preserve Calamus' plain-text authority and single window.
- **REJECT:** plugin/session complexity not required by the product.

### GNOME Text Editor
Files: `editor-application.c`, `editor-session.c`, `editor-window.c`, `editor-page.c`, `editor-document.c`.

- **ADOPT:** one explicit session owner for multi-object application lifecycle.
- **ADAPT:** use the pattern first for Calamus composition, then extract the document session in W102.
- **REJECT:** asynchronous/session breadth not needed in W100 itself.

### Pluma
Files: `pluma/pluma-application.c`, `pluma/pluma-app.c`, `pluma/pluma-window.c`, `pluma/pluma-document.c`.

- **ADOPT:** thin launcher, application-level factories and explicit cleanup.
- **ADAPT:** typed component bundles without activatable plugins.
- **REJECT:** plugin activatable machinery.

### Kate
Files: `kateapp.cpp`, `katedocmanager.cpp`, `katemainwindow.cpp`.

- **ADOPT:** explicit app/document-manager/main-window ownership.
- **ADAPT:** no multi-document manager is introduced in W100; the lesson is ownership separation.
- **REJECT:** IDE/session breadth.

### Geany
Files: `src/main.c`, `src/libmain.c`, `src/document.c`.

- **ADOPT:** named initialization profiles and explicit document functions.
- **REJECT:** broad `main_widgets` and `documents[]` globals, which are equivalent to a service locator.

### NotepadNext
Files: `NotepadNextApplication.*`, `MainWindow.*`, `EditorManager.*`, `SessionManager.*`.

- **ADOPT:** explicit editor/session managers and stale-reference cleanup.
- **REJECT:** broad MainWindow command ownership and window-close as implicit application lifecycle.

### Pulsar
Files: `atom-application.js`, `atom-window.js`, `atom-environment.js`, `workspace.js`, `text-editor.js`.

- **ADOPT:** explicit environment construction and model/view lifecycle distinction.
- **REJECT:** Electron, global `window.atom`, package dynamism and plugin override.

### Lite XL
Files: `core/init.lua`, `doc.lua`, `docview.lua`, `rootview.lua`, `command.lua`.

- **ADOPT:** Doc/DocView/RootView separation and command predicates.
- **REJECT:** global mutable `core` and dynamic plugin command replacement.

## Cross-source decision

The convergent pattern is:

```text
thin launcher/window shell
→ explicit Application/Composer/Session owner
→ document/session and subsystem managers
→ concrete views/adapters
```

W100 therefore freezes typed composition and ownership contracts. It explicitly
forbids solving the monolith by moving methods to files that still receive the
whole `App`, by introducing a service locator, or by adding a generic event bus.
