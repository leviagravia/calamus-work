# Calamus W97 — Candidate R1/R2 exact failure correction

Date: 2026-08-02
Published baseline: `199459fb023e4862407f7eb60318192f276d3239`

## Superseding evidence

The dedicated product logs for the earlier Candidate R1 and Candidate R2 are now available. Both runs reached the same Python assertion immediately after `search.set_text("patristics")` and one non-waiting GTK pump. The list still contained `beta2021`, `alpha2020`, `gamma2019`; the delayed `Gtk.SearchEntry.search-changed` callback had not yet published the query. Cleanup completed normally.

Exact classification:

`CALAMUS-W97-SEARCH-CHANGED-DELAYED-TEST-ORACLE-01`

Therefore:

- no native GTK crash is proved;
- no ListBox lifecycle failure is proved at the failure point;
- external focus or another editor is irrelevant;
- Candidate R1 and Candidate R2 are INVALID RUN / FALSE-NEGATIVE TRUE-APP ORACLE;
- they do not consume valid product attempts.

## Correction of the earlier hypothesis

The previous lifecycle audit identified genuine architectural risks: selection derived from an ephemeral row and complete row replacement during refresh. Those risks remain worth correcting, but they are not the causal explanation of the two recorded failures. `CALAMUS-BIBLIOGRAPHY-LISTBOX-ROW-LIFECYCLE-01` is retained only as a risk/debt classification, not as the observed failure frame. `CALAMUS-PROFILE-NATIVE-CRASH-EVIDENCE-02` is withdrawn for these runs because the dedicated logs show an ordinary assertion failure and normal cleanup.

## Runner evidence defect

The outer Bash runner did not display the existing dedicated log before its FAIL banner because inherited `ERR` handling intercepted the profile return. Classification:

`CALAMUS-RUN-PROFILE-ERR-TRAP-INTERCEPTION-01`

A corrected runner must execute the profiled command in an `if ...; then ... else ... fi` condition, capture status, print and copy the complete log, then return the status for the outer fail report.

## Rebuild decision

The new line is `W97 Bibliography Manager Core — Search/Model Rebuild Candidate R1`. It uses explicit 150 ms coalescing over `changed`, controller-owned selected key, bounded true-App waits, and crash-visible/profile-visible runner semantics. It is not Candidate R3.
