# T4 implementation evidence

Base: 746edeef3f5194c440592d2e1b8fa2309fdfc9bb. Worktree: certificate-t4/certificate-admin-console. No commit/push. Parent supplied main.py/database.py adapters; those are not this writer's deliverable.

## Public seams and implementation

Tests exercise HTTP against a real temporary SQLite file, observing certificate detail and audit endpoints. SQLite is used only to set up fault/lock fixtures; assertions do not inspect internal rows. Revocation owns BEGIN IMMEDIATE, changes ACTIVE to REVOKED and inserts its event atomically, returns unchanged for repeated requests and maps only SQLITE_BUSY to retryable503.

UI boundary: RevokeCertificate owns confirmation/submission state only; receives actorId/certificateId/status and emits revoked. Parent detail owns loading, audit display and refresh. An inline alertdialog inside the existing native modal avoids competing showModal calls. Actor/certificate/status changes and unmount abort and invalidate responses; browser cancellation never claims to undo server work.

## Actual red/green sequence

1. First revoke test initially hit missing frontend/dist configuration; installed locked local dependencies and built frontend. Meaningful red was HTTP405 versus200. Added minimal transactional revoke and parent synced HTTP adapter: 1 passed.
2. Repeated revoke/restart test red: unique audit constraint exception. Added existing revoked-state check: 2 passed. Restart here recreates the application/lifespan over the same file; not a process-kill test.
3. Cross-tenant/missing test red: foreign-key exception. Added tenant-scoped existence404: 3 passed.
4. Audit failure rollback regression passed immediately with existing transaction: 4 passed. It asserts HTTP500 and unchanged public status/audit, then successful recovery after removing test trigger. No artificial production fault switch.
5. Overlapping request regression passed with existing transaction. Middleware in the test records both HTTP arrivals while an external SQLite writer holds the lock; futures remain incomplete until lock release. Exactly one changed:true response and one audit event after completion. This is concurrent ASGI HTTP with independent DB connections, not a sequential call or claimed socket benchmark.
6. Busy-lock test red: HTTP500 versus503 after the real five-second lock timeout. Added narrow SQLite busy mapping and Retry-After:1: 6 passed.
7. ISSUED preservation and unknown-body regression already passed with existing behavior and parent validation: 7 passed. This test issues a new certificate through HTTP with a key, then revokes and checks original ISSUED event unchanged.

## Focused checks

- uv sync --locked: passed, local .venv only, unchanged lockfile.
- backend .venv/Scripts/python.exe -m pytest tests/test_revocation.py -q: **7 passed, 1 warning, 6.50s**. Warning is locked Starlette TestClient/httpx deprecation.
- frontend node node_modules/vue-tsc/bin/vue-tsc.js --noEmit: passed.
- frontend npm run build: passed. New component typechecked but not yet mounted in this writer's checkout; build is not browser evidence.
- git diff --check: passed (Git CRLF informational warning for parent-owned database.py).

## Delivery files and remaining verification

Only backend/app/revocation.py, backend/tests/test_revocation.py, frontend/src/api/revocation.ts, frontend/src/components/certificates/RevokeCertificate.vue, backend/T4-evidence.md.

Root still needs page/detail wiring, public audit display, browser cancel/confirm/error/identity cases, integration with T3 replay and T6 revoked exports, independent review and final matrix. HTTP tests use T2 issuance adapter with required key; T3 actual persistence implementation is not present in this worktree. No Linux/macOS or browser acceptance claimed.
