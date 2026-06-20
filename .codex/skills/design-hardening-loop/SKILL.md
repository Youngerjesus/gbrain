---
name: design-hardening-loop
description: Use this skill to improve a worktree's overall website design by running `project_manager/design_loop.py`, which consumes a prior design consultation result and iterates `design-html` plus `design-review` with live browser evidence.
---

# Design Hardening Loop

reference @./references/loop-contract.md

Use this skill when the user wants a whole-site design improvement loop instead of a one-off mockup or a one-off visual audit.

## Use When

- Running a multi-round design hardening loop for a worktree website
- Converting a completed consultation result into repeated design artifacts and design reviews
- Saving all design-loop artifacts under `project_manager/contexts`
- Resuming a partially completed design loop run

## Do Not Use

- Creating the initial design strategy from scratch with no consultation result
- Implementing production UI code directly
- Reviewing one small component in isolation
- Saving artifacts outside `project_manager/contexts`

## Operating Rules

1. Treat `project_manager/design_loop.py` as the authoritative loop engine.
   Do not recreate its loop logic inside the skill folder.
2. Consultation is a required input, but it is not immutable.
   Run `design-consultation` first, then pass its result into the loop. If the evaluator proves a visual direction conflict or repeats the same `high` visual finding twice, the loop may create a consultation amendment before the next generator round by resuming the current evaluator session. Route accessibility or browser-reviewability failures are not consultation issues.
3. The loop is artifacts-only.
   Do not modify application source code while using this skill.
4. Use live browser evidence.
   The loop must inspect the running app URL and use browser-based review instead of source-only critique.
5. Store all outputs under `project_manager/contexts`.
   This loop overrides older `contexts/design-html/...` guidance.
6. Reuse generator sessions across rounds, but keep evaluator sessions fresh per round.
   Resume only the same phase/session after interruption. Do not reuse evaluator sessions across rounds.
7. Prefer the loop policy summary over raw rule files.
   The engine compiles repo and skill rules into a run-local `policy-summary.md` and uses that compact summary during generation and evaluation.
8. Treat target routes as preconditions, not design findings.
   If a route in the target brief is not browser-reviewable in the live app, the loop should stop with a route-precondition failure instead of continuing or amending the consultation.

## Workflow

1. Confirm the target worktree root and app URL.
2. Confirm a consultation markdown result already exists.
3. Run `project_manager/design_loop.py --worktree-root <path> --app-url <url> --consultation-path <file> --target-brief-path <file> --max-rounds 10`.
   If the app is already running or sandbox constraints make server startup undesirable, add `--skip-environment` and reuse the existing live URL.
   Use `--run-name` for a new loop run. Use `--run-dir <existing-run-dir>` when resuming a partially completed run.
   For smoke verification, prefer `--smoke-mode --max-rounds 1` so the loop uses a smaller model and shorter timeouts.
4. Review the generated `project_manager/contexts/design-loop/<run>/final.md`.
5. If the loop created consultation amendments, treat `consultation.current.md` as the active design SSOT for subsequent rounds.
6. If the loop approved early, use that round's artifact as canonical.
7. If max rounds were exhausted, use the recorded best round as canonical and summarize the remaining design debt.

## Defaults

- Engine: `project_manager/design_loop.py`
- Consultation: external prerequisite for project-level visual direction
- Target brief: required external prerequisite for run-specific route scope and success criteria
- Consultation revisions: allowed when direction conflict is proven by evaluation
- Default rounds: `10`
- Storage: `project_manager/contexts/design-loop/...`
- Final design artifact: best approved round, or best-scoring round when approval never happens
