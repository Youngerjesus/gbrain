# Scenario Brake: PGLite Priority Scheduler

## Verdict

SCENARIOS MISSING, reconciled.

## Reviewer

- Agent: `019ee3b3-c59d-7651-bf2b-feab8cd3eb95`
- Role: Scenario Recovery Observability Reviewer

## Findings

### S1. Owner starting/dying scenarios need concrete outcomes

- Severity: high
- Finding: The requirement names owner socket-not-bound and owner death while queued, but the plan lacked concrete verification.
- Reconciliation: Added startup-election-held `owner_starting` fallback to design/plan. Existing owner-missing socket and completion-unknown regression tests remain part of the related suite for owner unreachable/death behavior.

### S2. Corrupt/unknown lock evidence must be mandatory

- Severity: high
- Finding: The technical design specified `lock_safety_blocked`, but the test plan made corrupt-lock coverage optional.
- Reconciliation: Promoted corrupt-lock maintenance fallback to mandatory test evidence.

### S3. No-owner direct-open preservation needs evidence

- Severity: medium
- Finding: Absent-lock direct-open behavior is a required preservation invariant for `sync`, `embed`, and `extract`.
- Reconciliation: Added no-owner direct-open smoke evidence requirement for all three maintenance commands or explicit existing-test citation.

## Final Status

All findings were accepted and reconciled into `technical-design.md` and `plans/003-pglite-priority-scheduler/plan.md`.
