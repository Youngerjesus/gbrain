# Requirement Evidence Template

Use this template for:

```text
requirements/<requirement-id>/evidence.md
```

Record direct evidence for review, verification, and accepted criteria satisfaction. Summarize long logs and link to full artifacts when needed.

For `research.md`, `technical-design.md`, optional `architecture.md`, and UI-bearing `plan-design-review`, record source evidence, artifact paths or chat-only review outcomes, gate status evidence, and any Requirement Impact approval evidence. Evidence should make it possible to tell whether unresolved items are blocking/non-blocking and whether a required artifact or review outcome is missing, stale, or contradicted by progress state.

```markdown
# Requirement Evidence

## Worktree And Merge Evidence Guidance

When applicable, record direct evidence for worktree preflight, target classification, merge disposition, pre-merge gate, post-merge verification, and escalation. Dynamic values belong here or in `progress.md`; do not copy local cwd, branch, HEAD SHA, or machine paths into reusable templates.

For worktree preflight evidence, include:

- worktree preflight claim
- intended target classification
- current cwd
- git repository root
- branch
- HEAD SHA
- dirty status
- isolated worktree requirement
- binding source or setup owner
- mismatch or blocker result
- revalidation reason when resuming or when the intended change set changed

For managed repo merge disposition evidence, include:

- merge disposition
- pre-merge gate claim
- accepted requirement and accepted plan evidence
- implementation verification and `implementation-brake` evidence
- managed repo `scripts/verify` evidence when present
- conditional live verification evidence or explicit not-triggered/gap rationale
- verified base or target SHA and immediate pre-merge SHA recheck
- target branch
- merge command/result
- post-merge verification command/result
- resulting target SHA
- conflicted files when available
- manual cleanup required
- blocked/escalated cause
- no automatic recovery performed

Record `auto_merged` only when merge completion and post-merge verification passed. If the target branch was mutated and post-merge verification failed, record `blocked_escalated`, the resulting target SHA, the failing command/result, and the manual cleanup required.

For UI-bearing `plan-design-review` evidence, include:

- UI-bearing scope classification and trigger
- Draft Plan path reviewed
- review outcome
- locked design decisions
- deferred design items
- blockers or user approvals
- whether `plans/<plan-id>/plan.md` was reconciled before `plan-eng-review`

For experience review evidence, include:

- plan-ux-review evidence when user-facing experience scope is triggered
- plan-devex-review evidence when developer-facing experience scope is triggered
- ux-review evidence after implemented user-facing runnable/browser evidence exists
- devex-review evidence after implemented developer-facing docs/API/CLI/SDK evidence exists
- scope classification and trigger
- Draft Plan path reviewed for plan-stage reviews
- accepted plan targets consumed by live reviews
- review outcome
- locked UX or DX decisions
- deferred UX or DX items
- task trace or time-to-hello-world trace
- scorecard and boomerang comparison when available
- blockers, verification gaps, or user approvals
- whether `plans/<plan-id>/plan.md` or implementation evidence was reconciled before `implementation-brake`

For delegated subagent lifecycle evidence, include:

- gate and subagent role
- hard deadline and elapsed time
- expected artifact or result
- wait result: completed | partial | timeout | unavailable
- cancellation result: not_needed | cancel_requested | cancel_failed
- `close_agent` cleanup result: not_needed | completed | timeout | cancel_failed | cleanup_pending
- blocker, fallback, or resume cleanup action recorded in progress.md

Treat `close_agent` as best-effort cleanup evidence only; it must not become an unbounded wait condition.

For requirement reviewer fallback evidence, include:

- requirement reviewer fallback evidence
- reviewer_status
- reviewer_fallback_status
- whether the requirement is production-bound or launch-bound
- self-review checklist result when FALLBACK_SELF_REVIEW_USED
- confirmation that fallback did not claim external reviewer approval

For conformance review evidence, include:

- conformance review evidence
- conformance_result_status
- conformance_fallback_status
- AC coverage summary
- unresolved conformance findings
- fallback status such as FALLBACK_SELF_REVIEW_USED
- evidence reference consumed by implementation-brake
- whether partial_contract_state, cleanup_pending, or ready_after_parity_pass applies

## Evidence

### YYYY-MM-DD HH:MM KST - <claim>

- Claim:
- Evidence:
- Command/artifact:
- Result:
- Files:
- Gate status:
- Source artifact: research.md | technical-design.md | architecture.md | plan-design-review outcome | progress.md | other
- Requirement Impact:
- Blocking/non-blocking unresolved items:
```
