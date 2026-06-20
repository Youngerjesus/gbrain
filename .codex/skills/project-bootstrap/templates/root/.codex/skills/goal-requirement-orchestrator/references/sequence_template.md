# Goal Requirement Sequence Template

Use this template for:

```text
goal-requirements/<id>/sequence.md
```

Keep the generated sequence file minimal. The sequence outcome, requirement checklist with short slice outcomes, state rules, execution gates, and any final production readiness gate are the contract. The first requirement document is created by orchestration bootstrap; later requirement documents stay deferred until their slice starts.

```markdown
# <Initiative Name>

## Goal

<One or two sentences describing the overall objective this sequence should complete.>

## Sequence Rationale

<One or two sentences explaining how the listed requirements connect and why they run in this order.>

## Sequence Outcome

<One or two sentences describing the product, artifact, behavior, launch state, or operational capability that must exist after all listed requirements and any required production readiness gate are complete.>

## Requirement Sequence

- [ ] 1. `requirements/<requirement-id-1>/requirements.md` - outcome: <first slice contribution>
- [ ] 2. `requirements/<requirement-id-2>/requirements.md` - outcome: <later slice contribution; create this requirements file only when this slice starts>
- [ ] 3. `requirements/<requirement-id-3>/requirements.md` - outcome: <later slice contribution; create this requirements file only when this slice starts>

For MVP, beta, launch, or production-bound initiatives, reserve a final readiness slice:

- [ ] N. `requirements/<goal-id>-production-readiness/requirements.md` - outcome: <sequence-level readiness verdict and launch handoff state>

## State Files

This sequence owns a sequence-level state file next to this file:

- `progress.md`

Each listed requirement owns its own runtime state files:

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

- `autopilot_root`: use the Autopilot root worktree. Root closeout may create a local commit, but root work must not be auto-merged by this sequence policy.
- `managed_repo`: managed repo product source, product tests, or product docs changes require isolated task worktree execution. Managed repo read-only investigation and planning may use active main only after recording current cwd, git repository root, branch, HEAD SHA, and dirty status.
- `mixed`: split into separate root and managed repo requirement slices by default. If a mixed slice is kept as an exception, record the exception reason and separate root and managed worktree verification notes.

The `goal-requirement-orchestrator` declares, records, and blocks on worktree state; it does not select, switch, merge, or delete worktrees. Managed repo task worktree setup must use the repo-local `scripts/init_worktree.sh` entrypoint. If `scripts/init_worktree.sh` is missing and isolated managed repo work is required, create it before treating worktree setup as available. The script must be idempotent, accept the task worktree path as its first argument, run the repo's required bootstrap behavior, and avoid writing external automation runtime state into the repo.

Record dynamic worktree values in the requirement's `progress.md` or `evidence.md`, not in static `sequence.md` policy text. A mismatch between intended target and current cwd or git repository root is a blocker before implementation. Managed repo product modification in the base/main worktree is a blocker before implementation. Missing worktree binding or unavailable isolated setup is a blocker or handoff requirement, not a silent bypass.

Revalidate target classification and the Worktree Preflight Checklist on resume, before implementation, and whenever the intended change set changes. A slice that starts as read-only planning or root-only work but discovers managed repo product source, product tests, product docs, or mixed root-plus-managed changes must stop before implementation, reclassify, rerun preflight, and split or require isolated managed execution as applicable.

For isolated managed repo work where auto-merge is enabled by the accepted requirement and accepted plan, record a Managed Repo Merge Disposition Checklist with one of `not_applicable`, `pending_pre_merge_gate`, `auto_merged`, or `blocked_escalated`. Auto-merge is allowed only after the pre-merge gate passes. The standard green gate requires accepted requirement and accepted plan state, implementation verification, `implementation-brake` returned `[SHIP]`, managed repo `scripts/verify` passed when present, clean task worktree except intended tracked outputs, and clean/up-to-date base worktree. The conditional live verification gate applies to UI, live/model, prompt/schema contract, multi-agent handoff, repair/evaluator/generator loop, and live output parsing changes.

Immediately before merge, recheck the verified base or target SHA and block/escalate if it changed after the pre-merge gate. Record `auto_merged` only after merge completion and post-merge verification pass. Post-merge verification records target branch, merged commit or resulting target SHA, command(s), and result. If post-merge verification fails after the target branch was mutated, keep disposition `blocked_escalated` and record the mutated target SHA and failing command/result.

On merge conflict, dirty/stale base, invalid target, failed pre-merge verification, failed post-merge verification, ambiguous worktree state, or missing live gate, stop and escalate. Record the cause, affected repo/worktree, command/result, relevant SHA, conflicted files when available, whether manual cleanup required, and that no automatic recovery performed. Do not perform automatic retry, automatic rebase, automatic repair, or automatic revert. On re-entry, do not repeat a merge when prior disposition is `auto_merged`; verify the recorded target SHA/disposition first. Do not proceed from `blocked_escalated` without human resolution.

## Delegated Subagent Lifecycle

Every companion subagent invocation in this sequence must have a hard deadline before waiting for the result. The default companion wait deadline is 10 minutes unless the invoked skill declares a shorter bound; broad context-loading may use up to 15 minutes. A companion wait that reaches its hard deadline is `timeout`, not an invitation to keep waiting. Record the timeout, gate, subagent role, expected artifact, elapsed time, and next action or blocker in the current requirement's `progress.md` and `evidence.md`.

If a timeout or user interruption requires cancellation, request cancellation once and record `cancel_requested`. A failed or non-responsive cancellation is `cancel_failed`; record it in `progress.md` and `evidence.md` and stop treating that subagent as blocking evidence. Do not retry cancellation in a loop.

`close_agent` is best-effort cleanup only. It must use a short timeout, normally 30 seconds or less, and must not wait without a bounded timeout. If `close_agent` times out or fails, record `cancel_failed` or `cleanup_pending` in `progress.md` and `evidence.md`, then continue according to the gate's recorded blocker or fallback. `close_agent` failure alone must not keep `closeout` or sequence re-entry waiting indefinitely after the gate result has already been recorded.

On resume or re-entry, read `progress.md` and `evidence.md` before launching another companion. A prior `timeout`, `cancel_failed`, or `cleanup_pending` entry must be reconciled as stale cleanup state, explicit blocker, or accepted fallback before any duplicate companion is spawned.

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

For `requirement-clarifier-post-draft-review`, `select_fallback_policy()` upgrades reviewer unavailability to `structured_blocked` when the requirement is production-bound, launch-bound, MVP-bound, irreversible, or safety-critical. Ordinary non-production fallback still requires explicit `reviewer_fallback_status: FALLBACK_SELF_REVIEW_USED`; it is never recorded as reviewer `SHIP`.

The helper validates structured lifecycle records, result shape and provenance, replacement fallback outcomes, partial companion sets, resume states, and cleanup-only close results. A successful `close_agent` result after no usable subagent result is cleanup evidence only; it cannot satisfy requirement, closeout, or goal acceptance without a valid fallback artifact, replacement result, structured blocker, or escalation record.

## Execution Gates

For each listed requirement, starting with the first unchecked item:

1. Use the listed `requirements/<requirement-id>/requirements.md` as the current requirement. If it is missing, stale, or not accepted for this slice, create or update it with `requirement-clarifier`. When `requirement-clarifier` creates or updates the file, it must invoke the `requirement-clarifier-post-draft-reviewer` gate when the runtime allows subagents, and must record structured `reviewer_status` and any allowed `reviewer_fallback_status` before the requirement can be treated as accepted.
2. Run the **Requirement Acceptance Gate** before any downstream gate. File existence alone is insufficient; file existence alone is insufficient as acceptance evidence. The requirement must be present, current for this slice, and not missing, stale, invalid, or unaccepted. Accepted state requires `Readiness Status: Ready` with `reviewer_status: SHIP`, or `Risky but usable` with explicit residual-risk acceptance and a recorded fallback status for ordinary non-production work. `FINDINGS`, `BLOCKED_INVALID`, `BLOCKED_UNAVAILABLE`, or missing `reviewer_status` do not satisfy `Ready`. Production/launch/MVP-bound reviewer unavailability blocks acceptance; production/launch/MVP-bound reviewer unavailability cannot proceed through ordinary fallback. Invalid reviewer status, missing fallback status after reviewer unavailability, `Blocked`, `stale_needs_recheck`, unresolved blocking Open Questions, or contradictory progress/evidence state means do not proceed to research, design, planning, or implementation; update the requirement with `requirement-clarifier`, rerun or revalidate the post-draft reviewer gate, or stop with a recorded blocker.
3. A ready requirement document is still not permission to implement directly.
4. Evaluate the `research` gate. If decision-bearing technical unknowns, external dependencies, temporally unstable facts, platform/API/library choices, domain constraints, security/compliance concerns, model behavior, pricing/cost, or architecture pattern choices affect implementation planning, run `research` and write `requirements/<requirement-id>/research.md`. If research is not required, record `Gate status: not_required` and the reason in `progress.md`.
5. Evaluate the `technical-design` gate. If module boundaries, architecture boundaries, interactions, state, invariants, error handling, edge cases, testability, or cross-layer handoff decisions are needed before planning, run `technical-design` and write `requirements/<requirement-id>/technical-design.md`. Write `requirements/<requirement-id>/architecture.md` only when system-level architecture design is required; otherwise record the architecture not-required rationale.
6. Treat `research`, `technical-design`, UI-bearing `plan-design-review`, user-facing experience `plan-ux-review`, and developer-facing experience `plan-devex-review` as conditional hard gates. When a trigger applies, missing, stale, contradictory, unresolved-blocking, or approval-pending gate output blocks progress to `plan-eng-review`.
7. Artifact existence alone is insufficient. Gate completion requires coherent `progress.md`, artifact path, `evidence.md`, material `decisions.md` reference, unresolved-item classification, and no pending requirement-impact approval.
8. Create or update a requirement-based Draft Plan artifact at `plans/<plan-id>/plan.md` with `Status: draft`. The Draft Plan must use the `secondary-plan` primary plan template shape, fill the required primary plan sections with task-specific content, and be substantive enough for `plan-design-review`, `plan-eng-review`, and `scenario-brake`; it is not permission to implement.
9. If the current slice is UI-bearing, run `plan-design-review` after the Draft Plan is created and before `plan-eng-review`, using the current requirement, research/design gate state, Draft Plan, and existing design/code patterns as inputs. This gate must review information architecture, interaction states, user journey, design specificity, design-system alignment, responsive/accessibility coverage, and unresolved UI decisions. Write the gate result to `plans/<plan-id>/reviews/plan-design-review.md`, then record the review outcome, locked design decisions, deferred items, artifact path, and any blockers in the current requirement's `progress.md`, `decisions.md`, and `evidence.md`. If the slice is not UI-bearing, record `Gate status: not_required` with the reason before `plan-eng-review`.
10. If the current slice is user-facing experience work, run `plan-ux-review` after the Draft Plan is created and before `plan-eng-review`, using the current requirement, research/design gate state, Draft Plan, existing UX patterns, and target user/job evidence as inputs. This gate must review first value, core task flow, information architecture, interaction states, recovery/re-entry, trust/clarity, accessibility, and UX measurement. Write the gate result to `plans/<plan-id>/reviews/plan-ux-review.md`, then record the review outcome, locked UX decisions, deferred items, artifact path, blockers, and whether the Draft Plan needs reconciliation before `plan-eng-review`. If the slice is not user-facing experience work, record `Gate status: not_required` with the reason before `plan-eng-review`.
11. If the current slice is developer-facing experience work, run `plan-devex-review` after the Draft Plan is created and before `plan-eng-review`, using the current requirement, research/design gate state, Draft Plan, existing docs/API/CLI/SDK patterns, and target developer persona evidence as inputs. This gate must review time to hello world, getting started, API/CLI/SDK ergonomics, error quality, documentation, upgrade path, developer tooling, ecosystem, and DX measurement. Write the gate result to `plans/<plan-id>/reviews/plan-devex-review.md`, then record the review outcome, locked DX decisions, deferred items, artifact path, blockers, and whether the Draft Plan needs reconciliation before `plan-eng-review`. If the slice is not developer-facing work, record `Gate status: not_required` with the reason before `plan-eng-review`.
12. For this requirement, run the remaining pre-implementation review gates in order: `plan-eng-review`, then `scenario-brake`, using the current requirement, research/design gate state, any `plans/<plan-id>/reviews/plan-design-review.md`, `plans/<plan-id>/reviews/plan-ux-review.md`, or `plans/<plan-id>/reviews/plan-devex-review.md` outcome, and Draft Plan as inputs. Write the `plan-eng-review` result to `plans/<plan-id>/reviews/plan-eng-review.md`. `plan-eng-review` and `scenario-brake` must invoke their relevant read-only companion subagents according to each skill's companion routing contract when the runtime allows subagents. If delegation is unavailable, record the explicit fallback or blocker in the current requirement's `progress.md`.
13. Run `secondary-plan` to reconcile review findings from `plans/<plan-id>/reviews/plan-design-review.md`, `plans/<plan-id>/reviews/plan-ux-review.md`, `plans/<plan-id>/reviews/plan-devex-review.md`, `plans/<plan-id>/reviews/plan-eng-review.md`, and `scenario-brake`; update `plans/<plan-id>/plan.md`, and write `plans/<plan-id>/secondary_plan.md`. Implementation must follow those accepted plan artifacts, not the earlier draft alone.
14. Before coding, complete the Worktree Preflight Checklist for the current slice and block on any mismatch, base/main managed product modification, missing binding, or stale dynamic state.
15. Before coding, run `context-loading` when required by the root `AGENTS.md` context-loading rules.
16. Implement with `tdd-workflow`.
17. If the current slice is a UI-bearing requirement, run `visual-qa-hardening` after browser screenshot verification and before `implementation-brake`; it must invoke the `visual-qa-reviewer` read-only companion when the runtime allows subagents, and for reference-driven visual work it must also invoke the `reference-fidelity-reviewer` read-only companion. If unavailable visual QA companion delegation blocks the gate, record the blocker in the current requirement's `progress.md` and `evidence.md`.
18. If the current slice is user-facing experience work, run `ux-review` after runnable/browser evidence exists and before `implementation-brake`, using the accepted plan targets and implemented flow as inputs. Record live user experience evidence, task trace, first-value result, scorecard, boomerang comparison against `plan-ux-review` when available, blockers, and verification gaps in `progress.md` and `evidence.md`. If the slice is not user-facing experience work, record `Gate status: not_required` with the reason before `implementation-brake`.
19. If the current slice is developer-facing experience work, run `devex-review` after runnable docs/API/CLI/SDK evidence exists and before `implementation-brake`, using the accepted plan targets and implemented developer-facing surface as inputs. Record live developer experience evidence, time-to-hello-world trace, scorecard, boomerang comparison against `plan-devex-review` when available, blockers, and verification gaps in `progress.md` and `evidence.md`. If the slice is not developer-facing experience work, record `Gate status: not_required` with the reason before `implementation-brake`.
20. After implementation and verification, and after any required `visual-qa-hardening`, `ux-review`, and `devex-review` gates have passed, run `implementation-brake`, invoking its relevant read-only companion subagents according to the `implementation-brake` companion routing contract when the runtime allows subagents, and close must-fix findings. If delegation is unavailable, record the explicit fallback or blocker in the current requirement's `progress.md`.
21. For managed repo isolated task work where auto-merge is applicable, run the Managed Repo Pre-Merge Gate and record merge disposition before closeout. If the gate blocks or escalates, do not mark the requirement complete.
22. After `implementation-brake` returns `[SHIP]`, required merge disposition is resolved, and required verification is recorded, run `closeout`.
23. Mark the requirement checkbox complete only after `closeout` is complete.
24. Select the next unchecked requirement in this sequence and repeat these gates from step 1.
25. When all listed requirements are checked complete, run `production-readiness` as the sequence-level final launch gate before marking the goal sequence complete if the sequence is MVP, beta, launch, or production-bound. A missing, stale, blocked, or unaccepted readiness verdict blocks sequence completion.

## State Update Rules

Update state files at gate boundaries, not only at closeout.

- At the start of each work slice, update sequence-level `progress.md` with the current requirement, current gate, status, and next action.
- Before and after every gate, update the current requirement's `progress.md`.
- When the Draft Plan is created or updated, record its path and `Status: draft` in the current requirement's `progress.md`.
- After `plan-design-review`, record the UI scope classification, gate status, `plans/<plan-id>/reviews/plan-design-review.md`, review outcome, locked design decisions, blockers, and whether the Draft Plan needs reconciliation before `plan-eng-review`.
- After `plan-ux-review`, record the user-facing experience classification, gate status, `plans/<plan-id>/reviews/plan-ux-review.md`, review outcome, locked UX decisions, blockers, and whether the Draft Plan needs reconciliation before `plan-eng-review`.
- After `plan-devex-review`, record the developer-facing experience classification, gate status, `plans/<plan-id>/reviews/plan-devex-review.md`, review outcome, locked DX decisions, blockers, and whether the Draft Plan needs reconciliation before `plan-eng-review`.
- After `plan-eng-review`, record the gate status, `plans/<plan-id>/reviews/plan-eng-review.md`, review outcome, blockers, and whether the Draft Plan needs reconciliation before `scenario-brake` or `secondary-plan`.
- After `secondary-plan`, record the primary plan path, secondary plan path, and accepted plan status in the current requirement's `progress.md`.
- After `ux-review`, record the live user experience evidence path or chat outcome, gate status, scorecard, task trace, boomerang result, blockers, and whether implementation must be reconciled before `implementation-brake`.
- After `devex-review`, record the live developer experience evidence path or chat outcome, gate status, scorecard, TTHW trace, boomerang result, blockers, and whether implementation must be reconciled before `implementation-brake`.
- For `research` and `technical-design`, record `not_evaluated`, `required_pending`, `in_progress`, `completed`, `not_required`, `blocked`, `awaiting_user_approval`, or `stale_needs_recheck`.
- When verification or review evidence is produced, update the current requirement's `evidence.md`.
- When a material design, scope, ordering, constraint, or tradeoff decision is made, update the current requirement's `decisions.md`.
- When worktree target, preflight, merge disposition, pre-merge gate, post-merge verification, re-entry, or escalation state changes, update the current requirement's `progress.md` and `evidence.md`.
- When a companion subagent starts, completes, times out, is cancelled, fails cancellation, or leaves cleanup pending, update the current requirement's `progress.md` and `evidence.md` before moving to the next gate.
- During `closeout`, reconcile the current requirement's state files, update sequence-level `progress.md`, then mark the requirement checkbox complete only if the completion contract is satisfied.
- During `production-readiness`, record the launch boundary, final readiness verdict, internal blockers, external handoff items, deferred non-goals, and next action in sequence-level `progress.md` and the readiness requirement's state files.

## Completion Contract

Mark a requirement complete only when `implementation-brake` has returned `[SHIP]`, `closeout` is complete, all must-fix findings are closed, any required UI-bearing `plan-design-review` and `visual-qa-hardening` gates have passed, any required user-facing `plan-ux-review` and `ux-review` gates have passed, any required developer-facing `plan-devex-review` and `devex-review` gates have passed, required verification has direct evidence in the requirement's `evidence.md`, and the accepted criteria are satisfied.
For managed repo isolated task work where auto-merge is applicable, completion also requires a resolved merge disposition: `auto_merged` after post-merge verification pass, or explicit human-approved closure for a non-merged disposition. `pending_pre_merge_gate` and unresolved `blocked_escalated` block completion.
For MVP, beta, launch, or production-bound sequences, the goal sequence is complete only after the final sequence-level `production-readiness` verdict is `ready` or `ready_with_external_handoff` with explicit human acceptance of the external handoff. Any unresolved `blocked_internal` item, launch-blocking `blocked_external` item, or unclassified readiness item blocks sequence completion. `deferred_non_goal` items must include the reason they are outside the accepted launch boundary.

## Blocked Rules

Do not skip gates or substitute guessed work. If a required gate, artifact, or acceptance criterion is unavailable or ambiguous, record the blocker in the relevant `progress.md` and stop or clarify unless the required artifact can be produced by the named gate.
For `research` and `technical-design`, a skip is valid only when `progress.md` records `Gate status: not_required` with a reason. Requirement impact records `awaiting_user_approval` and blocks downstream gates. Requirement edits after a completed or skipped gate make prior gate state `stale_needs_recheck` only when new evidence materially changes scope, verification, safety, design direction, decision boundaries, or handoff path.
Requirement recheck is an exception path. Do not silently reinterpret or patch accepted requirements; do not silently reinterpret or patch accepted requirements. When a requirement becomes `stale_needs_recheck`, old plan/review/conformance evidence, implementation-brake evidence, and closeout evidence must not be reused until the affected gates are rerun or explicitly revalidated.
Existing generated sequences are not automatically migrated. When resuming an older sequence that lacks the `research`, `technical-design`, UI-bearing `plan-design-review`, user-facing `plan-ux-review`, developer-facing `plan-devex-review`, live `ux-review`, or live `devex-review` gate text, rehydrate against the current `goal-requirement-orchestrator` contract before `plan-eng-review` and record whether the old sequence is manually updated or compatibility-accepted for that slice.
For `plan-design-review`, `plan-ux-review`, `plan-devex-review`, `plan-eng-review`, `scenario-brake`, `visual-qa-hardening`, `ux-review`, `devex-review`, and `implementation-brake`, unavailable required review execution, required review result, or companion subagent delegation is a gate-level fallback or blocker that must be recorded before continuing.
For companion subagent waits, an expired hard deadline is a gate-level timeout that must be recorded in `progress.md` and `evidence.md`; do not wait again for the same result unless a human explicitly approves a new attempt. A `close_agent` timeout or failure is cleanup state, not authority to keep the sequence blocked in an unbounded wait.
For UI-bearing requirements, `plan-design-review` is conditional but mandatory once triggered by a new screen, existing screen change, interaction change, state expression, design system/layout/responsive/accessibility change, or unresolved UI trust/hierarchy decision. It runs after the Draft Plan is created and before `plan-eng-review`.
For user-facing experience requirements, `plan-ux-review` is conditional but mandatory once triggered by onboarding, core task flow, navigation, state handling, recovery/re-entry, trust/safety/clarity, accessibility, or UX measurement changes. It runs after the Draft Plan is created and before `plan-eng-review`.
For developer-facing experience requirements, `plan-devex-review` is conditional but mandatory once triggered by docs, API, CLI, SDK, library, platform, agent-tool, onboarding, error-message, upgrade, developer-tooling, ecosystem, or DX measurement changes. It runs after the Draft Plan is created and before `plan-eng-review`.
For UI-bearing requirements, `visual-qa-hardening` is conditional but mandatory once triggered by user-facing UI, layout, visual state, responsive behavior, or reference-driven visual acceptance criteria. It runs after browser screenshot verification and before `implementation-brake`.
For user-facing experience requirements, `ux-review` is conditional but mandatory once triggered by implemented user-facing flows with runnable/browser evidence. It runs after implementation verification and any required browser evidence, and before `implementation-brake`.
For developer-facing experience requirements, `devex-review` is conditional but mandatory once triggered by implemented developer-facing docs/API/CLI/SDK/library/platform/agent-tool surfaces with runnable docs/API/CLI/SDK evidence. It runs after implementation verification and before `implementation-brake`.
For MVP, beta, launch, or production-bound sequences, `production-readiness` is mandatory before marking the goal sequence complete. If the final readiness requirement is missing, stale, or not accepted when reached, create or update it with `requirement-clarifier`; do not skip the launch gate or replace it with normal requirement `closeout`.
For worktree preflight and managed repo merge disposition, stale dynamic state is a blocker. Resume/re-entry must refresh current cwd, git repository root, branch, HEAD SHA, dirty status, and any relevant base or target SHA before implementation or merge. A prior `auto_merged` disposition must not trigger a duplicate merge; a prior `blocked_escalated` disposition must not proceed without recorded human resolution.

## Context Budget Rules

Keep state files concise. Summarize logs and verification output; preserve paths to full artifacts when useful. Avoid loading unrelated large files or full logs into context.
```

Use the companion templates for state files:

- `sequence_progress_template.md` for `goal-requirements/<id>/progress.md`
- `requirement_progress_template.md` for `requirements/<requirement-id>/progress.md`
- `decisions_template.md` for `requirements/<requirement-id>/decisions.md`
- `evidence_template.md` for `requirements/<requirement-id>/evidence.md`
