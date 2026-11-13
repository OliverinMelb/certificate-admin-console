# T2 / T5 execution evidence

## Isolation and integration

User approved parallel T2/T5 including no reissue after revocation, then explicitly accepted T1 browser verification and authorized local T1 baseline commit only. Base: 1b30bbe13fde37334738a22b5a3395d53b8fdee5. Native linked worktrees certificate-t2 and certificate-t5 were registered clean at this SHA before writers started. Root supplied shared route wiring. Writers stopped before root copied owned files, T2 then T5. No T2/T5 commits or remote pushes.

Detailed red-green cycles: backend/T2-evidence.md and backend/T5-evidence.md. Integrated configured checks initially PASS: frontend types/build, 27 HTTP tests, 4 process smoke tests. Initial acceptance mapping mistakenly assumed CLI argument order; workflow sorted criteria. Review found the mismatch; corrected by actual criterion text before final verify.

## Browser observations

Real Chrome at http://127.0.0.1:8015 with separate ignored .smoke/t2-t5.sqlite3, not the user's default demonstration database. Submitted East: observed busy/disabled course and button, then 14 outcomes (learner013 issued, incomplete014 skipped, existing001-012 skipped); list refreshed12→13. Selected local-date sort and opened EAST-001 detail:2026-01-11 00:30+11:00 Australia/Sydney. Switched to Bob: old result cleared, West4 and2026-01-10 21:30+08:00 Australia/Perth.

A test-only SQLite trigger on audit insert produced real503; browser displayed uncertainty/error and re-enabled action (browser-error.txt). Removed this exact fixture trigger, manually submitted again: West learner005 issued,006 skipped, existing001-004 skipped. No product failure switch was added.

Clicked West submit and immediately switched Alice; subsequent view remained East with no old operation result. A temporary write-lock fixture was attempted, but exact request/lock overlap was not instrumented; do not claim a measured delayed-response race. Code independently reviewed for generation/identity protection. Final query Alex returned2 East rows, local-date sort selected. Evidence: browser-ready.txt and browser-ready.png. No browser timezone override was applied; UI directly renders server fields, which API tests cover across two tenants.

## Scope and limitations

A4 and A1 issuance paths implemented; A5 list/detail implemented. No T3 result replay, no T4 revoke action, no T6 CSV or100k performance claim. Existing duplicates fail unique-index initialization without deleting data. HTTPX/Starlette deprecation warning persists from baseline; not a failing check.

Frontend caller map: CertificatePage composes BulkIssue, Filters, Table, Detail; CertificateTime is consumed by Table and Detail. Startup/health unchanged; identity changes and read retry remain in existing composable. Guard scan targets nuxt/src and is not applicable to this Vue frontend layout; direct rg caller scan used. Browser covered mount, mutation busy/success/error/recovery, identity switch, date selection/detail; no KeepAlive/media/virtual-list consumers exist.
