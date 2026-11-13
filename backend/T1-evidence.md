# T1 backend maker evidence

Scope: backend/** in the native certificate-backend worktree, base a9ee16346692aee0d5ca47362909bc9f41b28edd. Initial git status was clean and HEAD detached. Approval and HTTP seams are recorded by the main workflow in the canonical T1 execution spec; this document is a summary, not an original interaction export.

Impact envelope: add SQLite initialization and read-only actors/courses/certificates/detail endpoints for the administrator UI. Preserve health and built static hosting; no mutation, audit, authentication infrastructure, frontend, dependency, or lockfile changes. Rollback is restoring these scoped backend files from the base; keep any local database file unless explicitly authorized to remove it.

## Actual sequential TDD observations

Command for each cycle: `uv run --locked --project backend pytest backend/tests/test_certificates.py -q` (later cycles also used `--tb=short`). Each new behavior was introduced only after the preceding cycle passed.

1. Actors and file-path factory: red `TypeError` for unsupported `database_path`; implementation then 1 passed.
2. Courses and actor identity: initial red hit missing frontend/dist because the unimplemented route fell through to static hosting. Added explicit unknown-API 404 handling; confirmed behavioral red 404 versus required 401. Implemented course route/identity/seed; 2 passed.
3. Tenant certificate lists and fixed sample payload: red 404 versus 401; implemented remaining schema, mixed enrollment seed and list; 3 passed.
4. Detail isolation and identical missing/cross-tenant responses: red 404 versus 401; implemented detail; 4 passed.
5. Trimmed name/serial and literal %, underscore, backslash search: red extra unfiltered rows; implemented escaped parameterized LIKE; 5 passed.
6. Pagination, totals and stable ascending ID ties under both sort directions: red unpaginated payload; implemented count/order/limit/offset; 6 passed.
7. Invalid page/page size/sort/order: red 200 versus 422; added public parameter validation; 7 passed.

Additional regression: repeated application startup preserves a pre-existing revoked certificate and all other HTTP rows/counts. Existing data is arranged with SQLite, with results observed only through HTTP; no internal-method or SQL-text assertions. This passed immediately and is not claimed as a separate red/green cycle.

Initialization uses an explicit transaction, six tables and composite tenant foreign keys. Seed inserts use conflict-do-nothing and deterministic IDs. Each synchronous request opens/closes its own connection with foreign keys enabled. Existing T0 HTTP tests now supply temporary database paths. A typo in that helper initially produced a collection SyntaxError; fixed and reran successfully.

## Final maker checks

- `uv sync --locked --project backend`: succeeded; no lockfile changes.
- `uv run --locked --project backend pytest backend/tests/test_certificates.py backend/tests/test_http.py -q -k 'not root_serves' --tb=short`: **10 passed, 1 deselected**, 0.95 seconds.
- `git diff --check`: passed.
- Locked Starlette emits one httpx test-client deprecation warning; no dependency changes made.

Static frontend test, full launcher/startup matrix and real browser verification are intentionally left to the main integrator, which owns the build and independent verification. Default database is resolved from the worktree repository root and initialized on application lifespan startup; tests use actual temporary SQLite files, not the default database. No production identity/security claim is made for the approved demo X-Actor-Id mechanism.

## Integration manifest

- backend/app/database.py (new)
- backend/app/main.py (changed)
- backend/tests/test_certificates.py (new)
- backend/tests/test_http.py (changed)
- backend/T1-evidence.md (new)

Sample actors: alice / bob. Courses: east-safety / west-safety. Samples: east-cert-001 / west-cert-001, both Alex Lee, 2026-01-10T13:30:00Z. East has 12 certificates and West 4; each also has one completed unissued enrollment and one incomplete enrollment. Certificate 002 supplies another Alex Lee stable-sort tie; learner 003 contains literal search characters. All seeded certificates start ACTIVE.

## Independent-review correction: oversized positive page

Main verification identified that a valid positive page could overflow SQLite's integer OFFSET binding. Added HTTP regression for page=9223372036854775807 with default page_size=50. Focused red command `uv run --locked --project backend pytest backend/tests/test_certificates.py -q -k very_large --tb=short` failed with `OverflowError: Python int too large to convert to SQLite INTEGER` (1 failed, 8 deselected). Minimal fix computes the offset in Python and returns empty items with the actual total when offset >= total, before SQLite binding; no new page limit.

Green command `uv run --locked --project backend pytest backend/tests/test_certificates.py -q --tb=short`: **9 passed**, 0.91 seconds, same existing deprecation warning. `git diff --check` passed. Follow-up changes are limited to backend/app/main.py, backend/tests/test_certificates.py and this evidence file. No full matrix run.
