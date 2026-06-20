# PGLite All-Access Concurrency

## Goal

Make every PGLite-touching gbrain path behave predictably while a local `gbrain serve` owner is active, so users and agents never see raw PGLite lock/connect timeout failures as the product boundary.

## Sequence Rationale

The prior PGLite concurrency sequence intentionally covered `query`, `search`, and `think`, with maintenance paths deferred. This sequence widens the contract in two steps: first inventory and reproduce every remaining PGLite access path, then implement broker-success or typed guard-fail-fast behavior operation by operation.

## Sequence Outcome

All PGLite-touching CLI and MCP paths are classified and covered by deterministic concurrency behavior under a live local owner. Read/diagnostic paths either route through the owner and succeed, while mutating, schema-changing, file-touching, or heavy maintenance paths either serialize safely through the owner or return a typed, bounded, operator-actionable error instead of raw PGLite lock/connect timeout text.

## Requirement Sequence

- [x] 1. `requirements/006-pglite-access-path-inventory/requirements.md` - outcome: complete access-path inventory, operation classification, and a minimal failing/reproducing concurrency gauntlet for all PGLite-touching paths.
- [ ] 2. `requirements/007-pglite-broker-guard-implementation/requirements.md` - outcome: implement per-operation broker-success, serialized owner execution, or typed guard-fail-fast behavior according to the accepted inventory classification.
- [ ] 3. `requirements/008-pglite-all-access-concurrency-verification/requirements.md` - outcome: prove the named command matrix has zero raw PGLite lock/connect timeout failures across repeated concurrent attempts, with exit code, stderr, and error-shape evidence.
- [ ] 4. `requirements/009-pglite-all-access-concurrency-production-readiness/requirements.md` - outcome: sequence-level readiness verdict covering trust boundary preservation, operator recovery guidance, documentation, and launch handoff state.

## State Files

This sequence owns `goal-requirements/002-pglite-all-access-concurrency/progress.md`.

Each listed requirement owns:

- `requirements/<requirement-id>/research.md` when the `research` gate is required
- `requirements/<requirement-id>/technical-design.md` when the `technical-design` gate is required
- `requirements/<requirement-id>/architecture.md` when system-level architecture design is required
- `requirements/<requirement-id>/progress.md`
- `requirements/<requirement-id>/decisions.md`
- `requirements/<requirement-id>/evidence.md`

Each listed requirement also gets a plan artifact during its execution gates:

- `plans/<plan-id>/plan.md` with `Status: draft` before `plan-design-review` or `plan-eng-review`
- `plans/<plan-id>/reviews/plan-design-review.md` when the `plan-design-review` gate runs
- `plans/<plan-id>/reviews/plan-ux-review.md` when the `plan-ux-review` gate runs
- `plans/<plan-id>/reviews/plan-devex-review.md` when the `plan-devex-review` gate runs
- `plans/<plan-id>/reviews/plan-eng-review.md` when the `plan-eng-review` gate runs
- `plans/<plan-id>/secondary_plan.md` after `secondary-plan`

Create missing state files before starting that requirement. Do not store goal state only in the conversation transcript.

## Authoritative State

At the start of every work slice, read this `sequence.md`, sequence-level `progress.md`, the current requirement's `requirements.md`, any existing `research.md`, `technical-design.md`, optional `architecture.md`, `progress.md`, `decisions.md`, `evidence.md`, existing draft or accepted plan artifacts, and current git status/diff. Treat these artifacts and the worktree as authoritative over conversation memory.

## Worktree Execution Policy

Before implementation gates proceed, classify each requirement slice as `autopilot_root`, `managed_repo`, or `mixed` and record the result in the requirement progress state.

- `autopilot_root`: use the Autopilot root worktree. Root closeout may create a local commit, but root work is not auto-merged by this sequence policy.
- `managed_repo`: managed repo product source, product tests, or product docs changes require isolated task worktree execution. Managed repo read-only investigation and planning may use active main only after recording current cwd, git repository root, branch, HEAD SHA, and dirty status.
- `mixed`: split into separate root and managed repo requirement slices by default. If a mixed slice is kept as an exception, record the exception reason and separate root and managed worktree verification notes.

The `goal-requirement-orchestrator` declares, records, and blocks on worktree state; it does not select, switch, merge, or delete worktrees. Managed repo task worktree setup must use the repo-local `scripts/init_worktree.sh` entrypoint. If `scripts/init_worktree.sh` is missing and isolated managed repo work is required, create it before treating worktree setup as available.

## Delegated Subagent Lifecycle

Every companion subagent invocation in this sequence must have a hard deadline before waiting for the result. The default companion wait deadline is 10 minutes unless the invoked skill declares a shorter bound; broad context-loading may use up to 15 minutes. A companion wait that reaches its hard deadline is `timeout`, not an invitation to keep waiting. Record the timeout, gate, subagent role, expected artifact, elapsed time, and next action or blocker in the current requirement's `progress.md` and `evidence.md`.

`close_agent` is best-effort cleanup only. It must use a short timeout, normally 30 seconds or less, and must not wait without a bounded timeout. `close_agent` failure alone must not keep closeout or sequence re-entry waiting indefinitely after the gate result has already been recorded.

## Execution Gates

For each listed requirement, starting with the first unchecked item:

1. Use the listed `requirements/<requirement-id>/requirements.md` as the current requirement. If it is missing, stale, or not accepted for this slice, create or update it with `requirement-clarifier`. When `requirement-clarifier` creates or updates the file, it must invoke the `requirement-clarifier-post-draft-reviewer` gate when the runtime allows subagents.
2. Run the Requirement Acceptance Gate before any downstream gate. File existence alone is insufficient. Accepted state requires `Readiness Status: Ready` with `reviewer_status: SHIP`, or `Risky but usable` with explicit residual-risk acceptance and a recorded fallback status for ordinary non-production work.
3. A ready requirement document is not permission to implement directly.
4. Evaluate `research`; if decision-bearing technical unknowns, security/trust concerns, operation classification uncertainty, or architecture choices affect planning, write `requirements/<requirement-id>/research.md`. Otherwise record `Gate status: not_required` with reason in `progress.md`.
5. Evaluate `technical-design`; if module boundaries, state, invariants, error semantics, trust boundaries, queueing/serialization, or test harness design are needed, write `requirements/<requirement-id>/technical-design.md` and optional `architecture.md` when system-level architecture is required.
6. Treat `research`, `technical-design`, developer-facing `plan-devex-review`, `plan-eng-review`, and `scenario-brake` as hard gates when triggered. This sequence is developer-facing CLI/MCP work; `plan-devex-review` is expected unless a requirement records a specific not-required reason.
7. Create or update a requirement-based Draft Plan at `plans/<plan-id>/plan.md` with `Status: draft`.
8. Run conditional plan-stage reviews, then `plan-eng-review`, `scenario-brake`, and `secondary-plan` before implementation.
9. Before coding, complete the Worktree Preflight Checklist and run `context-loading` when required by `AGENTS.md`.
10. Implement with `tdd-workflow`.
11. Run `devex-review` after runnable CLI/MCP evidence exists when the slice changes developer-facing commands, diagnostics, docs, or agent-tool behavior.
12. After implementation and verification, run `implementation-brake`; close must-fix findings.
13. After `implementation-brake` returns `[SHIP]`, required verification is recorded, and any merge disposition is resolved, run `closeout`.
14. Mark the requirement checkbox complete only after closeout is complete.
15. When all listed requirements are checked complete, run `production-readiness` before marking the goal sequence complete.

## State Update Rules

Update state files at gate boundaries, not only at closeout.

- At the start of each work slice, update sequence-level `progress.md` with the current requirement, current gate, status, and next action.
- Before and after every gate, update the current requirement's `progress.md`.
- When verification or review evidence is produced, update the current requirement's `evidence.md`.
- When a material scope, ordering, constraint, trust-boundary, operation-classification, or tradeoff decision is made, update the current requirement's `decisions.md`.
- During closeout, reconcile the current requirement's state files, update sequence-level `progress.md`, then mark the requirement checkbox complete only if the completion contract is satisfied.
- During production readiness, record the final readiness verdict, internal blockers, external handoff items, deferred non-goals, and next action in sequence-level `progress.md` and the readiness requirement's state files.

## Completion Contract

Mark a requirement complete only when `implementation-brake` has returned `[SHIP]`, closeout is complete, all must-fix findings are closed, required review gates have passed or been explicitly recorded as not required, required verification has direct evidence in the requirement's `evidence.md`, and the accepted criteria are satisfied.

The goal sequence is complete only after the final `production-readiness` verdict is `ready` or `ready_with_external_handoff` with explicit human acceptance of the external handoff.

## Blocked Rules

Do not skip gates or substitute guessed work. If a required gate, artifact, or acceptance criterion is unavailable or ambiguous, record the blocker in the relevant `progress.md` and stop or clarify unless the required artifact can be produced by the named gate.

For this sequence, any proposed behavior that broadens remote-MCP authority, bypasses `OperationContext.remote`, weakens filesystem confinement, deletes live PGLite locks, introduces network broker exposure, or changes public command syntax without user confirmation is blocked.

## Context Budget Rules

Keep state files concise. Summarize logs and verification output; preserve paths to full artifacts when useful. Avoid loading unrelated large files or full logs into context.
