# Requirement Decisions

## Decisions

### 2026-06-20 21:25 KST - Require real subprocess E2E evidence

- Decision: Requirement 004 cannot close on injected socket or fake-owner tests alone; it requires at least one real gbrain subprocess owner/proxy/CLI E2E test with five mixed callers.
- Rationale: Requirements 001-003 already cover the unit and command-level pieces. The sequence outcome needs proof that those pieces compose in real local process topology.
- Alternatives considered: Treat existing injected owner tests as sufficient; defer all real E2E proof to production readiness.
- Status: accepted in draft pending reviewer.

### 2026-06-20 21:25 KST - Treat docs contradiction cleanup as in scope

- Decision: Requirement 004 includes documentation alignment, especially replacing stale blanket guidance in `docs/architecture/serve-sync-concurrency.md`.
- Rationale: Operator-facing stale guidance can make the implemented broker/defer behavior effectively undiscoverable or misleading.
- Alternatives considered: Leave docs to production readiness; update only ENGINES.md.
- Status: accepted in draft pending reviewer.

### 2026-06-20 21:40 KST - Make recovery diagnostics a named-case matrix

- Decision: AC3/AC4 must explicitly require stale socket recovery, dead/stale lock recovery, live-owner-missing-socket `owner_unreachable`, accepted-request timeout `completion_unknown`, and corrupt/unknown lock `lock_safety_blocked`.
- Rationale: The reviewer correctly flagged that phrases like "as applicable" could let later work overclaim partial stale-owner evidence.
- Alternatives considered: Leave stale-owner recovery as a general acceptance criterion; defer diagnostic matrix to technical design.
- Status: accepted pending reviewer rerun.

### 2026-06-20 21:40 KST - Carry forward user-confirmed constraints as evidence

- Decision: Requirement 004 explicitly cites the accepted Requirement 001 product-boundary evidence instead of relying only on current-session prose.
- Rationale: PGLite-only scope, five mixed callers, unchanged command syntax, no mandatory daemon, and direct-open fallback are decision-bearing constraints that must survive every downstream gate.
- Alternatives considered: Treat sequence.md and current conversation as enough evidence.
- Status: accepted pending reviewer rerun.

### 2026-06-20 21:55 KST - Advance requirement 004 to research

- Decision: Requirement 004 is ready for research after reviewer rerun returned `SHIP`.
- Rationale: The reviewer confirmed the prior evidence-citation and stale-owner diagnostic specificity findings were resolved.
- Alternatives considered: Ask for another user clarification; run another reviewer pass.
- Status: accepted.

### 2026-06-20 22:35 KST - Tighten E2E from no-lock-text to positive owner/proxy proof

- Decision: The real subprocess E2E must prove PGLite config, live owner operation socket, proxy-only `tools/list`, seeded `query`/`search` marker results, all three MCP proxy operations, and post-teardown re-entry. `owner_unreachable`, `broker_timeout`, and `completion_unknown` are failures for AC1/AC2 E2E.
- Rationale: Plan reviewers found that accepting deterministic error envelopes or only checking absence of raw PGLite lock text could let the test pass without proving a live owner served proxy/CLI calls.
- Alternatives considered: Keep broad deterministic-error acceptance; rely on injected broker tests for proxy proof.
- Status: accepted after plan review reconciliation.

### 2026-06-20 22:35 KST - Broaden command-level recovery and diagnostic evidence

- Decision: Requirement 004 implementation must add or cite command-level evidence for no-owner direct-open, dead/stale-lock direct-open recovery, post-`completion_unknown` queue usability, startup-election interactive status, and privacy-safe diagnostics across params/source/auth/status paths.
- Rationale: Scenario reviewers separated lock primitive evidence from command-path behavior and identified privacy/status overclaim risk.
- Alternatives considered: Treat existing IPC/unit tests as sufficient for all AC3/AC4 rows.
- Status: accepted after scenario review reconciliation.

### 2026-06-20 22:35 KST - Include README and preserve status ownership in docs

- Decision: Documentation updates must include README troubleshooting language in addition to `docs/architecture/serve-sync-concurrency.md` and `docs/ENGINES.md`, and must keep broker/IPC statuses separate from CLI maintenance preflight statuses.
- Rationale: README contains known stale blanket guidance; status ownership prevents users from mistaking maintenance deferral for broker queue execution.
- Alternatives considered: Update only architecture and engine docs; use one undifferentiated status vocabulary.
- Status: accepted after DevEx and plan review reconciliation.
