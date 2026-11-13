# Planning Record

- status: `ready`
- grilling_status: `confirmed`
- multi_session: `true`
- spec_ref: `workflow/tasks/20261113-112716-944318-t2-t5-parallel-issuance-and-tenant-d/spec.md`

## Unresolved decisions

- None

## Decisions

- User approved both parallel proposals including no reissue after revocation; user confirmed T1 browser acceptance and authorized local T1 baseline commit. See decisions D006 D007 and approved proposals.

## Acceptance criteria

- [ ] T1 HTTP and startup contracts remain green
- [ ] T2 public HTTP eligibility, no reissue, atomic audit, repeated and cross-tenant writes
- [ ] T5 public HTTP literal timezone samples, DST, errors and stable local-day pagination
- [ ] UI bulk issuance outcomes, identity isolation and server-derived local dates

## Tracer-bullet tickets

### T2: Bulk issuance and audit

- blocked_by: none
- [ ] Approved T2 proposal: eligibility, uniqueness, atomic audit, tenant isolation and UI outcomes

### T5: Tenant dates and stable sorting

- blocked_by: none
- [ ] Approved T5 proposal: UTC preservation, zoneinfo, DST and date pagination
