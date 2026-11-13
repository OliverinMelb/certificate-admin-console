# T7 AI record evidence

Base 5e52148f528c9d8842a1a22d921af0bc1ecb82f8, clean detached integration worktree.
Scope: docs, standalone export CLI and artifact tests; no application/DB/API/dependency/runtime changes. Original logs read-only; generated transcripts ignored under .smoke, never staged. Rollback reverts only this docs/tooling commit.

Five vertical TDD slices through CLI/artifact seam: visible records vs internal fields; fork/nested-agent closure; credentials and changed transcript; appended source vs altered prefix; structured credential redaction preserving failure. Each observed red before corresponding implementation; final 5 passed.

Source inventory scans first-line metadata only outside selected tree. All 15 related logs located on 2026/11/13. Initial global inventory refused duplicate unrelated historical ID; narrowed export to verified date directory, no silent overwrite.

Preview: 15 sources, 6220 source lines, 2052 visible records, 8 pattern-based redactions, 0 incomplete-tail bytes. Preview export and source-prefix replay verification passed. 13 observed spawn task names match 13 child agent metadata paths; zero unmatched names. Final snapshot after reviews will have updated counts and explicit byte cutoffs in its manifest.

A1-A7 application evidence unchanged. Previous clean ZIP startup smoke passed; AI companion packaging does not alter application source. Final source ZIP and AI ZIP have separate checksums and combined manifest. Raw internal logs are not exported. External acceptance/push not performed.

Review fix: sixth CLI test first failed, then passed after source-derived ledger/lineage/set replay and nested omission tracking. Removed runtime agent_message records; retained child-session visible messages/tools. Prior 2052 preview count predates this stricter filter and is not final delivery count. All 6 focused tests pass. Fixed roadmap heading and documented exact local ZIP/checksum/combined-manifest commands.
