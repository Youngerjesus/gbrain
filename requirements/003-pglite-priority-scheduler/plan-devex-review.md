# Plan DevEx Review: PGLite Priority Scheduler

## Verdict

GO WITH CHANGES.

## Findings

### D1. Fallback status must be explicit that maintenance did not run

- Severity: medium
- Finding: The plan introduces `maintenance_deferred`. The operator-facing copy must avoid saying or implying the maintenance command was queued, because this slice intentionally does not broker `sync`, `embed`, or `extract`.
- Required change: Tests should assert the stderr status includes `maintenance_deferred`, and closeout must classify each maintenance command as `deferred_safe_fallback`, not `covered_real_command`.

### D2. The fallback should name the command and next action

- Severity: low
- Finding: A generic live-owner error would be hard for agents to recover from. The message should include the command name and a next action: rerun after the owner exits; use `query`/`search`/`think` for interactive reads while the owner is live.
- Required change: Keep the suggested technical-design copy or equivalent.

## Contract Checks

- Public syntax unchanged: yes, if implementation adds no flags.
- No mandatory daemon: yes.
- Existing no-owner direct-open behavior: preserved by design.
- Machine-readable enough for agents: acceptable via stable `maintenance_deferred` status string.

## Required Plan Updates

- Add a note that tests must assert the fallback copy does not contain `queued` unless the implementation actually queues maintenance.
- Add the per-command matrix classification target to closeout.

## Reconciliation

- Reflected in `plans/003-pglite-priority-scheduler/plan.md`: fallback copy must not imply queued/completed maintenance, and closeout must classify the three commands as `deferred_safe_fallback` unless real maintenance queuing is added.
