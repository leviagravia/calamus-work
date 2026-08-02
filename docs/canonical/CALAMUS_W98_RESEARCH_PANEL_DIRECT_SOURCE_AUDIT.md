# W98 — direct Calamus source audit

The published W97 source was read directly. The audit mapped 26 Research commands and all seven clients. It confirmed that Source Notes and Scratchpad already synchronize on document identity, while Bibliography, Tags and Authoring Bridge remained stale when already visible after document switches; Bibliography and Authoring Bridge also remained stale after live document edits. Persistence and transaction boundaries were already sound. The missing boundary was typed cross-client invalidation and Research-wide shutdown.

The chosen correction is a fixed coordinator with declared dependencies, hidden-client dirty state, active refresh, bounded content coalescing and idempotent shutdown. Existing stores/controllers/views remain authoritative; no Full behavior or new persistence is introduced.
