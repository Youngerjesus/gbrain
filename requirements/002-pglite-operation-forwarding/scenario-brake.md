---
requirement_id: 002-pglite-operation-forwarding
review_type: scenario-brake
status: completed
verdict: SCENARIOS_MISSING
created_at: 2026-06-20 17:25 KST
---

# Scenario Brake Review

## Verdict

[SCENARIOS MISSING]

Requirement 002 can proceed, but only after the implementation plan treats operation forwarding as a matrix of caller/owner paths plus recovery states, not only as a reuse check for requirement 001 evidence.

## Companion Reviews

### Path Separation Reviewer

- Agent: `019ee38f-40d1-7031-9b21-56e011ec9889`
- Verdict: `[SCENARIOS MISSING]`
- Finding 1: The plan needs an explicit owner/caller actor matrix: CLI owner to CLI caller, CLI owner to MCP proxy, MCP owner to CLI caller, and MCP owner to MCP proxy. Each path must be proved or explicitly collapsed with a same-code-path rationale.
- Finding 2: Direct stdio MCP first-process/no-owner behavior must be treated as a predecessor path to brokered MCP behavior, not implied by CLI direct-open tests.
- Finding 3: Source/auth parity needs paired direct-MCP and brokered-MCP evidence when `GBRAIN_FEDERATED_READ` / `auth.allowedSources` is active.

### Parameter Mutation Reviewer

- Agent: `019ee38f-41a9-7ba1-a820-f66528695f19`
- Verdict: `[SCENARIOS MISSING]`
- Finding 1: Brokered MCP source-scope mutation is not yet proved.
- Finding 2: No-owner direct `search` evidence is still mandatory.
- Finding 3: The second stdio MCP proxy needs a failure-shape check distinct from direct-dispatch invalid params.
- Finding 4: If permission-denied or not-yet-bound socket scenarios are considered covered, closeout must cite exact evidence rather than hand-wave them into generic unavailable-socket coverage.

### Recovery Observability Reviewer

- Agent: `019ee38f-4344-71d1-816f-8cd030f81ee7`
- Verdict: `[SCENARIOS MISSING]`
- Finding 1: `completion_unknown` is covered at IPC level only; CLI/MCP surfaces need evidence that accepted outcome-unknown is distinguishable from ordinary success/failure.
- Finding 2: `owner_unreachable` needs both CLI and MCP surface evidence, with no success-like payload and no fallback into PGLite lock wait.
- Finding 3: `lock_safety_blocked` must prove no cleanup, no forward, and no direct DB open past an ambiguous lock.
- Finding 4: Stale socket recovery must be distinct from owner-unreachable and should prove safe remove/recreate behavior.

## Accepted Obligations

- Add an actor matrix to the plan and final evidence.
- Add direct stdio MCP no-owner evidence before relying on brokered MCP behavior.
- Add paired direct-MCP versus brokered-MCP source/auth parity evidence for `GBRAIN_FEDERATED_READ` / `auth.allowedSources`.
- Add no-owner direct `search` evidence.
- Add second-stdio-MCP proxy failure envelope evidence.
- Add CLI and MCP surface evidence for `owner_unreachable`; add at least one surface-level `completion_unknown` proof or a tightly justified lower-level sufficiency rationale if surface simulation is impractical.
- Assert `lock_safety_blocked` does not clean up, forward, or direct-open.
- Pin stale-socket recovery evidence separately from owner-unreachable evidence.
- If permission denied or not-yet-bound sockets remain lower-level only, closeout must state the exact evidence and residual risk.

## Outcome

The plan must be revised before secondary-plan and implementation. These findings do not change the requirement text, but they expand the proof required for AC2, AC4, AC6, and AC7.
