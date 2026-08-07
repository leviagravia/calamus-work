# W107 — Test and Gate Plan

Baseline: `e8befafaf7f75d958eabbd2e273f83c630042b84`.

## Focused pure/static gate

`w107-headless-focused` owns:
- narrow-port validation;
- Search transactional mutation/projection;
- Spellcheck widget-free transaction flow;
- Workspace host narrow authority;
- W107 identity and W108 exclusion;
- no AppHost/ApplicationContext/service locator/event bus;
- Research composition ownership;
- private typed Search/Spell/Print bundle;
- bounded App compatibility delegates;
- no restored `App.state`;
- complete `Ctrl+Alt+L` removal with no replacement.

Zero skips required.

## Historical headless barrier

Run in order:
W107, W106, W105, W104, W103, W102, W101, W100, W99, W98 focused profiles.
All zero-skip.

`headless-core` must pass zero-skip.

## Full discovery

Every discovered automated test must be assigned to at least one release profile.
Full discovery may contain only capability/environment skips; no failure/error.

## Capability gates

Run where available:
- filesystem/symlink/FIFO/case-rename;
- real GIO;
- real Pandoc;
- GTK component/display lanes on T480.

## True-App / true-GTK

Current W107 lanes:
1. exact W107 identity/About/System Info;
2. W107 subsystem host-port product lane:
   - private typed bundles present;
   - no broad App/state/runtime aliases;
   - Search replace-all through W103 transaction and Undo;
   - Workspace close/open through host/runtime owners;
   - Research panel behavior unchanged;
   - Line Numbers command works while Ctrl+Alt+L is absent;
   - normal close and real config unchanged.

Historical GTK order after W107:
W106 preferences/state → W105 UI-state → W104 command/action → W103 transaction
→ W102 session → W101 composition → W99 lifecycle → W98 Research.

## Desktop manual controls

The Candidate runner must open one known fixture and print exact click-by-click
instructions. Manual validation must include visible representative W107 behavior
and confirm Help/Keyboard Shortcuts does **not** list `Ctrl+Alt+L` for Line Numbers.
Never instruct the user to press Ctrl+Alt+L on Linux Mint.

## Repeated desktop FAIL policy

Two consecutive valid Candidate desktop FAILs => STOP. No automatic third
candidate. Return to direct Calamus + mature-source audit and resume only after
explicit authorization.

## R2 hostile construction-order regression

The W107 contract lane must prove that:
- `calamus_ui.build_menu()` does not call
  `app.populate_recent_workspaces_menu()` before core composition;
- App performs the initial Recent Workspaces projection only after assigning
  `_components = compose_core_application_components(...)`;
- the App compatibility method still delegates to
  `_components.workspace.host_runtime.populate_recent_workspaces_menu()`;
- true-App GTK construction reaches post-composition state without an
  `_components` AttributeError.

## Post-FAIL2 Workspace ownership hostile gates

The post-audit candidate must prove:
- WorkspaceHostRuntime source has no `bind_components`, `components` property or
  `_components` slot;
- Workspace builder owns a named `SetOnceReference("workspace-host-runtime")`;
- host callbacks resolve through that set-once reference during construction;
- host direct collaborators are the exact objects in final WorkspaceComponents;
- startup `dataclasses.replace()` cannot create a stale host aggregate because
  no aggregate is retained;
- W101 core-composition contract still passes;
- full true-App W107 behavior proceeds beyond ownership checks through Search,
  Workspace close/reopen, Research toggle, Line Numbers and normal shutdown.

## R3 oracle failure regression barrier / R4

The W107 headless contract lane must reject `document_session.dirty` in the
W107 true-App test and require the frozen W102 checks
`document_session.modified` and `document_session.requires_save_confirmation()`.
The true-App Search lane must still prove replace-all changes the buffer before
those assertions and Undo restores the exact prior text.

R4 reruns the complete automated sequence. No R3 gate result is inherited.
One valid R4 desktop FAIL exhausts the current 2/2 retry budget and triggers
mandatory STOP before any further candidate.
