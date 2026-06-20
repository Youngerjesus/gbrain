# Plan Engineering Review: PGLite Concurrency Verification

Status: GO WITH CHANGES
Date: 2026-06-20
Reviewed plan: `plans/004-pglite-concurrency-verification/plan.md`

## Grounding

- Requirement source: `requirements/004-pglite-concurrency-verification/requirements.md`
- Research/design state: research and technical design complete.
- Scope: verification/docs slice after requirements 001-003 implemented the owner broker, operation forwarding, and maintenance deferral.
- Scenario-brake routing: used, because this work depends on state, timing, recovery, and operator-facing diagnostics.
- Executable contract compatibility gate: triggered for the local IPC operation vocabulary and stdio MCP proxy tool surface. Code-owned contract allows only `query`, `search`, and `think` through the operation broker/proxy.

## Companion Findings Reconciled

### Accepted, Plan-Changing

- Add MCP proxy `search` to the real subprocess E2E. AC2 names `query`, `search`, and `think` through the second stdio server, so proxy coverage cannot stop at `query` and `think`.
- Prove positive proxy mode. The serial E2E must wait for owner lock/socket readiness and assert the second server's `tools/list` exposes only `query`, `search`, and `think`.
- Treat `owner_unreachable`, `broker_timeout`, and `completion_unknown` as failures for AC1/AC2 E2E. They remain valid recovery/status tests elsewhere, but they do not prove the owner served the mixed interactive workload.
- Include README in required docs updates. The current README troubleshooting section still contains blanket serve/sync guidance.
- Add or strengthen command-level dead/stale-lock direct-open recovery evidence. Lock primitive recovery alone is not a command-path proof.
- Broaden privacy-safe diagnostic evidence to request params, source/federated env sentinels, MCP auth material, and maintenance/status paths.
- Preserve status ownership in docs and closeout: broker/IPC statuses are distinct from CLI maintenance preflight statuses.

### Accepted, Verification-Changing

- Require every subprocess in the serial E2E to clear `DATABASE_URL` and `GBRAIN_DATABASE_URL`, and assert config `engine: pglite`.
- Require seeded marker evidence from `query`/`search` so empty data or keyless behavior cannot masquerade as a served result.
- Classify `think` evidence as route/no-lock/proxy-envelope evidence, not LLM answer-quality evidence.
- Add post-teardown re-entry evidence after the real owner/proxy test.
- Extend `completion_unknown` coverage with a later same-broker request after the handler releases.
- Add interactive startup-election status evidence or explicitly verify the current deterministic `owner_unreachable` behavior without raw lock timeout.

### Accepted But Separable

- Direct MCP owner-as-user-call concurrency does not need to be added to the expensive E2E if closeout does not claim it. Existing stdio lifecycle evidence can be cited narrowly.
- Maintenance deferral remains command-level regression evidence and must not be labeled as real subprocess interactive broker E2E.

### Rejected Or Narrowed

- Do not add a new architecture or mandatory daemon. The reviewed plan is minimum-sufficient once verification assertions are tightened.
- Do not require external APIs for `think`; missing-key/no-result behavior is acceptable only when the test separately proves live owner/proxy routing.

## Main Review

The plan is directionally sound and reuses the right code paths: existing lock/IPС/broker tests for named recovery statuses, and a new serial real-subprocess harness for integrated mixed caller proof. No architecture stop was found.

The original plan was too loose about success. A deterministic MCP error envelope is not enough to prove AC1/AC2 because a proxy can return `owner_unreachable` when the broker socket is absent. The reconciled plan now requires positive evidence: PGLite config, live owner socket, proxy-only tool list, seeded marker results, and explicit failure on broker reachability/timeouts in the E2E.

## Required Changes Before Implementation

- Update `technical-design.md` and `plan.md` with the accepted findings.
- Write the serial E2E with positive owner/proxy routing assertions.
- Strengthen command-level tests for stale-lock direct-open, post-timeout queue usability, startup race/status behavior, and privacy-safe diagnostics as needed.
- Update README, `docs/ENGINES.md`, and `docs/architecture/serve-sync-concurrency.md`.

## Verdict

GO WITH CHANGES. After the required changes are reflected in the plan/design artifacts, implementation may proceed.
