---
name: goal-requirement-orchestrator
description: Split a broad initiative into ordered requirement-clarifier outputs, then execute each accepted slice through three main gates: Plan, Impl, and Review, with closeout and any required production-readiness lifecycle gate after Review.
---

# Goal Requirement Orchestrator

reference @./references/three_gate_contract.toml
reference @./references/sequence_template.md
reference @./references/sequence_progress_template.md
reference @./references/requirement_progress_template.md
reference @./references/decisions_template.md
reference @./references/evidence_template.md

Use this skill before `requirement-clarifier` when a broad idea, feature, or initiative should be clarified and implemented in multiple sequential requirement slices instead of one large requirements document.

This skill bootstraps the full requirement sequence up front, then advances one accepted requirement at a time. It owns ordering, state files, Worktree Execution Policy, Delegated Subagent Lifecycle, and completion bookkeeping. It must resist becoming a giant state machine for implementation details; `planning-orchestrator`, `impl-orchestrator`, `review-orchestrator`, and `closeout` own the detailed work inside their gates.

## Contract

The per-requirement execution surface is:

```text
Plan -> Impl -> Review
```

Requirement acceptance, source-obligation readiness, and coverage-ledger readiness are preconditions before the three gates. `closeout` and sequence-level `production-readiness` are lifecycle completion gates after Review, not fourth and fifth main execution gates.

The semantic source of truth for the gate surface is `references/three_gate_contract.toml`. This markdown is an operator-facing projection.

Before creating or resuming a sequence, classify the user's requested artifact class and the checklist's execution unit separately. Do not let a goal id, sequence title, or domain phrase such as "reference", "IA", "design", or a product name override the actual requested artifact. If the user asks to organize reference material, extract a clone-coding contract, create a design/input contract, or produce another prerequisite artifact, that artifact is its own goal-requirements sequence unless the active sequence's checklist items are also about producing that same artifact.

Adding, inserting, or rewriting a requirement path in an existing sequence changes that sequence's scope. Do not add a requirement to an existing sequence merely because it seems related, prerequisite-like, or useful for the named goal. If a new user request appears related to an existing sequence but has a different artifact class, execution unit, or deliverable, stop and ask for explicit user approval before inserting it into that sequence; otherwise create or select a separate sequence for the new request.

## Output

Create or update:

```text
goal-requirements/<id>/sequence.md
goal-requirements/<id>/progress.md
requirements/<requirement-id-1>/requirements.md
requirements/<requirement-id-1>/progress.md
requirements/<requirement-id-1>/decisions.md
requirements/<requirement-id-1>/evidence.md
```

Create every listed requirement document during orchestration bootstrap, including the production readiness requirement for MVP, beta, launch, or production-bound initiatives. Before any slice can move toward Plan, all listed requirement documents must exist, carry reviewer-backed acceptance state or a recorded blocker, and have `progress.md`, `decisions.md`, and `evidence.md`.

## File Shape

Keep `sequence.md` small. Include the overall goal, sequence rationale, sequence outcome, requirement paths with short slice outcomes, completion checkboxes, state-file rules, blocked rules, completion contract, context budget rules, the fixed `Plan -> Impl -> Review` execution surface, and final production readiness rule when applicable.

Use `references/sequence_template.md` as the example template.

Each sequence must include:

```markdown
## Sequence Outcome

- [ ] 1. `requirements/<requirement-id>/requirements.md` - outcome: <slice contribution>
```

## State Files

This sequence owns `goal-requirements/<id>/progress.md`.

Each listed requirement owns:

- `requirements/<requirement-id>/requirements.md`
- `requirements/<requirement-id>/research.md` when Plan decides research is required
- `requirements/<requirement-id>/technical-design.md` when Plan records `design_depth = "full_artifact_required"`
- `requirements/<requirement-id>/architecture.md` when system-level architecture design is required
- `requirements/<requirement-id>/progress.md`
- `requirements/<requirement-id>/decisions.md`
- `requirements/<requirement-id>/evidence.md`

Each listed requirement also gets Plan artifacts during `planning-orchestrator`:

- `plans/<plan-id>/plan.md`
- `plans/<plan-id>/secondary_plan.md`
- `plans/<plan-id>/plan_handoff.toml`
- `plans/<plan-id>/reviews/plan-design-review.md` when triggered
- `plans/<plan-id>/reviews/plan-ux-review.md` when triggered
- `plans/<plan-id>/reviews/plan-devex-review.md` when triggered
- `plans/<plan-id>/reviews/plan-eng-review.md` when triggered

Do not store goal state only in the conversation transcript.

## Authoritative State

At the start of every work slice, read this `sequence.md`, sequence-level `progress.md`, the current requirement's `requirements.md`, any existing research/design/architecture artifacts, `progress.md`, `decisions.md`, `evidence.md`, accepted Plan handoff artifacts, and current git status/diff. Treat these artifacts and the worktree as authoritative over conversation memory.

## Worktree Execution Policy

Goal-requirements implementation must run in an isolated task worktree. Do not use any root-worktree exception for implementation. Read-only investigation and planning may inspect the active checkout only after recording current cwd, git repository root, branch, HEAD SHA, and dirty status.

Before coding, bind the requirement slice to a task worktree path and run `scripts/init_worktree.sh <task-worktree-path>` from the repo that owns the sequence. The script must be idempotent, accept the task worktree path as its first argument, verify that the target is a git worktree for the same repository, reject the primary worktree, reject any target whose branch is `main`, require the target worktree's `scripts/verify` entrypoint, and avoid writing external automation runtime state into the repo.

The `goal-requirement-orchestrator` declares, records, and blocks on worktree state; it does not select, switch, merge, or delete worktrees. Missing worktree binding, branch `main`, primary-worktree target, stale dynamic state, failed setup, or unavailable isolated setup is a blocker before Impl.

For isolated task work where auto-merge is enabled by the accepted requirement and accepted Plan, record a Managed Repo Merge Disposition Checklist with one of `not_applicable`, `pending_pre_merge_gate`, `auto_merged`, or `blocked_escalated`.

## Delegated Subagent Lifecycle

Every companion subagent invocation in this sequence must have a hard deadline before waiting for the result. The default companion wait deadline is 10 minutes unless the invoked skill declares a shorter bound; broad context-loading may use up to 15 minutes.

A companion wait that reaches its hard deadline is `timeout`, not an invitation to keep waiting. Record the timeout, gate, subagent role, expected artifact, elapsed time, and next action or blocker in the current requirement's `progress.md` and `evidence.md`.

If a timeout or user interruption requires cancellation, request cancellation once and record `cancel_requested`. A failed or non-responsive cancellation is `cancel_failed`; record it in `progress.md` and `evidence.md` and stop treating that subagent as blocking evidence. Do not retry cancellation in a loop.

`close_agent` is best-effort cleanup only. It must use a short timeout, normally 30 seconds or less, and must not wait without a bounded timeout. If `close_agent` times out or fails, record `cancel_failed` or `cleanup_pending` in `progress.md` and `evidence.md`, then continue according to the gate's recorded blocker or fallback.

## Executable Subagent Lifecycle Policy

The executable source of truth for subagent fallback policy is `scripts/subagent_lifecycle.py`. Its `fallback_policies()` mapping is canonical for the gate-to-action contract; this markdown section is an operator-facing projection, not semantic authority.

Current projected fallback actions:

- `requirement-clarifier-post-draft-review`: `parent_fallback`
- `context-loading`: `parent_fallback`
- `plan-design-review`: `structured_blocked`
- `plan-ux-review`: `structured_blocked`
- `plan-devex-review`: `structured_blocked`
- `plan-eng-review`: `structured_blocked`
- `scenario-brake`: `structured_blocked`
- `visual-qa-hardening`: `structured_blocked`
- `ux-review`: `structured_blocked`
- `devex-review`: `structured_blocked`
- `implementation-brake`: `structured_blocked`
- `closeout`: `parent_fallback`

The helper validates structured lifecycle records, result shape and provenance, replacement fallback outcomes, partial companion sets, resume states, and cleanup-only close results. A successful `close_agent` result after no usable subagent result is cleanup evidence only; it cannot satisfy requirement, closeout, or goal acceptance without a valid fallback artifact, replacement result, structured blocker, or escalation record.

## Execution Gates

For each listed requirement, starting with the first unchecked item:

1. Use the listed `requirements/<requirement-id>/requirements.md` as the current requirement. If it is missing, stale, or not accepted for this slice, create or update it with `requirement-clarifier`.
2. Run the **Requirement Acceptance Gate** before `Plan`. File existence alone is insufficient; file existence alone is insufficient as acceptance evidence. The requirement must not be missing, stale, invalid, or unaccepted. Accepted state requires `Readiness Status: Ready` with `reviewer_status: SHIP`, or `Risky but usable` with explicit residual-risk acceptance and an allowed fallback status for ordinary non-production work. Production/launch/MVP-bound reviewer unavailability blocks acceptance; production/launch/MVP-bound slices cannot use ordinary fallback for acceptance. `FINDINGS`, `BLOCKED_INVALID`, `BLOCKED_UNAVAILABLE`, missing `reviewer_status`, `Blocked`, `stale_needs_recheck`, unresolved blocking Open Questions, or contradictory progress/evidence state means do not proceed to `Plan`; in the old gate vocabulary, do not proceed to research.
3. For source-obligation-triggered slices, acceptance also requires `source-inventory.yml`, `scope-reconciliation.yml`, `source_obligation_inventory_required`, source-obligation reviewer `SHIP`, or a structured source-obligation not-required decision. Run `scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/<requirement-id>` and record the result. Missing, stale, failed, or unavailable source-obligation state routes to `source-obligation-review`, `source-inventory-rebuild`, `scope-reconciliation-recheck`, or `coverage-ledger-repair`; source-obligation state cannot be satisfied by prose, progress text, reviewer praise, or closeout summaries.
4. Run `Plan` with `planning-orchestrator`. Plan owns `research`, `design_depth`, `plan-design-review`, `plan-ux-review`, `plan-devex-review`, `plan-eng-review`, `scenario-brake`, and `secondary-plan` as internal sub-decisions. `technical-design` is not a top-level gate; it is a Plan-internal full-artifact option invoked only when `design_depth = "full_artifact_required"`. Plan must emit `plans/<plan-id>/plan_handoff.toml`.
5. Run `Impl` with `impl-orchestrator` only after the Plan handoff is accepted. Impl must complete worktree preflight, run `scripts/init_worktree.sh <task-worktree-path>`, run `context-loading` when root AGENTS rules require it, then implement with `tdd-workflow`.
6. Run `Review` with `review-orchestrator` only after Impl produces implementation and verification evidence. Review runs lens-specific post-implementation conditional reviews when triggered: `visual-qa-hardening` for UI/layout/reference-fidelity work, `ux-review` for user-facing experience work with live user experience evidence, and `devex-review` for developer-facing experience docs/API/CLI/SDK/agent-tool work with live developer experience evidence. If multiple independent lenses trigger, Review may run them in parallel and then join their evidence. If no lens triggers, record a structured not-required reason. When any lens triggers, use subagent-based review when runtime supports subagents.
7. Still inside `Review`, run `implementation-brake` after triggered post-implementation reviews have passed or been recorded not required. `implementation-brake` must consume the triggered lens evidence, reconcile related review agent findings, and return `[SHIP]` before closeout.
8. After Review `[SHIP]`, resolve any required merge disposition and run `closeout`.
9. Mark the requirement checkbox complete only after closeout is complete.
10. When all listed requirements are checked complete, run `production-readiness` as the sequence-level final launch gate before marking the goal sequence complete if the sequence is MVP, beta, launch, or production-bound.

## State Update Rules

Update state files at gate boundaries, not only at closeout.

- At the start of each work slice, update sequence-level `progress.md` with the current requirement, current gate, status, and next action.
- Before and after `Plan`, record Plan status, `plans/<plan-id>/plan_handoff.toml`, `design_depth`, invoked subreviews, blockers, deferred items, and verification strategy.
- During `Plan`, record triggered `plan-design-review`, `plan-ux-review`, `plan-devex-review`, `plan-eng-review`, `scenario-brake`, and `secondary-plan` results as Plan-internal evidence.
- Before and after `Impl`, record worktree target, `scripts/init_worktree.sh <task-worktree-path>` result, context-loading result, TDD evidence, and verification commands.
- Before and after `Review`, record post-implementation lens decisions for `visual-qa-hardening`, `ux-review`, and `devex-review`; record whether triggered lenses ran in parallel or serial, the joined evidence set consumed by `implementation-brake`, and `[SHIP]` evidence.
- When verification or review evidence is produced, update the current requirement's `evidence.md`.
- When a material design, scope, ordering, constraint, or tradeoff decision is made, update the current requirement's `decisions.md`.
- When a companion subagent starts, completes, times out, is cancelled, fails cancellation, or leaves cleanup pending, update the current requirement's `progress.md` and `evidence.md` before moving to the next gate.

## Completion Contract

Mark a requirement complete only when `Plan`, `Impl`, and `Review` are complete, `implementation-brake` has returned `[SHIP]`, `closeout` is complete, all must-fix findings are closed, required verification has direct evidence in the requirement's `evidence.md`, and accepted criteria are satisfied.

For MVP, beta, launch, or production-bound sequences, the goal sequence is complete only after the final sequence-level `production-readiness` verdict is `ready` or `ready_with_external_handoff` with explicit human acceptance of the external handoff. Any unresolved `blocked_internal` item, launch-blocking `blocked_external` item, or unclassified readiness item blocks sequence completion. `deferred_non_goal` items must include the reason they are outside the accepted launch boundary.

## Blocked Rules

Do not skip gates or substitute guessed work. If a required gate, artifact, or acceptance criterion is unavailable or ambiguous, record the blocker in the relevant `progress.md` and stop or clarify unless the required artifact can be produced by the named gate.

Existing generated sequences are not automatically migrated. When resuming an older sequence that lacks the current `Plan -> Impl -> Review` contract, rehydrate against the current `Plan -> Impl -> Review` contract before `Impl` and record whether the old sequence is manually updated or compatibility-accepted for that slice.

Requirement recheck is an exception path. Do not silently reinterpret or patch accepted requirements; do not silently reinterpret or patch accepted requirements. When a requirement becomes `stale_needs_recheck`, old plan/review/conformance evidence, implementation-brake evidence, and closeout evidence must not be reused until the affected gates are rerun or explicitly revalidated. Mark prior state stale only when new evidence materially changes scope, verification, safety, design direction, decision boundaries, or handoff path.

For `Plan`, a skip is never valid for a goal-requirements implementation slice. For Plan-internal `research`, `design_depth`, `plan-design-review`, `plan-ux-review`, `plan-devex-review`, `plan-eng-review`, `scenario-brake`, and `secondary-plan` decisions, a not-required decision is valid only when the Plan handoff records a structured reason.

For `Impl`, missing accepted Plan handoff, failed worktree preflight, branch `main`, primary/base worktree target, missing `scripts/init_worktree.sh` result, stale dynamic state, or missing required `context-loading` blocks implementation.

For `Review`, unavailable required post-implementation review execution, missing lens-specific subagent evidence when `visual-qa-hardening`, `ux-review`, or `devex-review` is triggered, cleanup-only review output, missing implementation evidence, unresolved post-implementation blockers, or missing `implementation-brake` `[SHIP]` blocks closeout.

For source-obligation-triggered slices, missing, stale, failed, or unavailable source-obligation artifacts, source-obligation reviewer `SHIP`, structured source-obligation not-required decision, or readiness/closure validator evidence is a blocker. `source-inventory.yml`, `scope-reconciliation.yml`, `source_obligation_inventory_required`, `source-obligation-review`, and `scripts/coverage_ledger.py validate --mode readiness` must be recorded before implementation when the gate is required. Source-obligation state cannot be satisfied by prose or warning-only text.

For MVP, beta, launch, or production-bound sequences, `production-readiness` is mandatory before marking the goal sequence complete.

## Context Budget Rules

Keep state files concise. Summarize logs and verification output; preserve paths to full artifacts when useful. Avoid loading unrelated large files or full logs into context.

## Workflow

1. Run the sequence boundary check: classify the requested artifact class, the execution unit of each checklist item, and whether the request belongs in the current sequence or needs a separate sequence.
2. Identify the smallest sequence of requirement document paths needed for the broad initiative.
3. Add a concise overall goal, sequence rationale, and `Sequence Outcome`.
4. For each listed requirement, include a short slice outcome in the sequence checklist.
5. Create or update `goal-requirements/<id>/sequence.md` and `goal-requirements/<id>/progress.md`.
6. Create or update every listed `requirements/<requirement-id>/requirements.md` with `requirement-clarifier`; create each requirement's `progress.md`, `decisions.md`, and `evidence.md` state files during orchestration bootstrap.
7. Ensure each `requirement-clarifier` run invokes `requirement-clarifier-post-draft-reviewer` when the runtime allows subagents. Record structured `reviewer_status`, any fallback status, and unresolved findings in each requirement's state files before treating the sequence as accepted for later execution. If reviewer state becomes stale, rerun or revalidate the post-draft reviewer gate before `Plan`.
8. Add the fixed execution surface so later goal runs know the required `Plan`, `Impl`, `Review`, closeout, and production-readiness contract.
9. In the final response, tell the user the listed requirement paths, their reviewer-backed acceptance statuses or blockers, and that implementation still starts at state rehydration plus the `Plan` gate, not direct implementation.

## Constraints

- Do not create a combined requirements document.
- Do not mix different artifact classes in one sequence.
- Do not insert a new requirement into an existing sequence because it is adjacent, prerequisite-like, or related to the sequence name.
- For MVP, beta, launch, or production-bound initiatives, include and create a final production readiness requirement path.
- Each work slice focuses on exactly one requirement unless the current requirement is fully closed out and the only remaining action is selecting the next unchecked requirement.
- Read the authoritative state files and git status/diff at the start of every work slice.
- Update state at gate boundaries, not only at closeout.
- Apply root `AGENTS.md` context-loading rules before coding; if triggered, `context-loading` must run before `tdd-workflow`.
- Do not mark a requirement checkbox complete when only clarification, planning, coding, tests, experience review, or `implementation-brake` are done.
- After `closeout`, choose the next unchecked requirement from `sequence.md` and run the same gate order for that requirement.
- Do not mark an MVP, beta, launch, or production-bound sequence complete until `production-readiness` has produced an accepted sequence-level verdict.

## Anti-Patterns

- Treating a ready requirement as direct implementation permission.
- Adding a related-looking requirement to an existing sequence without user approval.
- Treating `Plan -> Impl -> Review` as permission to remove acceptance, source-obligation, coverage-ledger, worktree, implementation-brake, closeout, or production-readiness protections.
- Deleting `technical-design` or making full technical design impossible.
- Hiding Plan-internal design/review/scenario decisions in chat.
- Collapsing visual, UX, and DevEx post-implementation review into a generic review.
- Skipping Worktree Execution Policy or Delegated Subagent Lifecycle records because the path seems obvious.
- Marking a checkbox complete before implementation-brake `[SHIP]`, verification evidence, and closeout.
