# T6 maker evidence

Worktree: certificate-t6/certificate-admin-console. Base: 746edeef3f5194c440592d2e1b8fa2309fdfc9bb. No commit or push. Root supplied main.py/database.py adapters; they are not this writer's delivery files.

## Public seams and observed red → green

1. Real HTTP CSV contract test initially failed 404 instead of200. Added CSV response using shared tenant/date query. CSV test plus 9 existing T5 tests passed (10 total).
2. Formula/quoted-text test failed because ` =1+1` was unchanged. Added prefix neutralization, retaining DB values. Both CSV tests passed. Added tenant/filter/all-six-sort-directions/empty/invalid-parameter/date-error regressions; these passed with existing shared query, without a fabricated red.
3. Real TCP stream test initially failed because response had Content-Length24828593 and no chunked transfer. Replaced buffered response with bounded queue2 and producer-owned SQLite connection/read transaction, fetchmany1000, first-batch preflight. VM progress callback plus queue cancellation and shielded join release resources. Real socket test then passed: list succeeds while consumption paused, WAL checkpoint reports busy during active snapshot, then succeeds after disconnect.
4. Standalone generator command first failed missing file. Added explicit-new-path generator; first green attempt exposed a genuine FK setup error, corrected by inserting valid enrollments before certificates. CLI test passes and rerun refuses existing file without modifying its bytes.
5. Added actual write-during-stream snapshot test and early-disconnect regression; both pass. The early-disconnect test closes before reading headers but cannot prove exactly which server instruction ran at disconnect; pre-first-batch cleanup is additionally visible in response lifecycle code.

## Final focused checks

`backend/.venv/Scripts/python.exe -X utf8 -m pytest tests/test_export_stream.py backend/tests/test_csv_export.py backend/tests/test_tenant_time.py -q`: **17 passed**, one pre-existing Starlette httpx deprecation warning,9.26s.

`frontend: npm ci --ignore-scripts`, `node node_modules/vue-tsc/bin/vue-tsc.js --noEmit`: passed. No lock changes. Browser behavior left to main thread; typecheck is not browser proof.

`git diff --check`: passed; line-ending normalization warning only on root-supplied database.py.

## Actual performance run

Commands from this worktree:

```
backend/.venv/Scripts/python.exe -X utf8 scripts/generate_export_fixture.py --database .smoke/t6-performance.sqlite3
backend/.venv/Scripts/python.exe -X utf8 scripts/benchmark_export.py --database .smoke/t6-performance.sqlite3
```

Generated East100000 and West4 certificates in an explicitly new ignored file; kept default IDs so application restart does not add extra seed certificates. Names contain ties, local dates span days, includes revoked certificates. Generator refuses overwrite. `--rows` supports small focused fixtures (minimum12), defaults100000.

Measured on Windows11 build26200, Python3.14.6, SQLite3.50.4, AMD64, Intel64 Family6 Model186 Stepping2,12 logical CPUs. Date descending with id ascending ties:

| Run | Rows | Bytes | Total seconds | List completed after request start |
| --- | ---: | ---: | ---: | ---: |
| Complete1 |100000|5499933|1.054|0.494s, before export EOF |
| Complete2 |100000|5499933|1.000|not probed |
| Filter `Perf Learner 000`, learner ascending |2000|110062|0.107|not probed |

Both complete file SHA256: `f59a6d0146ff1eaa14fcfb6c61c65bbb6c56743048960e284d34c70c789ed76b`. Incremental parsing verifies count, East serial namespace, ordering and tie-ID monotonicity; repetition hash matches. Observed actual Python server peak working set66,883,584 bytes. Initial instrumentation sampled Windows venv launcher instead; corrected to read actual server PID before recording the final figures. Benchmark closes its stdin-owned server after measurement. This is one-machine evidence, not a universal latency guarantee.

## UI and module responsibilities

ExportCertificates.vue owns one download action/status/cancel control; props actorId,q,sort,order. api/export.ts owns HTTP+Blob read. Identity switch/unmount aborts, generation ignores stale responses, incomplete transfer rejects before creating download; object URL released after click. Browser Blob memory remains the explicitly accepted file-size tradeoff.

## Delivery paths

- backend/app/csv_export.py
- backend/app/certificate_query.py
- backend/tests/test_csv_export.py
- tests/test_export_stream.py
- scripts/generate_export_fixture.py
- scripts/benchmark_export.py
- frontend/src/api/export.ts
- frontend/src/components/certificates/ExportCertificates.vue
- backend/T6-evidence.md

Remaining limits: no Linux/macOS execution or browser acceptance by this writer. Stream error after headers intentionally terminates transfer rather than appending JSON. Long read snapshots may delay WAL checkpoint. SQLite runtime version risk remains the root's separately documented environment limitation; no global runtime was changed.
