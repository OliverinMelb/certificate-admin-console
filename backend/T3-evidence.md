# T3 maker evidence

Base: 746edeef3f5194c440592d2e1b8fa2309fdfc9bb. Dedicated certificate-t3 worktree; no commits/push. Root supplied main.py/database.py integration adapters, not part of this writer's delivery.

## Public HTTP vertical cycles

1. Same-key second request changed issued to skipped: actual RED 1 failed; added durable result and extracted transaction-owned issuance body; GREEN 1 passed, including application restart.
2. Same key with another permitted course returned200 rather than409: RED 1 failed/1 passed; added fingerprint conflict and course authorization before replay; GREEN 2 passed.
3. SQLite test trigger rejecting operation persistence returned500 rather than503: RED 1 failed/2 passed; added storage failure mapping, transaction rollback retained; GREEN 3 passed. Public list proves no partial certificate; same-key recovery issues normally and audits once.
4. Real Uvicorn/socket request under held SQLite write lock returned503 without Retry-After: RED 1 failed/3 deselected; added specific SQLITE_BUSY mapping; GREEN 1 passed/3 deselected after five-second wait.

Supplemental tests were immediately green with the transaction implementation: actual overlapping network same-key and different-key requests (arrival Condition plus held real write lock, both futures incomplete before release), missing/invalid key, unknown payload, actor/tenant key isolation, and stable replay of a partial-failed result even after fixture fault removal. These are not claimed as additional red cycles.

Final focused command: backend/.venv/Scripts/python.exe -m pytest tests/test_idempotency.py tests/test_issuance.py -q => 14 passed, 1 warning in8.10s. T2 tests updated with unique keys for explicitly new operations, existing business assertions retained. Warning is existing locked Starlette TestClient/httpx deprecation.

## Frontend

BulkIssue remains presentation/selection, useBulkIssue owns async state and retry key, issuance API sends header. New action allocates crypto.randomUUID; explicit retry reuses the operation key; identity/course change clears retry state and generation-guards old responses. UI distinguishes 重试原操作 from 重新发起发证. Props/emits unchanged.

Typecheck and Vite build passed (45 modules). npm ci used project lock without changes. UI implementation follows the API test cycles; no dedicated browser RED or browser pass claimed here. Root performs real browser timeout/lost response and retry verification.

## Delivery / limits

Owned changes: app/idempotency.py, app/issuance.py, tests/test_idempotency.py, tests/test_issuance.py, frontend/src/api/issuance.ts, frontend/src/composables/useBulkIssue.ts, frontend/src/components/certificates/BulkIssue.vue, this file.

No dependencies changed. Python3.14.6 links SQLite3.50.4; root is recording the official rare WAL reset issue separately. No production authentication, expiry cleanup or refresh-persistent frontend context added. Cross-ticket revoke/replay regression waits for T4 integration. Public success status is always200 and stored with the original JSON; no configurable alternate successful status exists.
