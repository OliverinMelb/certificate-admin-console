# T2 maker evidence

Base: `1b30bbe13fde37334738a22b5a3395d53b8fdee5`, detached native worktree `certificate-t2/certificate-admin-console`. User approved T2 including no reissue after revocation. Parent supplied shared main.py wiring; writer changed only assigned module, HTTP tests, UI/API/composable, and this evidence file. No commit or remote operation.

## Public seams and cycles

All behavioral observations use FastAPI HTTP with temporary file SQLite. Direct SQL only arranges fault/existing-state fixtures. No internal call assertions or production fault switch.

- Baseline: `backend/.venv/Scripts/python.exe -m pytest tests/test_certificates.py -q`: 9 passed.
- First new HTTP test initially hit missing module during wiring, then a 501 scaffold response (expected 200). Implemented eligibility and persistent issuance: 1 passed.
- Audit/repeat test red: audit route 501; implemented audit schema and atomic event insertion/read: 2 passed.
- Audit-failure test red: uncaught sqlite IntegrityError from test trigger. Added public 503 error mapping after transaction rollback and per-learner savepoints: 3 passed. Trigger rejects the second eligible learner's audit, proving earlier provisional issuance also rolls back; retry after removing fixture succeeds with one event each.
- Cross-tenant/identity and revoked-existing-certificate tests were already green against prior behavior: added individually, 4 then 5 passed. These are regressions, not fabricated red cycles.
- Recoverable serial conflict red: response503 instead of expected200. Test trigger creates a real duplicate serial constraint violation for one learner; narrow classification by SQLite extended error code AND exact certificate column set rolls that savepoint back as failed/serial_conflict, while next learner succeeds. Unknown integrity/DB errors still fail and roll back the whole batch. Final target run: 6 passed, 1 pre-existing Starlette HTTPX deprecation warning, 0.67s.

## UI

BulkIssue: presentational course form and per-learner outcomes; props actorId/courses, emits issued for parent list refresh. useBulkIssue: owns pending/result/error, generation guard and AbortController; identity/unmount clears results; duplicate submit disabled; 15s timeout clearly says the operation may have completed, no automatic retry. API helper and reason labels remain separate. Parent owns mounting and shared types.

`node node_modules/vue-tsc/bin/vue-tsc.js --noEmit` passed. `git diff --check` passed. No browser operation was performed by this writer; parent must verify UI. No claim of automated UI red/green evidence.

## Limits

T3 idempotency-key replay, T4 revocation, T6 CSV/performance remain out of scope. Existing seed certificates have no invented historical audit events. Unique-index migration intentionally fails on duplicate pre-existing certificates rather than deleting data; no destructive migration test added. Full configured matrix and integration/browser acceptance belong to parent.
