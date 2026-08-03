CALAMUS — MEMORIA OPERATIVA SUPPLEMENT
W100 MONOLITH DECOMPOSITION CONTRACT — CANDIDATE R1
Date: 2026-08-03 (Europe/Rome)

BASELINE
9a80b266cbdb41b499efdb296ff2a312cf85656f — W99: complete GTK-free and lifecycle audit

STATUS
W100 AUTHORIZED / CONTRACT IMPLEMENTED IN ISOLATED CANDIDATE / HEADLESS-CERTIFIED
DESKTOP VALIDATION PENDING
NO CANONICAL REPOSITORY MUTATION
NO COMMIT OR PUSH

BINDING ROADMAP
W100 Monolith Decomposition Contract
W101 Application Composition Root Extraction
W102 Document Session Extraction
W103 Editor Transaction Extraction
W104 Command and Action Architecture
W105 Menu and UI-State Decoupling
W106 Preferences and Application State Extraction
W107 Subsystem Host-Port Migration
W108 Thin GTK Shell
W109 Monolith Closure Gate
W110 Source Code Cleanup
W111 Product Roadmap Rebaseline

W100 OUTPUTS
- exact baseline metrics;
- all 266 App methods assigned;
- all 94 assigned App attributes assigned;
- all 35 functions accepting the whole App inventoried;
- mature-source composition decisions;
- executable growth and completeness gates;
- current W100 runtime identity.

HEADLESS EVIDENCE
- source files: 536;
- changed paths from W99: 24;
- full discovery: 1660 PASS, 84 environmental skips;
- headless-core: 1547 PASS, zero skips;
- W100 focused: 13 PASS, zero skips;
- historical W99 focused: 29 PASS, zero skips;
- filesystem capabilities: 3 PASS, zero skips;
- Python compile: 406 files PASS;
- Bash syntax: 40 files PASS;
- source provenance: PASS;
- distributive ZIP preflight: PASS after extraction with python3 -m zipfile.

CANDIDATE-CONSTRUCTION LEDGER
1. The first focused run found one stale mature-source path spelling in the new
   W100 decision audit. The documentary path was corrected before candidate freeze.
2. The first release-manifest run found stale W99 identity test IDs after the
   historical identity oracle was reclassified. The manifest was corrected.
3. The first headless-core run found two historical tests still expecting the W98
   identity/baseline. They were updated to the current W100/W99 authorities.
4. The first package build omitted newly added files because the patch was created
   without intent-to-add. Patch generation was corrected with git add -N.
5. The next package preflight created a temporary .git directory during patch
   reconstruction, which correctly appeared as an unexpected source path. The
   reconstruction now applies the patch without git init. The final distributive
   preflight is PASS.
6. The preflight-only runner initially reused the generic desktop PASS marker in
   its EXIT report. The runner now emits a distinct PREFLIGHT marker and
   cannot classify a headless package check as desktop validation.

These were candidate-construction and packaging defects discovered before desktop
validation. They are retained here and are not classified as desktop candidate FAILs.

W100 DOES NOT EXTRACT PRODUCT RESPONSIBILITIES.
The first code extraction is W101 after W100 is CLOSED/CERTIFIED/PUBLISHED.
