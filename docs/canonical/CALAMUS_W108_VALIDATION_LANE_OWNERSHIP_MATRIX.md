# W108 — Validation lane ownership matrix — FROZEN

Each completion fact has one primary authority lane. A later lane may observe a consequence but may not reconstruct/reparse the primary authority's structural proof.

| Fact | Primary authority | Forbidden duplicate in current W108 GTK |
|---|---|---|
| 39 baseline seams all closed; semantic whole-App seam count zero | W108 source/static | re-counting by runtime reflection |
| no renamed App-equivalent host/context/service bag | W108 source/static | hasattr/private graph walk |
| exact 24 W101 aliases, ledger schema, removal authority | W101/W108 headless+source | reading/parsing ledger JSON from GTK E2E |
| alias projection before Workspace startup | W101/W108 headless | private `_components` topology assertion |
| `_components` assigned once and complete; Recent projection afterward | W101/W108 headless | `composition_complete` or private bundle assertions in current GTK |
| exact 117 bindings and stable command IDs | W104 source/headless | `len(binding_ids()) == 117` in GTK |
| port families explicit; no generic command host | W104/W108 source | private family cardinality assertions in GTK |
| aggregate root records confined | W108 source/headless | object graph introspection in GTK |
| menu catalog/shortcut identity | W104/W105 source/headless | rebuilding catalog in GTK |
| command actually reaches live owner and changes product state | W108 true-App/GTK | static-only proof is insufficient |
| Character Map insert + Undo/modal semantics | W108 true-App/GTK + W103 behavior | source shape alone is insufficient |
| DnD open + drag finish | W108 true-App/GTK | private drop-owner inspection |
| Recent Workspaces re-projection | W105 historical behavior E2E, amended only for superseded facade | calling `_components.workspace.host_runtime` |
| close/quit/no residual process/config unchanged | W99/W108 true-App lifecycle | source-only inference |
| exact source-tree reconstruction/modes | package/reconstruction gate | GTK check |

Historical W107→W98 true-App architecture tests remain frozen under their original work-item authority unless W108 explicitly removes the physical facade they invoke. W108 must not generalize its black-box rule into a retrospective test-architecture rewrite.
