# W108 Changed-Binding Coverage Closure — frozen pre-packaging gate

## Purpose
Prevent “same command family” smoke coverage from hiding a regression in the exact callback/action path that W108 rewired.

The post-audit R2 current W108 smoke exercised `navigate.bookmark.toggle`, while W108 had changed Navigator-panel visibility composition. Historical W101 later found that precise path broken.

## Inventory
Diff published W107 production against the exact package source and inventory every physically changed callback/signal/action binding.

Required fields per row:
- stable row ID;
- W107 source path/symbol/expression;
- package source path/symbol/expression;
- event or command identity;
- payload shape;
- live owner;
- adapter/transformation semantics;
- primary authority lane;
- exact test/receipt that traverses it;
- GTK requirement yes/no;
- status PASS/FAIL.

## Coverage rules
1. Every row must have one primary authority.
2. A sibling command in the same W104 family cannot satisfy coverage for another changed binding.
3. If a changed binding is GTK/event dependent, the exact stable command or natural event must traverse it in true-App unless an unchanged frozen historical true-App test already traverses the exact path.
4. Non-GTK direct-owner rewiring may be owned by headless focused tests.
5. Duplicate tests may exist, but duplicate primary authority for the same fact is forbidden.
6. If a changed binding is removed rather than replaced, the inventory must point to the source/static removal receipt and, where user-visible behavior remains, the replacement behavioral path.

## Mandatory Navigator receipts
Both must PASS:
- current W108 public/stable `navigate.navigator-panel` behavior toggles real Navigator visibility on and off without exception and projects expected UI state;
- historical W101 owner-level `navigator_panel_runtime.set_visible(True)` remains unchanged and PASS.

The two receipts are intentionally complementary.

## PASS receipt
100% inventory classified; zero missing changed bindings; zero rows covered only by family-level proxy smoke.
