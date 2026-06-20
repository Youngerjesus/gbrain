---
name: context-loading
description: Use before non-trivial implementation to delegate broad codebase exploration to a read-only context-loader sub-agent while keeping the parent agent context focused; triggers on explicit context-loading requests or automatic complexity and safety boundaries before tdd-workflow.
---

# Context Loading

Use this skill before implementation when the parent agent needs enough codebase context to work safely but should not absorb broad exploratory reading into its own context.

This skill prepares implementation. It does not implement, approve, verify completion, or replace `tdd-workflow`.

## Contract

Context loading is successful only when the parent has either:

- a usable read-only `context-loader` report with all required report fields; or
- a recorded `context-loading` `parent_fallback` result that supplies equivalent bounded parent-side context and names the residual context risk.

Unavailable, timed-out, stale, interrupted, or incomplete sub-agent output is not a successful report. `close_agent` cleanup is best-effort cleanup and must not block fallback, blocker recording, or the parent-side decision about whether implementation may continue.

## Mandatory Triggers

Run context loading when the user explicitly asks for context loading, delegated codebase exploration, sub-agent exploration, or keeping the parent context clean.

Also run context loading automatically before implementation when any of these signals is present:

- The task requires inspecting three or more files.
- The task crosses module, component, package, service, scheduler, control-plane, policy, evidence, or repo boundary.
- The affected implementation path or existing pattern is not already clear.
- The parent agent cannot state a focused test strategy without broader exploration.
- The task touches a safety-sensitive boundary, protected area, persistence or state behavior, external side effect, or verification contract.

If a task initially looks narrow but the first focused read reveals one of these triggers, stop expanding parent-side exploration and invoke context loading at that point.

If the user explicitly says "do not use subagents", honor that instruction unless a higher-priority instruction requires delegation. When skipping context loading despite a mandatory trigger, state the risk and keep parent-side exploration bounded.

## Workflow

1. State the implementation question and the mandatory trigger that applies.
2. Invoke `context-loader` with a concrete read-only exploration task.
3. Ask the sub-agent for a compact report with the required report fields.
4. If the sub-agent is unavailable, times out, or returns an incomplete report, treat the report as unusable and follow the `context-loading` `parent_fallback` policy from the goal-orchestrator lifecycle helper: record the status, perform only bounded parent-side local reads, include the same required report fields, and name the residual context risk. Rerun once only when a fresh bounded attempt is likely to produce the missing context; otherwise record a structured blocker. Do not proceed as if context loading succeeded.
5. Treat command results from context loading as exploratory evidence only. Baseline failures, missing dependencies, skipped checks, and timeouts must be labeled separately from post-implementation verification.
6. After a usable report returns, the parent agent should directly inspect only the reported change candidate files and relevant test files before editing.
7. Continue implementation with `tdd-workflow` when code changes are needed.

## Fallback Policy

When this skill runs inside goal-requirements or another lifecycle-managed gate, use the canonical fallback policy for gate `context-loading`: `parent_fallback`.

The parent fallback must:

- record timeout, unavailable, stale, interrupted, or incomplete status before continuing;
- preserve the implementation question and mandatory trigger;
- perform a bounded local read instead of broad unbounded exploration;
- produce the same required report fields as a usable context-loader report;
- record residual context risk in durable progress or evidence when such state files exist.

The parent fallback must not:

- treat missing sub-agent output as a successful no-findings report;
- wait indefinitely, retry in a loop, or spawn duplicate context-loaders on resume;
- require successful `close_agent` cleanup before fallback, blocker recording, or implementation planning can continue.

## Context-Loader Boundaries

The `context-loader` may deeply inspect the codebase and run local exploratory commands such as search, file inspection, test collection, targeted tests, type checks, or lint checks when those commands help establish context.

The `context-loader` must not intentionally modify, create, format, delete, or move files. It must not create durable report files, task files, specs, contracts, queue entries, or acceptance artifacts. Tool-created caches, stdout/stderr, and normal transient command byproducts may occur, but unexpected durable repository changes must be reported to the parent.

## Required Report Fields

The context-loader report must include:

- inspected files or directories
- core findings
- change candidate files
- test strategy

The report may also include risks, unknowns, existing patterns, command evidence, and recommended parent reads.

The report must distinguish observed facts from inferences and unknowns when that distinction matters for implementation safety. It must not choose the implementation approach for the parent. It is not acceptance evidence and not completion evidence.

## Parent-Side Completeness Gate

Before editing, the parent agent must check that the report includes all required fields and that the change candidate files and test strategy are usable.

If the report is stale, contradicted by candidate-file inspection, missing required fields, or includes concrete implementation decisions, either rerun context loading, do a bounded clarification read, or document the blocker. Do not silently follow an invalid report.

If the parent is using `parent_fallback`, the bounded local-read artifact must satisfy this same completeness gate before editing.

## Retry And Resume

On retry, resume, or interruption after context loading, revalidate the report against the current task, worktree state, candidate files, and failure evidence. Rerun context loading when the prior report is stale, incomplete, contradicted, or no longer covers the changed task.

## Handoff To TDD

For implementation work that meets the mandatory trigger criteria, context loading runs before `tdd-workflow`. The output supplies bounded code context and test strategy for `tdd-workflow`; it does not replace failing-test-first implementation or final verification.

## Output Format

Report context-loading evidence with:

- `Trigger`: the explicit request or mandatory trigger.
- `Path`: `context-loader` or `parent_fallback`.
- `Inspected files or directories`: concrete paths or directories.
- `Core findings`: observed facts, with inferences labeled when safety-relevant.
- `Change candidate files`: likely edit and nearby test files.
- `Test strategy`: focused checks the parent can run after edits.
- `Residual context risk`: required for `parent_fallback`, otherwise `none` or a concise risk.

## Anti-Patterns

- Treating sub-agent timeout, unavailability, or incomplete output as a usable context report.
- Using broad parent-side exploration as an invisible substitute for context loading.
- Blocking on `close_agent` cleanup before recording fallback or blocker state.
- Re-running context loading repeatedly without a changed task, deadline, or missing-context rationale.
- Letting a context-loader choose the implementation approach for the parent.
- Claiming context loading as completion or acceptance evidence.
