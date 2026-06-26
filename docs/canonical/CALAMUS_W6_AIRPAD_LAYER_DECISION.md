# Calamus W6 — AirPad-like Layer Decision

Status: accepted  
Scope: architecture decision only  
Implementation status: not yet implemented

## 1. Decision

Calamus should grow an AirPad-like control layer.

This layer is convenient and advisable, but only if it is introduced as a thin, gradual, behaviour-preserving layer.

The layer must not become a large abstract framework. It must not rewrite Calamus. It must not replace the current application in one step.

The correct model is:

```text
existing Calamus feature
        ↓
documented command/control entry
        ↓
thin layer wrapper
        ↓
tests
        ↓
old direct wiring removed only after parity is proven
```

## 2. Why the layer is justified

Calamus is now source-authoritative in `calamus-work` from the installed stable4.3 package. The installed feature set has been preserved, including the stable4-specific modules and tests.

The remaining architectural problem is not lack of features. The problem is concentration of too many responsibilities in `bin/calamus` and especially in the `App` class.

A layer is therefore justified because it gives Calamus a controlled path from:

```text
feature methods directly wired in App
```

toward:

```text
registered command / context / result / UI binding
```

without removing current behaviour.

## 3. AirPad as model of order

AirPad is not a feature target. It is the model of order.

The useful AirPad principle is separation by responsibility:

```text
main/application lifecycle
window/widgets/menu
file lifecycle
edit commands
undo
search/find/replace
dialogs
options/view/font
quit/lifecycle
```

Calamus should converge toward the same discipline, translated to Python/GTK3.

## 4. What the layer should be

The initial layer should be a **Command/Control Layer**, not a broad service layer.

Recommended initial files:

```text
calamus/calamus_command_layer.py
calamus/calamus_command_context.py
calamus/calamus_command_registry.py
```

Possible contents:

```text
CommandId
CommandSpec
CommandContext
CommandResult
CommandRegistry
```

The layer should initially manage metadata and dispatch discipline, not deep application state.

## 5. What should enter the layer first

The first features to move under the layer should be low-risk and already semantically command-like:

```text
shortcut metadata
menu command metadata
simple text transforms
writing cleanup commands
statistics
date/time insertion
case transforms
sort/reflow/smart typography wrappers
```

These are suitable because they are either pure functions or narrow buffer transformations.

## 6. What must not enter first

Do not begin with:

```text
open
save
save as
dirty state
close
quit
session restore
undo
redo
Gtk.TextBuffer lifecycle
printing
```

These areas are high risk because they combine user data, persistence, modified state, cursor position, history, and GTK synchronization.

## 7. Migration rule

No direct feature should be removed from `App` merely because the layer exists.

The migration order must be:

```text
1. register feature in layer
2. call existing App method through layer wrapper
3. prove no behaviour change
4. move pure logic out only if safe
5. remove old direct path only after parity is certified
```

## 8. Testing rule

Every layer migration must prove source provenance first.

Working-copy tests must not run plain:

```text
calamus
calamus-selftest
```

They must run through:

```text
scripts/prove-source-provenance.sh
scripts/selftest-from-source.sh
```

The provenance proof must show modules loaded from:

```text
/home/luciano/Projects/calamus-work/calamus/
```

and never from:

```text
/usr/lib/calamus/
```

## 9. Implementation staging

### Stage 0 — already achieved by W5

Authoritative installed stable4.3 source imported into `calamus-work`.

### Stage 1 — layer skeleton

Add the layer files with no behavioural change.

Acceptance:

```text
source provenance PASS
selftest PASS
no runtime behaviour change
no command moved yet
```

### Stage 2 — registry of low-risk commands

Register low-risk commands without changing execution.

Acceptance:

```text
registry lists commands
shortcut/menu metadata remains conflict-free
existing tests pass
```

### Stage 3 — wrapper dispatch for safe commands

Route safe commands through the layer while still invoking existing App methods.

Acceptance:

```text
old feature behaviour unchanged
tests pass
manual desktop smoke pass
```

### Stage 4 — pure command extraction

Move pure transformations into layer-adjacent command handlers only when they are already pure or easily isolated.

### Stage 5 — medium-risk UI controls

Move view/font/options/status helpers only after low-risk layer proves stable.

### Stage 6 — high-risk lifecycle

File lifecycle, undo, dirty state, close/session remain last.

## 10. Final decision

Build the layer.

Do it gradually.

The layer should first control command identity, metadata, dispatch and result discipline. It should not initially own file lifecycle or GUI state.

This is the safest path to make Calamus more modular while preserving all features of the installed Calamus stable4.3 package.
