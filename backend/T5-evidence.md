# T5 maker evidence

Worktree: certificate-t5/certificate-admin-console, detached baseline 1b30bbe13fde37334738a22b5a3395d53b8fdee5. User approved .scratch/certificate-admin/T5-proposal.md. Writer edits limited to registered T5 paths; parent supplied main.py route assembly.

## Public seam and impact

Real FastAPI HTTP requests with temporary file SQLite; SQL is used only to arrange timestamp/tenant fixtures. Observations use list/detail responses, not internal functions or SQL results. Existing search, isolation, pagination limits/defaults and UTC values stay intact. No schema change, CSV, 100k performance claim, or browser timezone conversion.

## Actual red/green sequence

1. Clean locked environment: uv sync --locked; original tests/test_certificates.py: 9 passed (3.17s).
2. Added original Sydney/Perth sample + list/detail consistency + client timezone ignored test: failed KeyError issued_local_date. Added tenant_time.py, migrated T1 SQL to certificate_query.py, installed approved tzdata, parent connected routes: 1 passed (0.51s).
3. Added both-direction 4-page local-day sort with same-day timestamps opposite ID order: failed at ID position 1 (002 versus 003). Registered tenant-bound SQLite function and sorted before LIMIT/OFFSET with id ASC tie: 2 passed (0.50s).
4. Added invalid tenant timezone test: failed with uncaught ZoneInfoNotFoundError. Explicit HTTP500 Invalid tenant timezone for list/detail, unaffected West tenant succeeds: 3 passed (0.57s).
5. Added naive/malformed timestamp test across normal list, date-sorted list and detail: failed HTTP200 versus expected500. Reject naive timestamp, map invalid projections to explicit HTTP500; sorted callback records invalid input and rejects result instead of returning a partial page: 4 passed (0.58s).
6. Added five literal Sydney winter and both DST transition cases. Already green under zoneinfo: no new production code and no fabricated red. Final target suite: 9 passed (0.81s).

Commands: `.venv/Scripts/python.exe -m pytest tests/test_tenant_time.py -q`; frontend `npm ci --no-audit --no-fund`, `node node_modules/vue-tsc/bin/vue-tsc.js --noEmit` passed. Existing Starlette httpx TestClient deprecation warning remains; no unrelated dependency changes.

## Interfaces

- list_certificates(db, tenant_id, q, page, page_size, sort, order): same page envelope, additive local fields. Tenant comes from authenticated route; timezone fetched from server database.
- get_certificate(db, tenant_id, certificate_id): same tenant-scoped404, additive local fields.
- local_fields(issued_at, ZoneInfo): shared conversion for future CSV; raises ValueError for invalid/naive timestamp.
- CertificateTime.vue: localDate, localDatetime, timezone string props; presentational server-value display, no events or state. Parent owns table/detail composition and sorting control.

Dependency: explicit tzdata>=2026.6 with exact uv lock 2026.6; clean environment was synced successfully. Only tzdata project dependency/lock addition expected.

## Limits and handoff

Browser behavior awaits parent integration and verification. No UI runtime pass claimed from typecheck. T1 exact complete-dictionary test must gain the new literal local fields (parent owns update). SQLite local-date ordering computes matching rows; T6 owns 100k performance measurement. No commits, remote actions, or modifications outside owned files by this writer.
