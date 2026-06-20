# Secondary Plan: PGLite Operation Forwarding

Primary plan: [plan.md](plan.md)
Codex proposed plan link: current goal execution turn
Plan id: `002-pglite-operation-forwarding`
Created: 2026-06-20
Last updated: 2026-06-20

## Why This Approach

- Chosen direction: Treat requirement 002 as a forwarding conformance slice that can reuse requirement 001 broker code only after current, path-specific evidence is revalidated and gaps are repaired.
- Why it fits the stated goal: The user wants PGLite callers to queue/serve without lock errors; that depends on caller behavior, not only on the existence of an owner socket.
- Rejected alternatives: Do not add a separate daemon requirement; do not weaken PGLite locks; do not expand to maintenance priority/yield in this slice.
- Assumptions that must hold: The requirement 001 task branch is still available; source/test edits happen in the isolated worktree; base user changes are preserved.
- Evidence still needed before implementation: Exact target HEAD, direct no-owner `search`, direct and brokered MCP source/auth parity, actor matrix coverage, and surface-level recovery evidence.

## RALPLAN-DR Summary

- Principles:
  - Preserve PGLite lock safety; forwarding is a local operation-level escape hatch, not a lock bypass.
  - Preserve current CLI and stdio MCP semantics for source scope, remote trust, privacy defaults, and error envelopes.
  - Prove each caller/owner path or explicitly justify same-code-path collapse.
  - Keep requirement 003 maintenance scheduling out of this slice.
- Decision drivers:
  - The most user-visible failure is falling through to PGLite lock wait while an owner is alive.
  - MCP parity is easy to regress because direct MCP dispatch and brokered MCP dispatch can diverge.
  - Recovery states must be distinguishable so operators can understand whether an owner is absent, unreachable, stale, or outcome-unknown.
- Viable options:
  - Revalidate-and-patch current broker implementation: smallest blast radius, uses requirement 001 code, but requires careful scenario coverage.
  - Build a new dedicated owner daemon: clearer ownership model, but violates the user constraint that no daemon is required and expands scope.
  - Route all operations through a long-lived process even without a detected owner: uniform flow, but risks changing no-owner CLI behavior and startup expectations.
- Alternatives rejected or invalidated:
  - Direct concurrent PGLite opens: rejected because it preserves the lock-timeout class of failures.
  - Network broker or HTTP MCP forwarding: rejected as out of scope and a larger trust boundary.
  - Raw SQL forwarding: rejected because the requirement is operation-level and local-only.
- Premortem for high-risk plans:
  - Failure scenario: brokered MCP omits `auth.allowedSources` and leaks or hides data differently than direct MCP. Mitigation: paired direct/brokered parity test.
  - Failure scenario: corrupt/ambiguous lock gets cleaned up and a second process opens PGLite unsafely. Mitigation: lock_safety_blocked no-cleanup/no-forward/no-direct-open evidence.
  - Failure scenario: an unreachable owner returns success-like output or waits on PGLite lock. Mitigation: CLI and MCP surface tests with explicit error/status assertions.
- Expanded test plan for high-risk plans:
  - Unit: IPC request/response, stale socket recovery, completion_unknown, closed client skip, local-only socket/path invariants.
  - Integration: CLI owner/caller and MCP owner/proxy forwarding for `query`, `search`, `think`.
  - E2E or browser/manual: none; this is CLI/MCP only.
  - Observability/operator evidence: user-facing failure copy must contain cause/action and not mask outcome-unknown as success.

## ADR

- Decision: Complete operation forwarding through local owner discovery plus filesystem IPC, with explicit CLI/MCP parity tests and safe failure semantics.
- Drivers: PGLite single-writer/single-process locking, existing requirement 001 broker implementation, user requirement that no daemon is mandatory, and MCP trust-boundary preservation.
- Alternatives considered: new daemon, direct multi-process PGLite, network broker, SQL proxy, evidence-only closeout.
- Why chosen: It keeps the smallest product surface while proving the exact concurrent caller paths users exercise.
- Consequences: Some tests will simulate owner locks/sockets and JSON-RPC MCP proxy behavior; closeout must be evidence-rich; future requirement 003 can focus on priority/yield without re-litigating operation forwarding.
- Follow-ups: Requirement 003 must handle `query/search/think` priority over `sync/embed/extract`; later slices may consider operational docs once behavior is complete.

## Implementation Guardrails

- Required implementation constraints:
  - PGLite-only forwarding; Postgres behavior remains unchanged.
  - Forwarding transport remains local filesystem socket, operation-level, and non-SQL.
  - Caller discovery happens before direct PGLite open for eligible operations when a live owner lock exists.
  - Brokered MCP calls must preserve direct stdio MCP semantics, including `remote=true`, source resolution, `auth.allowedSources`, takes-holder privacy defaults, and invalid-params error shape.
  - No-owner direct-open behavior remains for `query`, `search`, and `think`.
  - Ambiguous/corrupt locks must not be cleaned up or bypassed in this slice.
- Allowed implementation freedom:
  - Exact test helper names and fixture shape.
  - Whether broker dispatch adapter is moved or documented, as long as low-level IPC remains CLI/MCP agnostic.
  - Whether completion_unknown has a full CLI/MCP surface test or a justified lower-level proof accepted by implementation-brake.
- Likely mistake points:
  - Treating direct MCP evidence as brokered MCP evidence.
  - Forgetting base-only `GBRAIN_FEDERATED_READ` / `auth.allowedSources` behavior while implementing in the task branch.
  - Letting unreachable owners fall back to normal PGLite lock wait.
  - Claiming requirement 003 priority/yield behavior during requirement 002 closeout.
- Boundaries not to cross:
  - No network listener, no raw SQL transport, no mandatory daemon, no public syntax change, no weakening PGLite locks.
- Existing behavior that must not regress:
  - Existing `gbrain query "x"` command form, free-text `search`, `think`, stdio MCP tool envelopes, takes privacy, source routing, and no-owner CLI operation behavior.
- Decisions the implementer must not reopen:
  - Scope is PGLite only.
  - Maintenance operation scheduling belongs to requirement 003.
  - Requirement 001 evidence is useful but not automatically sufficient.
- Details that belong in `spec.md` or `contracts.md` instead: none introduced by this slice unless a new public contract is created.
- Executable contract compatibility findings: Plan-eng found brokered MCP must preserve active stdio MCP `GBRAIN_FEDERATED_READ` / `auth.allowedSources` behavior if present in the target.
- Required legal executable contract evidence: Tests or inspection proving direct and brokered MCP behavior match for source/auth and invalid params; typecheck after source edits.
- Drift checks against `plan.md` and the compressed Codex plan: Compare AC map, actor matrix, and verification commands before implementation-brake.

## Files To Inspect

- `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/src/cli.ts`: caller-side owner discovery and direct-open fallback.
- `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/src/mcp/server.ts`: stdio MCP direct dispatch and proxy server behavior.
- `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/src/core/pglite-operation-ipc.ts`: local IPC protocol, queueing, failure statuses, stale recovery.
- `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/src/core/pglite-lock.ts`: live/corrupt/unknown lock classification and safety behavior.
- `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/test/cli-pglite-operation-broker.test.ts`: CLI/MCP forwarding integration coverage.
- `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker/test/pglite-operation-ipc.test.ts`: IPC recovery and protocol coverage.
- `/Users/jeongmin/Documents/garrytan-gbrain/test/mcp-stdio-source-scope.test.ts`: base-only source-scope tests to port or preserve behavior from without modifying base user changes.

## Tests To Run Or Add

- Run `bun test test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/pglite-lock.test.ts --timeout 60000`: proves focused forwarding/lock behavior.
- Run `bun test test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts --timeout 60000 && bun run typecheck`: proves related regressions and types after edits.
- Add no-owner direct `search` coverage: proves AC3 for all three operations.
- Add actor matrix coverage or explicit same-path collapse evidence: proves CLI/MCP owner/caller combinations.
- Add paired direct/brokered MCP source/auth parity coverage: proves `GBRAIN_FEDERATED_READ` / `auth.allowedSources` survives forwarding.
- Add proxy invalid-params and owner-unreachable surface coverage: proves MCP error envelopes and CLI/MCP recovery semantics.
- Likely failure interpretation: lock timeout text indicates caller missed forwarding; unexpected success-like owner_unreachable output indicates unsafe UX; source/auth mismatch indicates MCP dispatch context drift.
- Minimum verification before handoff: full related command plus implementation-brake `[SHIP]`.

## Review Notes

- Decision brake: not separately triggered.
- Plan design review: not required; no UI.
- Plan UX review: `GO WITH CHANGES`; required exact no-owner search evidence and cause/action-oriented broker failure copy.
- Plan DevEx review: `GO WITH CHANGES`; required exact verification commands, worktree/commit pinning, and second stdio MCP proxy evidence.
- Plan engineering review: `GO WITH CHANGES`; required target pinning, no-owner search, MCP source/auth parity, proxy failures, adapter boundary, and narrowed verification trigger.
- Scenario review: `[SCENARIOS MISSING]`; required actor matrix, direct stdio MCP predecessor path, paired source/auth parity, surface recovery evidence, and stale/ambiguous lock separation.
- Open review risks: Completion_unknown may need a lower-level sufficiency rationale if deterministic surface simulation is too brittle; permission-denied/not-yet-bound socket coverage must be explicitly cited or accepted as residual risk.

## Plan Engineering Review Details

- Implementation approach reviewed: revalidate requirement 001 broker implementation, adding targeted source/test changes for missing evidence.
- Reuse or architecture constraints: reuse current broker; avoid a new daemon; preserve local IPC operation boundary.
- File, module, or ownership boundaries: `pglite-operation-ipc.ts` should remain low-level and handler-injected; the CLI/MCP dispatch adapter should not live as a generic core dependency unless deliberately documented.
- Interface, data, or migration risks: stdio MCP source/auth context can drift when brokered dispatch constructs a new context.
- Testing gaps: no-owner `search`, proxy-level failure envelope, owner-unreachable, direct/brokered source-auth parity.
- Sequencing or dependency risks: must pin exact worktree HEAD before evidence counts.
- Required changes before implementation: primary plan now includes all accepted obligations.

## Plan UX Review Details

- User-facing scope reviewed: CLI/MCP forwarding behavior and broker failure copy.
- First value or onboarding gaps: no daemon should be required; no-owner direct-open behavior must remain.
- Core task flow gaps: direct `search` no-owner evidence was missing.
- Interaction state coverage: owner unreachable and outcome unknown must not look like ordinary success.
- Recovery or re-entry risks: stale sockets should recover safely, while live-but-unreachable owners should report actionable failure.
- Trust, clarity, or accessibility concerns: failure messages should identify cause and next action.
- Locked UX decisions: no public syntax changes and no manual daemon requirement.
- Deferred UX items: maintenance operation priority/yield is deferred to requirement 003.
- Required changes before implementation: add direct no-owner `search` evidence and inspect failure copy during implementation-brake.

## Plan DevEx Review Details

- Developer-facing scope reviewed: CLI/MCP diagnostics, test commands, and handoff reproducibility.
- Target developer persona: local contributors and downstream agent operators diagnosing PGLite lock behavior.
- TTHW target or getting-started gaps: exact commands and worktree/commit pinning are needed to reproduce evidence.
- API/CLI/SDK ergonomics: existing command syntax must remain unchanged.
- Error quality or debugging gaps: second stdio MCP proxy errors need explicit envelopes.
- Documentation, upgrade, or tooling risks: docs must not imply requirement 003 behavior is complete.
- Locked DX decisions: full related suite plus typecheck after source/test/product-doc edits.
- Deferred DX items: broader release documentation belongs after sequence completion.
- Required changes before implementation: record exact commands, HEADs, and proxy evidence.

## Scenario Brake Details

- Scenarios covered: owner-forwarding happy paths, no-owner fallback, local IPC failure classes, MCP proxy behavior.
- Missing or weak scenarios: actor matrix, direct MCP predecessor path, brokered MCP source/auth mutation, second proxy invalid params, CLI/MCP owner_unreachable, completion_unknown surface proof, stale versus unreachable distinction.
- Edge cases: corrupt/unknown lock, absent socket, permission denied, not-yet-bound socket, owner death after accept, caller closes while queued.
- Recovery or rollback paths: stale socket can be removed/recreated; ambiguous lock must not be cleaned up; owner_unreachable must not fall back to PGLite lock wait.
- State, timing, or concurrency risks: accepted-but-timeout outcomes and live-lock/no-socket windows can produce misleading errors if collapsed.
- Acceptance evidence needed: named tests or closeout evidence for each AC and each scenario-brake obligation.
- Required scenario additions before implementation: reflected in primary plan steps 5-7.

## Conversation Details To Preserve

- User preferences: Korean conversation is fine; final system behavior matters more than theoretical discussion.
- User constraints: PGLite only; apply to gbrain; multiple callers should queue/serve without lock errors; query/search/think have priority over sync/embed/extract in the full sequence; `gbrain query "x"` and search/think command forms remain unchanged; owner daemon is optional, CLI may direct-open when no owner exists; at least five simultaneous MCP/CLI callers must avoid PGLite lock timeout in the final sequence.
- Examples or references: User specifically called out query/search/think MCP tool usage being blocked by pglock.
- Rejected ideas: mandatory owner daemon, network broker, direct concurrent PGLite open, scope expansion to maintenance scheduling inside requirement 002.
- Context likely to disappear during compression: base worktree has uncommitted stdio MCP source-scope/auth changes that must be preserved and, if relevant, ported into the task branch rather than reverted.

## Handoff Checklist

- [x] Primary plan, secondary plan, and compressed Codex plan agree.
- [x] Any conflict between this document, `plan.md`, and the compressed Codex plan has been reconciled before editing.
- [ ] Required files have been inspected before editing.
- [ ] Implementation stays inside the listed guardrails.
- [ ] Implementation details in this document are required constraints, not incidental coding choices.
- [ ] Required tests have been added or run.
- [ ] Review notes have been addressed or explicitly deferred.
- [ ] No new decisions were introduced without updating this document.
