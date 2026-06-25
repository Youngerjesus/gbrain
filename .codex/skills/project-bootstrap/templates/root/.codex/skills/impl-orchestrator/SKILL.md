---
name: impl-orchestrator
description: Own the goal-requirements Impl main gate by consuming an accepted Plan handoff, enforcing isolated worktree preflight, running context-loading when required, and executing implementation through tdd-workflow before Review.
---

# Impl Orchestrator

Use this skill as the `Impl` main gate for goal-requirements slices after `planning-orchestrator` has emitted an accepted Plan handoff.

This skill is intentionally thin. It does not replace `tdd-workflow`, `context-loading`, or worktree preflight; it makes their ownership and handoff boundary explicit so the three main gates are symmetric.

## Contract

Impl may start only after an accepted Plan handoff exists at:

```text
plans/<plan-id>/plan_handoff.toml
```

Impl is complete only when it has:

- consumed the accepted Plan handoff without relying on conversation memory
- confirmed the task worktree is isolated from the primary/main worktree
- run `scripts/init_worktree.sh <task-worktree-path>`
- run `context-loading` when root AGENTS triggers require it
- implemented through `tdd-workflow`
- recorded implementation evidence and verification commands for `Review`

## Workflow

1. Read the accepted Plan handoff, requirement state, progress, decisions, evidence, and current git status/diff.
2. Block if the Plan handoff is missing, stale, prose-only, or has unresolved blockers.
3. Bind and verify the isolated task worktree; run `scripts/init_worktree.sh <task-worktree-path>`.
4. Run `context-loading` before implementation when AGENTS triggers apply.
5. Use `tdd-workflow` for code or behavior changes. Record red/green/refactor or a valid pragmatic exception.
6. Run targeted verification and the relevant broader checks.
7. Record implementation evidence, verification results, residual gaps, and handoff notes for `Review`.

## Output Format

Report:

- Impl status
- Plan handoff consumed
- Worktree preflight result
- `scripts/init_worktree.sh` result
- Context-loading result or not-required reason
- TDD evidence
- Verification evidence
- Implementation evidence path
- Next gate: `Review`

## Anti-Patterns

- Starting from a ready requirement without an accepted Plan handoff.
- Implementing in the primary/main worktree.
- Treating chat or conversation memory as the Plan handoff.
- Skipping `context-loading` when AGENTS triggers require it.
- Claiming implementation complete without evidence for Review.
