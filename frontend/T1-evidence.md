# T1 frontend maker evidence

Scope: frontend/** in the assigned certificate-frontend native worktree, starting from detached HEAD a9ee16346692aee0d5ca47362909bc9f41b28edd. Initial worktree was clean. The confirmed execution spec is the verifier worktree's workflow/tasks/20261113-110650-151404-t1-tenant-isolated-certificate-brows/spec.md; its explicit frontend assignment supersedes the older proposal's pending status.

## Component and contract map

- App: thin page shell composing CertificatePage and the existing ServiceStatus.
- CertificatePage: wires composable state into children and handles their emitted actions.
- ActorSelect: actor/course display with loading, empty and error states; typed actors/actorId/course/status props; emits select, retryActors, retryCourses.
- CertificateFilters: typed query/sort/order/disabled props; emits search, sort, order.
- CertificateTable: typed certificate/loading/error/hasActor props; emits detail and retry; UTC timestamps and status labels.
- CertificatePagination: page/pageSize/total/disabled/unavailable props; emits page and pageSize; choices 5/10/50/100.
- CertificateDetail: native modal dialog with typed item/loading/error props; emits close and retry; read-only fields, Escape closes.
- useCertificates: actors, tenant request lifecycle, search debounce (300 ms), sorting, paging, detail selection. Each resource has an AbortController and monotonically increasing generation. Old success/error/finally continuations cannot modify new state. Identity change synchronously clears courses/list/detail, cancels pending search, resets page and search, then loads the selected tenant. Unmount aborts all resources and clears the timer.
- api/certificates.ts: typed actor/course/certificate/list wrappers and same-origin GET with X-Actor-Id for tenant data; UTC formatting.

## Impact envelope and negative-space contracts

Only frontend source and this evidence file changed. No dependencies, package manifests, lockfiles, backend files, database files, routing, authentication policy, or write operations were added. ServiceStatus source and its health request remain unchanged and its controls remain visible. Root shell/global form presentation changes support the feature. Rollback is to restore these scoped source changes and remove the new feature files; no data migration or persistent state is involved.

Default identity is the first actor returned by the API; default sort serial_number asc, page 1, page size 50. Identity switches also clear search to avoid confusing empty results in another tenant. Courses are displayed, not offered as an unsupported course filter. UTC formatting deliberately does not convert to the administrator's timezone. Requests time out after 15 seconds and expose retry.

## Maker checks

Run in frontend on 2026-11-13:

- npm ci: exit 0; 50 packages installed; 0 audit vulnerabilities; lockfile unchanged.
- npm run typecheck: exit 0 (vue-tsc --noEmit).
- npm run build: exit 0 (Vite production build; 37 modules).
- git diff --check: exit 0.

No maker check failed. No frontend unit harness or fabricated mock integration evidence was introduced. Per the approved assignment, these checks are compile/build checks only, not proof of runtime behavior or a local red/green UI test cycle.

## Remaining verification

The main thread owns real browser acceptance on the integrated app: actor/course isolation, search, sort, paging and page reset, readonly detail and keyboard closing, loading/empty/error/retry, delayed list/course/detail responses across identity changes, narrow-screen layout, and existing T0 connection behavior. The native modal prevents background identity selection while open; race verification can close it during detail loading and then switch identity. No commit, merge, push, deployment, or full startup matrix was run here.
