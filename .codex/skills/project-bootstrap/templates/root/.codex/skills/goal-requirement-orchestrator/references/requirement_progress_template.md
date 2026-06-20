# Requirement Progress Template

Use this template for:

```text
requirements/<requirement-id>/progress.md
```

Keep this file focused on gate-level recovery state for one requirement. Update it before and after every gate.

For `research`, `technical-design`, and UI-bearing `plan-design-review`, use this gate status vocabulary:

- `not_evaluated`
- `required_pending`
- `in_progress`
- `completed`
- `not_required`
- `blocked`
- `awaiting_user_approval`
- `stale_needs_recheck`

Artifact existence alone is insufficient. If an artifact path, chat-only review outcome, and the recorded gate state disagree, record the artifact/state mismatch and set the next action to revalidate, rerun, or block before `plan-eng-review`.

```markdown
# Requirement Progress

## Current State

- Current gate:
- Status:
- Plan artifact:
- Plan status:
- Next action:

## Delegated Subagent Lifecycle

- Gate:
- Subagent role:
- Agent id or handle:
- Started at:
- Hard deadline:
- Expected artifact or result:
- Companion wait status: running | completed | partial | timeout | cancel_requested | cancel_failed | unavailable
- Elapsed time:
- Timeout recorded in evidence.md: yes | no
- Cancellation requested: yes | no
- `close_agent` cleanup status: not_needed | completed | timeout | cancel_failed | cleanup_pending
- `close_agent` short timeout: 30 seconds or less
- Next action or blocker:

Record every companion start, completion, timeout, cancellation request, cancellation failure, unavailable delegation fallback, and cleanup-pending state here before moving to the next gate. `close_agent` is best-effort cleanup and must not wait without a bounded timeout.

## Worktree Preflight Checklist

- Intended target classification: `autopilot_root` | `managed_repo` | `mixed`
- Current cwd:
- Git repository root:
- Branch:
- HEAD SHA:
- Dirty status:
- Isolated worktree execution required: yes | no
- Binding source or setup owner:
- Mismatch status:
- Next action or blocker:

Before implementation, revalidate this checklist on resume and whenever the intended change set changes. A mismatch between the intended target and current cwd or git repository root is a blocker. Managed repo product source, product tests, or product docs modification in the base/main worktree is a blocker. Missing worktree binding or unavailable isolated setup is a blocker or handoff requirement, not a silent bypass.

If a slice starts as read-only planning or root-only work and later discovers managed repo product source, product tests, product docs, or mixed root-plus-managed changes, stop before implementation, reclassify, rerun preflight, and split or require isolated managed execution as applicable.

## Managed Repo Merge Disposition Checklist

- Disposition: `not_applicable` | `pending_pre_merge_gate` | `auto_merged` | `blocked_escalated`
- Auto-merge applicable: yes | no
- standard green gate status:
- accepted requirement:
- accepted plan:
- Implementation verification:
- `implementation-brake` returned `[SHIP]`:
- managed repo `scripts/verify`:
- conditional live verification:
- Live trigger type: UI | live/model | prompt/schema contract | multi-agent handoff | repair/evaluator/generator loop | live output parsing | not_applicable
- Task worktree clean status:
- Base worktree clean/up-to-date status:
- verified base or target SHA:
- SHA recheck immediately before merge:
- target branch:
- Merge command/result:
- post-merge verification:
- resulting target SHA:
- Re-entry status:
- duplicate merge prevention:
- Blocked/escalated cause:
- Conflicted files:
- Manual cleanup required:
- No automatic recovery performed:
- Next merge action or blocker:

Record `auto_merged` only after merge completion and post-merge verification pass. If post-merge verification fails after the target branch was mutated, keep disposition `blocked_escalated` and record the resulting target SHA, failing command, result, and manual cleanup required. On merge conflict, dirty/stale base, invalid target, failed gate, missing live verification, or ambiguous state, stop and escalate. Do not perform automatic recovery: no automatic retry, no automatic rebase, no automatic repair, and no automatic revert.

## Requirement Review And Conformance State

- Requirement reviewer status: reviewer_status = SHIP | FINDINGS | BLOCKED_INVALID | BLOCKED_UNAVAILABLE | NOT_RUN
- Requirement reviewer fallback status: reviewer_fallback_status = none | FALLBACK_SELF_REVIEW_USED | production_bound_blocker | unavailable_no_policy
- Conformance review status: conformance_result_status = CONFORMANT | FINDINGS | BLOCKED_INVALID | BLOCKED_UNAVAILABLE
- Conformance fallback status: conformance_fallback_status = none | FALLBACK_SELF_REVIEW_USED | production_bound_blocker | unavailable_no_policy
- AC coverage summary:
- Conformance evidence reference:
- Unresolved conformance findings:
- Residual risk handling:
- Contract parity/recovery state: partial_contract_state | cleanup_pending | ready_after_parity_pass
- Next conformance action or blocker:

Record requirement reviewer fallback, conformance reviewer fallback, AC coverage summary, unresolved findings, residual risk handling, and partial contract recovery state before treating a requirement as accepted or an implementation as ship-ready.

## Research / Design Gate State

### research

- Gate: research
- Gate status: not_evaluated | required_pending | in_progress | completed | not_required | blocked | awaiting_user_approval | stale_needs_recheck
- Reason:
- Artifact path: requirements/<requirement-id>/research.md | Not required | Missing
- Blockers:
- Requires user approval: yes | no
- Requirement version or change note:
- Artifact/state mismatch:

### technical-design

- Gate: technical-design
- Gate status: not_evaluated | required_pending | in_progress | completed | not_required | blocked | awaiting_user_approval | stale_needs_recheck
- Reason:
- Artifact path: requirements/<requirement-id>/technical-design.md | Not required | Missing
- Architecture artifact path: requirements/<requirement-id>/architecture.md | Not required - <reason> | Missing
- Blockers:
- Requires user approval: yes | no
- Requirement version or change note:
- Artifact/state mismatch:

### plan-design-review

- Gate: plan-design-review
- UI-bearing scope: yes | no
- Gate status: not_evaluated | required_pending | in_progress | completed | not_required | blocked | awaiting_user_approval | stale_needs_recheck
- Reason:
- Review outcome: passed | changes_required | blocked | not_required
- Draft Plan reviewed: plans/<plan-id>/plan.md | Missing
- Locked design decisions:
- Deferred design items:
- Draft Plan reconciliation required before `plan-eng-review`: yes | no
- Blockers:
- Requires user approval: yes | no
- Requirement version or change note:
- Artifact/state mismatch:

### plan-ux-review

- Gate: plan-ux-review
- User-facing experience scope: yes | no
- Gate status: not_evaluated | required_pending | in_progress | completed | not_required | blocked | awaiting_user_approval | stale_needs_recheck
- Reason:
- Review outcome: passed | changes_required | blocked | not_required
- Draft Plan reviewed: plans/<plan-id>/plan.md | Missing
- Locked UX decisions:
- Deferred UX items:
- Draft Plan reconciliation required before `plan-eng-review`: yes | no
- Blockers:
- Requires user approval: yes | no
- Requirement version or change note:
- Artifact/state mismatch:

### plan-devex-review

- Gate: plan-devex-review
- Developer-facing experience scope: yes | no
- Gate status: not_evaluated | required_pending | in_progress | completed | not_required | blocked | awaiting_user_approval | stale_needs_recheck
- Reason:
- Review outcome: passed | changes_required | blocked | not_required
- Draft Plan reviewed: plans/<plan-id>/plan.md | Missing
- Locked DX decisions:
- Deferred DX items:
- Draft Plan reconciliation required before `plan-eng-review`: yes | no
- Blockers:
- Requires user approval: yes | no
- Requirement version or change note:
- Artifact/state mismatch:

## Experience Review Gate State

### ux-review

- Gate: ux-review
- User-facing experience scope: yes | no
- Gate status: not_evaluated | required_pending | in_progress | completed | not_required | blocked | awaiting_user_approval | stale_needs_recheck
- Reason:
- Review outcome: passed | changes_required | blocked | not_required
- Evidence path or chat outcome:
- Task trace:
- First-value result:
- Scorecard:
- Boomerang comparison against `plan-ux-review`: yes | no | not_available
- Implementation reconciliation required before `implementation-brake`: yes | no
- Blockers:
- Verification gaps:
- Requires user approval: yes | no
- Artifact/state mismatch:

### devex-review

- Gate: devex-review
- Developer-facing experience scope: yes | no
- Gate status: not_evaluated | required_pending | in_progress | completed | not_required | blocked | awaiting_user_approval | stale_needs_recheck
- Reason:
- Review outcome: passed | changes_required | blocked | not_required
- Evidence path or chat outcome:
- TTHW trace:
- Scorecard:
- Boomerang comparison against `plan-devex-review`: yes | no | not_available
- Implementation reconciliation required before `implementation-brake`: yes | no
- Blockers:
- Verification gaps:
- Requires user approval: yes | no
- Artifact/state mismatch:

## Gate Log

### YYYY-MM-DD HH:MM KST

- Gate:
- Result:
- Plan artifact:
- Plan status:
- Gate status:
- Reason:
- Artifact path:
- Blockers:
- Requires user approval:
- Changed files:
- Verification:
- Next:
```
