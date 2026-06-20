---
plan_id: 002-pglite-operation-forwarding
requirement_id: 002-pglite-operation-forwarding
status: accepted
created_at: 2026-06-20 16:50 KST
last_updated_at: 2026-06-20 17:35 KST
---

# Primary Plan: PGLite Operation Forwarding

Plan id: `002-pglite-operation-forwarding`
Status: accepted
Created: 2026-06-20
Last updated: 2026-06-20
Secondary plan: [secondary_plan.md](secondary_plan.md)
Requirements source: [requirements.md](../../requirements/002-pglite-operation-forwarding/requirements.md)

## Goal Objective

- Codex goal objective: Complete requirement 002 by proving and, where needed, repairing local owner-forwarding for PGLite `query`, `search`, and `think` across CLI and stdio MCP callers.
- User-visible outcome: Multiple local CLI/MCP callers can invoke `query`, `search`, and `think` while a PGLite owner is alive without hitting PGLite lock timeout, while no-owner direct-open behavior still works.
- Why this is the right unit of work: Requirement 001 established the broker boundary; this slice locks the operation-forwarding contract and evidence before requirement 003 handles maintenance priority/yield.
- Goal completion standard: AC1-AC7 are mapped to current evidence, missing tests or code are added in the isolated task worktree, review gates are reconciled, implementation-brake returns `[SHIP]`, closeout is written, sequence item 2 is checked, and changes are committed.

## Scope

- In scope: PGLite-only owner discovery and local IPC forwarding for `query`, `search`, and `think`; CLI direct-open fallback; stdio MCP proxy behavior; source/auth/error parity; deterministic safe failures; AC-to-evidence mapping.
- Out of scope: Real `sync`, `embed`, or `extract` priority/yield; HTTP MCP forwarding; network-accessible brokers; public CLI syntax changes; weakening or bypassing PGLite file locks.
- Non-goals: Claiming requirement 003 maintenance scheduling, adding a mandatory daemon, or treating stale requirement 001 evidence as sufficient without revalidation.
- Assumptions: Requirement 001 task worktree `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker` and commit `d50dc701` are available; base worktree user changes are not to be reverted; implementation source/test/doc edits happen only in the isolated task worktree.
- Dependencies or required inputs: Current requirement document, plan reviews, scenario-brake results, requirement 001 implementation, local Bun test environment.

## Execution Plan

1. Target preflight: confirm the isolated implementation worktree path, branch, exact HEAD, dirty status, and that it contains requirement 001 broker code.
2. Drift reconciliation: inspect base-only stdio MCP source-scope/auth changes and port behavior needed for brokered MCP parity into the task worktree without touching or reverting base user changes.
3. Boundary cleanup: relocate the broker dispatch adapter out of low-level `core` or document the adapter boundary while keeping `pglite-operation-ipc.ts` handler-injected and CLI/MCP-agnostic.
4. Direct-open evidence: add exact no-owner direct-open evidence for `search`, preserving existing no-owner `query` and `think` behavior.
5. Actor matrix evidence: prove or explicitly same-path-collapse CLI owner -> CLI caller, CLI owner -> MCP proxy, MCP owner -> CLI caller, and MCP owner -> MCP proxy.
6. MCP parity evidence: add direct stdio MCP no-owner predecessor evidence and paired direct-MCP versus brokered-MCP evidence for `GBRAIN_FEDERATED_READ` / `auth.allowedSources`.
7. Failure-state evidence: add second stdio MCP proxy invalid-params/failure-envelope proof; add CLI and MCP `owner_unreachable` surface proof; prove or justify `completion_unknown`; prove `lock_safety_blocked` does not clean up, forward, or direct-open; keep stale-socket recovery distinct.
8. Verification: run the focused and full related commands required by this plan after any source/test/product-doc edits.
9. Implementation-brake: run conformance review against AC1-AC7, secondary-plan guardrails, and current test output; reconcile any non-`[SHIP]` findings.
10. Closeout and sequence update: write closeout evidence, update requirement progress/evidence and sequence item 2, sync planning artifacts into the task worktree, and commit intended changes.

## Acceptance Evidence

- Required artifact changes: updated source/tests as needed in the task worktree; `requirements/002-pglite-operation-forwarding/closeout.md`; updated progress/evidence; checked sequence item 2; committed task branch.
- Required behavior or state changes: `query`, `search`, and `think` forward to a live PGLite owner for CLI and stdio MCP caller paths; no-owner direct-open behavior remains; brokered MCP preserves direct MCP source/auth/error semantics; safe failures are deterministic.
- Required tests or verification commands:
  ```bash
  bun test test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/pglite-lock.test.ts --timeout 60000
  ```
  ```bash
  bun test test/pglite-lock.test.ts test/pglite-operation-ipc.test.ts test/cli-pglite-operation-broker.test.ts test/serve-stdio-lifecycle.test.ts test/cli-search-dispatch.test.ts test/context/resolve-ipc.test.ts test/takes-mcp-allowlist.serial.test.ts --timeout 60000 && bun run typecheck
  ```
- Evidence that is insufficient by itself: passing requirement 001 tests without current HEAD pinning; IPC unit tests without CLI/MCP surface coverage for required paths; no-owner `query`/`think` evidence used as a substitute for `search`; direct MCP behavior used as a substitute for brokered MCP parity.
- Manual checks, if any: inspect user-facing broker failure copy for cause/action clarity and confirm docs/closeout do not claim maintenance priority/yield behavior.

## Goal Completion Audit

- Requirements evidence map:
  - AC1 -> CLI tests for owner discovery before direct PGLite open for `query`, `search`, and `think`, with no PGLite lock timeout text.
  - AC2 -> second stdio MCP proxy tests listing/calling `query`, `search`, and `think`, plus actor matrix coverage.
  - AC3 -> no-owner direct-open smoke tests for all three operations, including exact `search` evidence.
  - AC4 -> caller `cwd`/source tests, direct versus brokered MCP source/auth parity, takes privacy defaults, and invalid-params envelope tests.
  - AC5 -> code inspection or unit tests showing local filesystem socket, newline-delimited operation requests, no raw SQL, no network listener.
  - AC6 -> absent owner socket, owner-unreachable CLI/MCP surfaces, completion_unknown evidence or justified lower-level sufficiency, stale recovery, lock_safety_blocked, and closed client skip.
  - AC7 -> closeout AC map pinned to exact task worktree HEAD and re-run command output.
- Plan step evidence map:
  - Steps 1-3 -> recorded worktree/HEAD and source boundary diff.
  - Steps 4-7 -> named tests and AC map entries.
  - Steps 8-10 -> command output, implementation-brake `[SHIP]`, closeout, sequence update, commit.
- Secondary guardrail evidence map:
  - Preserve source/auth parity -> paired direct/brokered MCP evidence.
  - Do not weaken locks -> lock_safety_blocked and corrupt/unknown lock tests.
  - Keep forwarding local-only -> IPC transport inspection evidence.
  - Keep maintenance scheduling out of scope -> closeout non-goal statement.
- Review gate evidence map for gates used or requested:
  - requirement-clarifier -> reviewer `SHIP` recorded.
  - research -> AC-to-current-code map recorded.
  - plan-ux-review -> no-owner search and failure-copy obligations addressed.
  - plan-devex-review -> exact verification and second stdio MCP evidence addressed.
  - plan-eng-review -> target pinning, MCP parity, failure evidence, adapter boundary addressed.
  - scenario-brake -> actor matrix and recovery scenarios addressed.
  - implementation-brake -> `[SHIP]` required before closeout.
  - Unused gates: plan-design-review not applicable because this requirement has no UI.
- Deliverables evidence map:
  - Product/test changes -> committed task worktree diff.
  - Planning/closeout artifacts -> requirement-local files in base and task worktree.
  - Sequence state -> sequence item 2 checked.
- Verification evidence map:
  - Focused command -> forwarding and lock tests pass.
  - Full related command -> forwarding regressions and typecheck pass after source/test/product-doc edits.
- Insufficient completion signals:
  - A green focused suite alone without AC map and review closeout.
  - A committed diff without sequence/progress updates.
  - Brokered CLI evidence without MCP source/auth parity.
- Residual risk accepted for this goal: If deterministic surface simulation for `completion_unknown` proves impractical, lower-level IPC evidence may be accepted only with an explicit closeout rationale and no contradiction from implementation-brake.

## Context Sources

- Files or docs to read first:
  - `requirements/002-pglite-operation-forwarding/requirements.md`
  - `requirements/002-pglite-operation-forwarding/research.md`
  - `requirements/002-pglite-operation-forwarding/plan-eng-review.md`
  - `requirements/002-pglite-operation-forwarding/scenario-brake.md`
  - `plans/002-pglite-operation-forwarding/secondary_plan.md`
- Related requirements/spec/contracts:
  - `requirements/001-pglite-owner-broker/closeout.md`
  - `goal-requirements/001-pglite-concurrent-access/sequence.md`
- Related local planning or review artifacts:
  - `requirements/002-pglite-operation-forwarding/plan-ux-review.md`
  - `requirements/002-pglite-operation-forwarding/plan-devex-review.md`
  - `requirements/002-pglite-operation-forwarding/evidence.md`
  - `requirements/002-pglite-operation-forwarding/progress.md`
- External references, if any: none.

## Continuation And Stop Rules

- Continue while: work maps to AC1-AC7, review obligations, or required verification/closeout.
- Ask the user when: expanding forwarding beyond `query`, `search`, and `think`; adding network-facing broker behavior; changing public CLI syntax; merging this slice with maintenance scheduling.
- Stop without changing files when: a proposed fix would weaken PGLite lock safety, expose raw SQL/network forwarding, or require destructive git operations.
- Mark the goal blocked only when: the same blocking condition repeats for the required goal turns and meaningful progress is impossible without user input or external state change.
- Mark the goal complete only when: all sequence requirements are complete, not merely when requirement 002 is committed.

## Drift Checks

- The final Codex proposed plan agrees with this primary plan.
- The secondary plan's guardrails do not contradict this primary plan.
- Requirements/spec/contracts, when present, remain the product behavior source of truth.
- Any implementation-changing Plan Engineer Review or Scenario Brake decision has been reflected here.

## Goal Handoff Checklist

- [x] Objective is concrete enough for `create_goal`.
- [x] Execution steps are ordered and independently checkable.
- [x] Acceptance evidence is explicit.
- [x] Verification commands are listed.
- [x] Goal completion audit maps requirements, plan steps, guardrails, review gates, deliverables, and verification to evidence.
- [x] Stop, escalation, blocked, and completion rules are clear.
- [x] Secondary plan has been read and reconciled.
- [x] No hidden chat-only requirement is needed to execute this goal.
