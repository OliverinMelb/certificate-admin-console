# Execution evidence

Baseline authorized by user and committed locally as 746edeef3f5194c440592d2e1b8fa2309fdfc9bb; no remote push. Three native worktrees registered before writer launch. Previous preparation packet remains historical; this packet records execution against the integrated base.

Root integrates main/database and UI composition. Writers own disjoint paths, T3 issuance transaction adaptation and T6 shared query extraction explicitly delegated to their sole owner. Public behavior tests and real red/green evidence are owned by each writer; full integration and browser observations by root.

SQLite runtime is 3.50.4 in pinned Python3.14.6. Official WAL documentation https://www.sqlite.org/wal.html describes rare WAL reset race fixed in3.50.7/3.51.3. No runtime upgrade authorized or performed; this version limitation must be disclosed. No production-readiness claim.

Browser proxy adds POST forwarding and drop-issue-once mode to observe actual committed response loss and same-key retry. It is manual local test infrastructure only, not application code.

Root cross-ticket HTTP RED: test_workflow_integration.py against T2 worktree returned405 on revoke, expected200 (1 failed,0.57s). First two attempts were test setup failures (pytest pythonpath picked integration adapter, then missing static build); neither counted as behavior RED. Corrected explicit pytest pythonpath and supplied ignored built frontend for the baseline. Test subsequently will run against integrated modules.


## Integrated verification and browser evidence

Formal workflow verify 20261113-115640-515825 PASS: frontend types/build;47 HTTP tests16.53s;8 startup/real TCP tests46.71s. Includes root cross-ticket revoke→old-key replay→new-key skipped→CSV inclusion test. One preexisting Starlette/httpx deprecation warning. No dependency changes.

Root independent benchmark command: backend/.venv/Scripts/python.exe scripts/benchmark_export.py --database C:/Users/admin/.codex/worktrees/certificate-t6/certificate-admin-console/.smoke/t6-performance.sqlite3 --rows 100000. Windows11, Python3.14.6, SQLite3.50.4, Intel64 Family6 Model186 Stepping2,12 logical CPUs. Two complete local-day-desc exports:100000 rows each,5499933bytes,1.098s/0.947s; shared SHA256 f59a6d0146ff1eaa14fcfb6c61c65bbb6c56743048960e284d34c70c789ed76b. First list response0.510s before EOF1.098s. Filter Perf Learner 000/name ascending:2000 rows,110062bytes,0.095s;SHA2560027a19fb6d3c916abfb5a6c202725f4be1e4ad18a2f347bd5e4ec9dafa727d0. Actual server peak working set66682880bytes. Synthetic isolated performance DB, default seed untouched.

Browser performed through real Chrome UI with loopback proxy to real integrated server, separate .smoke/t346-browser.sqlite3. Initial proxy8015 was denied by Windows bind permissions;8020 succeeded. No application issue attributed to that.

- Dropped one successful issuance response after actual upstream commit. UI showed Failed to fetch and explicit retry/new-operation buttons. Retry returned original east-learner-013 issued, not recomputed skipped; proxy recorded both HTTP200 calls with same key5144d3ef-a801-4a7c-9181-1b0812bbdcfd. Processing state disabled submit. The raw network error wording is a minor UI limitation.
- EAST-001 detail→revoke confirmation→cancel: still active, no revoke POST. Then proxy503 on confirm: error/retry; restored service and retried: revoked, one alice audit displayed. Screenshot/DOM:browser-revocation.*.
- Actual UI CSV download after searchAlex produced certificates.csv and certificates (1).csv in Downloads,144bytes each; saved second file as browser-downloaded.csv. Contains two Alex/EAST001&002/local date2026-01-11 rows, including revoked EAST001. Browser download event wait timed out/reset automation although the file had downloaded; recovery used a fresh browser tab and direct click with filesystem verification, not a fabricated successful event.
- CSV503 shows failure; delayed Alice export shows busy/cancel, explicit cancel restores button. Another delayed export followed by Bob selection cleared state; no additional CSV files appeared. Bob remained4 records after late completion.
- Delayed Alice issuance followed by Bob selection cleared old operation/result; no late result displayed. Delayed EAST002 revocation showed processing; closing detail and switchingBob left no dialog and only West4 records after response. Final DOM/screenshot:browser-final.*. UI cancellation does not claim server transaction rollback.

Test servers/proxy stopped after observations. Browser records are tool-driven observations, not automated UI test counts. No production data used.

## Independent review

Spec reviewer and Standards reviewer both found no blocking code issue. Reviewed real transaction boundaries, tenant filters, idempotent/repeated audit uniqueness, shared query/date ordering, CSV bounded queue/snapshot/cleanup and UI generation guards. No repeated full testing by reviewers.

Nonblocking limits: no direct post-first-chunk producer-failure regression (code truncates transport and joins worker); changing filter during export does not change that already-started export; closing in-flight revoke can leave list stale until next reload; Linux/macOS untested;SQLite runtime issue disclosed above. Review evidence gaps were resolved by recording these root benchmark/browser observations and updating delivery docs. User business acceptance is not inferred.

Final freshness verification20261113-120248-896975 PASS after delivery-doc updates. Both independent reviews pass; Spec reviewer rechecked and closed evidence gaps. Workflow development closed with delivery pending-acceptance; no T3/T4/T6 commit or push. Current HEAD remains authorized baseline746edee. Prior pre-baseline packet is preparation history, not an additional active implementation. Root spec approved appendix and proposals define confirmed requirements; older roadmap '待确认' bullet text is historical checklist terminology, not a request to reconfirm implemented contracts.

