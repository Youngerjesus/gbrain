# Plan DevEx Review

## Plan Under Review

- Requirement: `requirements/002-pglite-operation-forwarding/requirements.md`
- Draft plan: `plans/002-pglite-operation-forwarding/plan.md`
- Product type: CLI, stdio MCP, documentation/evidence slice
- Review mode: DX TRIAGE

## Persona And TTHW Target

Target developer/operator: an open-source contributor or local operator validating that gbrain's PGLite forwarding works without reproducing a live user brain.

TTHW target: Competitive, 2-5 minutes for focused verification after dependencies are installed.

Magical moment: a copy-paste test command passes and shows the forwarding paths no longer emit PGLite lock timeout errors.

## Top DX Findings

### DX1 - The plan should name the exact minimum smoke command for this slice

- Risk: the plan includes both focused and full related suites, but does not say which command is required when no code changes occur versus when a small test is added.
- Developer impact: future agents may over-run full suites unnecessarily or under-run after touching tests.
- Required plan change: keep the focused suite as the minimum no-code-change proof and the broader suite plus typecheck as mandatory after any code/test/doc change.
- Verdict impact: GO WITH CHANGES.

### DX2 - Evidence reuse needs commit/path pinning in closeout

- Risk: this slice explicitly reuses requirement 001 implementation; without pinning commit `d50dc701` and worktree path, evidence can become ambiguous after later sequence edits.
- Developer impact: reviewers cannot tell whether the evidence was current at the time of closeout.
- Required plan change: implementation-brake/closeout must record commit `d50dc701` or a newer verified commit, test command output, and task worktree path.
- Verdict impact: GO WITH CHANGES.

### DX3 - Debuggability of MCP proxy path depends on JSON-RPC test evidence

- Risk: MCP stdio failures are harder to debug than CLI failures; plan should preserve the JSON-RPC initialize/list/call evidence from the existing test rather than only citing unit IPC tests.
- Developer impact: contributors may accidentally validate only the socket layer and miss MCP envelope drift.
- Required plan change: AC2 proof must include the second stdio MCP proxy integration test.
- Verdict impact: GO WITH CHANGES.

## DX Scorecard

| Dimension | Score | Target/Gap |
| --- | ---: | --- |
| Getting Started Experience | 8/10 | Copy-paste commands exist; minimum-vs-full gate should be explicit |
| API/CLI/SDK Design | 9/10 | Public syntax unchanged |
| Error Messages And Debugging | 8/10 | Statuses strong; copy review required by UX |
| Documentation And Learning | 7/10 | Evidence docs exist; closeout must pin commit/path |
| Upgrade And Migration Path | 9/10 | Backwards-compatible local behavior |
| Developer Environment And Tooling | 8/10 | Hermetic tests; no live brain required |
| Community And Ecosystem | 7/10 | Normal repo contribution path; no new support surface |
| DX Measurement And Feedback | 7/10 | Test pass/fail is measurable; production readiness handles broader DX |

## Implementation Checklist

- Declare minimum and full verification commands in plan/evidence.
- Pin reused evidence to a commit/worktree path in implementation-brake and closeout.
- Preserve second stdio MCP proxy integration evidence for AC2.
- Avoid claiming HTTP MCP or maintenance scheduling in this slice.

## Implementation Tasks

- [ ] **DX-T1 (P1)** - Verification gate - Record exact minimum and full test commands.
  - Surfaced by: DX1
  - Files: `plans/002-pglite-operation-forwarding/plan.md`, `requirements/002-pglite-operation-forwarding/evidence.md`
  - Verify: evidence command output

- [ ] **DX-T2 (P1)** - Evidence pinning - Record verified commit/worktree path in implementation-brake and closeout.
  - Surfaced by: DX2
  - Files: `requirements/002-pglite-operation-forwarding/implementation-brake.md`, `requirements/002-pglite-operation-forwarding/closeout.md`
  - Verify: final artifacts cite commit/path

- [ ] **DX-T3 (P1)** - MCP integration evidence - Keep second stdio MCP proxy test in AC2 proof.
  - Surfaced by: DX3
  - Files: `requirements/002-pglite-operation-forwarding/evidence.md`
  - Verify: focused forwarding test output

## Unresolved Decisions

None requiring user input.

## Recommended Next Step

GO WITH CHANGES. Reconcile DX-T1 through DX-T3 before plan-eng-review.
