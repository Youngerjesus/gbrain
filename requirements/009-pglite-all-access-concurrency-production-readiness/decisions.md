# 009 Decisions

## D1: Launch Boundary Is Local PGLite CLI/MCP Readiness

- Status: accepted
- Date: 2026-06-21
- Decision: Treat production readiness as readiness for local gbrain PGLite CLI, `gbrain call`, stdio MCP, HTTP MCP owner-server topology, owner startup, and maintenance behavior.
- Reason: The accepted sequence is about local PGLite all-access concurrency, not hosted service deployment.
- Consequence: DNS, hosted infrastructure, OAuth apps, payment/email, push, PR, merge, and release are out of scope unless the user asks for them.

## D2: Coverage Ledger Is Required

- Status: accepted
- Date: 2026-06-21
- Decision: Requirement 009 uses a coverage decision and coverage ledger.
- Reason: It is production-bound, spans multiple prior requirements, and has ten acceptance criteria covering launch, trust, diagnostics, data safety, privacy, verification freshness, and handoff state.
- Consequence: Readiness cannot complete until the ledger validates and rows are reconciled with evidence.

## D3: Fresh Readiness Evidence Is Required

- Status: accepted
- Date: 2026-06-21
- Decision: Prior implementation-brake `[SHIP]` decisions are necessary inputs but not sufficient for final readiness.
- Reason: Production-readiness evaluates assembled launch safety, operator recovery, external dependencies, privacy, and state reconciliation across the full sequence.
- Consequence: Requirement 009 must rerun or cite fresh validators/tests before issuing the final verdict.

## D4: Task Worktree Branch Is Authoritative For This Sequence Run

- Status: accepted
- Date: 2026-06-21
- Decision: Use branch `codex/008-pglite-all-access-concurrency-verification` in `/Users/jeongmin/Documents/garrytan-gbrain-008-pglite-all-access-concurrency-verification` as the authoritative sequence state.
- Reason: Base `master` is behind and still contains stale/uncommitted artifacts from earlier sequence work.
- Consequence: Merging to `master`, pushing, opening a PR, or releasing remains outside this readiness requirement.

## D5: Final Readiness Verdict Is Production Ready

- Status: accepted
- Date: 2026-06-21
- Decision: Record final verdict `[PRODUCTION READY]` for the accepted local PGLite CLI/MCP launch boundary.
- Reason: Prior slices have closeout evidence, fresh validators and regression tests pass, no raw PGLite timeout appears in all-access evidence, trust-boundary and heavy-maintenance paths are covered, and no internal or external launch blocker remains.
- Consequence: The sequence may be marked complete after final ledger closure and sequence state reconciliation.
