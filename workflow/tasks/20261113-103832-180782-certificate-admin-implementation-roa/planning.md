# Planning Record

- status: `discovering`
- grilling_status: `pending`
- multi_session: `true`
- spec_ref: `workflow/tasks/20261113-103832-180782-certificate-admin-implementation-roa/spec.md`

## Unresolved decisions

- Each requirement needs explicit user confirmation before its execution packet can enter EXECUTE.

## Decisions

- None

## Acceptance criteria

- [ ] Not defined

## Tracer-bullet tickets

### T0: One-command bootstrap

- blocked_by: none
- [ ] Meet the explicit acceptance criteria in .scratch/certificate-admin/issues/T0.md after per-ticket user confirmation.

### T1: Tenant-scoped certificate list

- blocked_by: T0
- [ ] Meet the explicit acceptance criteria in .scratch/certificate-admin/issues/T1.md after per-ticket user confirmation.

### T2: Bulk issuance outcomes

- blocked_by: T1
- [ ] Meet the explicit acceptance criteria in .scratch/certificate-admin/issues/T2.md after per-ticket user confirmation.

### T3: Concurrent idempotent retries

- blocked_by: T2
- [ ] Meet the explicit acceptance criteria in .scratch/certificate-admin/issues/T3.md after per-ticket user confirmation.

### T4: Certificate revocation

- blocked_by: T3
- [ ] Meet the explicit acceptance criteria in .scratch/certificate-admin/issues/T4.md after per-ticket user confirmation.

### T5: Tenant-local dates

- blocked_by: T4
- [ ] Meet the explicit acceptance criteria in .scratch/certificate-admin/issues/T5.md after per-ticket user confirmation.

### T6: Streaming CSV at 100k rows

- blocked_by: T5
- [ ] Meet the explicit acceptance criteria in .scratch/certificate-admin/issues/T6.md after per-ticket user confirmation.

### T7: Delivery and evidence

- blocked_by: T6
- [ ] Meet the explicit acceptance criteria in .scratch/certificate-admin/issues/T7.md after per-ticket user confirmation.
