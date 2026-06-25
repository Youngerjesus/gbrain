---
name: review-orchestrator
description: Own the goal-requirements Review main gate by routing post-implementation visual, UX, and DevEx lenses, then requiring implementation-brake [SHIP] before closeout.
---

# Review Orchestrator

Use this skill as the `Review` main gate for goal-requirements slices after `impl-orchestrator` has produced implementation evidence and verification results.

This skill is intentionally thin. It does not replace `visual-qa-hardening`, `ux-review`, `devex-review`, or `implementation-brake`; it makes their Review boundary and ordering explicit so the three main gates are symmetric.

## Contract

Review may start only after Impl produces implementation evidence.

Review is complete only when:

- each triggered post-implementation lens has passed with evidence, or is recorded as not required with a structured reason
- multiple triggered lenses may fan out in parallel inside the same Review gate when they do not depend on each other's output
- UI/layout/reference-fidelity work routes to `visual-qa-hardening`
- user-facing experience work routes to `ux-review`
- developer-facing docs/API/CLI/SDK/library/platform/agent-tool work routes to `devex-review`
- any triggered lens uses subagent-based review when runtime supports subagents
- cleanup-only, timed-out, missing, stale, or unresolved review output is not treated as approval
- `implementation-brake` consumes the review evidence from all triggered lenses before final ship-readiness
- `implementation-brake` returns `[SHIP]`

## Workflow

1. Read the accepted requirement, Plan handoff, implementation evidence, verification results, progress, decisions, evidence, and current git status/diff.
2. Decide which Review lenses trigger: visual, UX, DevEx, multiple lenses, or none.
3. For each triggered lens, run or verify the relevant review evidence. When multiple triggered lenses are independent, fan out those reviews in parallel, then join their evidence before `implementation-brake`:
   - `visual-qa-hardening`
   - `ux-review`
   - `devex-review`
4. Record structured not-required reasons for non-triggered lenses.
5. Block when a triggered lens is missing, cleanup-only, timed out, stale, unresolved, or contradicted.
6. Run `implementation-brake` after post-implementation review blockers are closed and all triggered lens outputs have been reconciled as Review evidence.
7. Require `implementation-brake` `[SHIP]` before handing off to closeout.

## Output Format

Report:

- Review status
- Triggered lenses and evidence paths
- Parallel lens execution used: yes | no, with dependency reason when no
- Not-required lens reasons
- Post-implementation review blockers
- `implementation-brake` verdict
- `[SHIP]` evidence or fix-before-ship findings
- Next lifecycle gate: `closeout`

## Anti-Patterns

- Flattening visual, UX, and DevEx into one vague review.
- Serializing independent triggered lenses only because they share the Review gate.
- Treating cleanup-only or timed-out review state as approval.
- Running `implementation-brake` before triggered post-implementation blockers are resolved.
- Running `implementation-brake` without all triggered lens evidence as inputs.
- Treating another review as a substitute for `[SHIP]`.
- Starting closeout without `implementation-brake` `[SHIP]`.
