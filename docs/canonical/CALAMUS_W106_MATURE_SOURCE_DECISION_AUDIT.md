# W106 Mature Source Comparison

All comparisons below are from source code supplied by the user.

## gedit — `gedit-settings.c` + GSettings schema

gedit separates editor preferences, UI preferences and window state through
typed GSettings schemas. `GeditSettings` listens for setting changes and
projects them to views/documents centrally.

ADAPT:
- typed keys and defaults;
- preference change notification/projection;
- separate editor/UI/window-state categories.

REJECT:
- global application traversal from the settings object;
- direct dependency on GSettings as a Calamus requirement.

Calamus should retain plain local files but copy the ownership separation.

## Pluma — `pluma-settings.c` + schema

Pluma follows the same pattern and explicitly separates editor/view choices
from window-state keys such as size, panel sizes and active pages.

ADAPT:
- preference vs window-state distinction;
- typed normalization/defaults.

## GNOME Text Editor — `org.gnome.TextEditor.gschema.xml`,
`editor-page-gsettings.c`

The schema is a single typed source for editor preferences. The page settings
provider watches change events and emits a logical settings-changed signal
rather than making each menu handler rebuild state independently.

STRONGLY ADAPT:
- one typed preference authority;
- observers/projections consume state changes;
- application code should not retain a second raw settings mirror.

## NotepadNext — `ApplicationSettings.*`, `MainWindow.cpp`,
`RecentFilesListManager.cpp`

`ApplicationSettings` gives named typed getters/setters and change signals.
`MainWindow::saveSettings()` stores geometry/window state separately from
ordinary editor preferences. Recent files are managed by a dedicated
`RecentFilesListManager`.

STRONGLY ADAPT:
- typed setting access;
- separate geometry/window state;
- separate MRU collection owner.

REJECT:
- Qt-specific inheritance from QSettings;
- tab/session features irrelevant to Calamus.

## Geany — `keyfile.c`, `stash.c`

Geany groups preference definitions and can load/save groups from key files.
It also separates PREFS and SESSION payloads.

ADAPT:
- grouped schema/codec;
- preference/session separation.

REJECT:
- large global mutable preference structs;
- widget-bound stash groups as the final Calamus architecture.

## Airpad — `options.c`

Airpad has a simple key-file lifecycle with defaults and one application
options structure. It is lightweight and understandable, but handlers mutate
GTK-derived option state directly and persistence is one broad general bag.

ADOPT:
- simplicity and local-file ownership.

REJECT:
- widget-driven preference truth;
- one undifferentiated global option bag.

## Convergent mature pattern

Across toolkits, the useful common architecture is:
1. typed defaults and normalization;
2. one authoritative preference store/model;
3. separate persisted window/session/application state;
4. recent/MRU collections as dedicated state owners;
5. change projection from logical state to UI;
6. UI widgets are consumers, never persistence authority.
