---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

reference @./references/phase-gates.md
reference @./references/test-layer-selection.md
reference @./references/debug-report-template.md
reference @./root-cause-tracing.md
reference @./defense-in-depth.md
reference @./condition-based-waiting.md

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```text
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you have not completed Phase 1, you cannot propose fixes.

## Debugging Tier Decision

Before broad investigation, classify the debugging path from the actual observed evidence:

- `trivial`: one obvious syntax, import, or wiring mistake, with no mixed evidence, cross-boundary signal, failed-fix history, or explicit user request for deeper subagent review
- `standard`: one bounded component or test failure where the existing four phases can identify and verify the cause locally
- `complex`: cross-boundary behavior, multiple plausible causes, state/recovery behavior, protected or control-plane boundaries, unclear test strategy, flaky/non-reproducing behavior, delegated exploration requested, or root `AGENTS.md` context-loading triggers
- `architecture-brake`: repeated fixes reveal hidden dependencies, shared state, layer movement, or the same class of failure reappears after local fixes

The tier is a working classification, not a shortcut around evidence. If a trivial-looking error appears in the same failure bundle as downstream, cross-boundary, flaky, stale, or mixed evidence, do not use the trivial compressed path.

If the issue is currently non-reproducing or already passes on rerun, do not claim root cause. Report the changed/current state, preserve the evidence, and define the next reproduction or monitoring step.

## Complex Investigation Path

For complex debugging:

- Use `context-loading` before broad parent-side exploration when root `AGENTS.md` or the `context-loading` skill says it is required. Do not duplicate or reinterpret those trigger rules here.
- The parent debugger defines the hypothesis space before delegating: direct cause, deeper cause, masked downstream failure, alternate entry/path coverage, environment/config, and architecture-brake candidates as relevant.
- Explore hypotheses with subagents when they exist and are relevant, and always when the user explicitly asks to call related debugging subagents. Until specialized debugging agents exist, use available read-only exploration tools and report unavailable delegation as a fallback or blocker.
- Treat context-loader and subagent reports as evidence inputs only. They do not own the root-cause claim.
- The parent must revalidate high-probability candidates directly against source evidence before saying a root cause is found.
- If delegated evidence is unavailable, timed out, partial, stale, contradictory, unsourced, or out-of-lens, surface that status in the debug output and keep the fix gate blocked or downgraded until the gap is resolved.

## Use When

Use for any technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

Use this especially when:
- You are under time pressure
- A quick fix seems obvious
- You already tried multiple fixes
- A previous fix did not work
- You do not fully understand the issue

Do not skip the process because:
- The issue seems simple
- You are in a hurry
- Someone wants it fixed immediately

## The Four Phases

You must complete each phase before proceeding to the next. For detailed gates, use `references/phase-gates.md`.

### Phase 1: Root Cause Investigation

Before attempting any fix:
- Read the full error message, stack trace, warning, and failing assertion
- Choose the debugging tier from the observed evidence, and revise it when new evidence changes the scope
- Reproduce the issue consistently or gather enough data to explain why you cannot
- Check recent changes, config differences, and environmental differences
- In multi-component flows, gather evidence at each boundary to locate where behavior diverges
- Trace data backward to find the original trigger instead of fixing where the error surfaced

Phase 1 is complete only when you can name:
- The observed symptom
- The expected behavior
- The most likely failing boundary, component, or assumption
- The evidence that supports that conclusion

If you cannot do that, you are still investigating.

For resumed or reopened debugging, first rehydrate the current state from code, commands, logs, and any local `debugging/<debug-id>/` context. Mark stale, missing, contradictory, partial, unsourced, or out-of-lens prior evidence explicitly. Prior conversation state, stale local artifacts, and previous candidates cannot authorize a root-cause claim without current parent revalidation. A distinct investigation needs a new `debug-id`, or an explicit fork/supersession note plus freshness check.

### Phase 2: Pattern Analysis

Find the pattern before fixing:
- Locate similar working code in the same codebase when possible
- Compare broken and working paths completely, not selectively
- Identify all meaningful differences in code, config, inputs, environment, and execution order
- Check whether the issue is tied to a contract, configuration expectation, data assumption, or integration boundary

Do not assume the issue is only a spec mismatch or only an implementation defect. It may also be:
- A test defect
- Environment or config drift
- Missing observability
- Bad data
- External dependency behavior

### Phase 3: Hypothesis and Testing

Use the scientific method:
- In standard debugging, keep one current hypothesis.
- In complex debugging, define a small parent-owned hypothesis space before choosing the next experiment.
- Form one explicit hypothesis: `I think X is the root cause because Y`
- Define one minimal test or experiment for that hypothesis
- Define the expected observation before running it
- Run the smallest experiment that can confirm or reject the hypothesis

If the hypothesis fails:
- Do not stack additional fixes on top
- Return to Phase 1 with the new evidence
- If production code was changed experimentally, roll back, isolate, or explicitly label the dirty state before continuing

If you do not understand the problem yet:
- Say so directly
- Gather more evidence
- Ask for help only after documenting what you checked

### Phase 4: Implementation

Fix the root cause, not the symptom:
- Do not enter Phase 4 until the Root Cause Claim Gate has passed
- Choose the lowest-cost reproduction layer that can prove the bug
- Create a failing reproduction before changing production code
- Prefer automated tests, but use a one-off script, targeted command, or browser reproduction when needed
- Implement one root-cause fix at a time
- Verify the reproduction now passes and relevant broader checks still pass

Use `@tdd-workflow` when the change should be driven by an automated failing test.

If repeated fixes fail:
- Return to investigation immediately
- Prioritize the failure pattern over the raw attempt count
- If multiple fixes reveal new issues in different places, stop and question the architecture

## Root Cause Definition

`Root cause identified` does not mean `I found where it crashed`.

It means you can explain:
- What input, state, ordering, assumption, or boundary is wrong
- Why it became wrong
- What evidence proves that explanation better than competing explanations

If you cannot do that, you have a symptom, not a root cause.

### Root Cause Claim Gate

Before reporting `root cause found` or moving into Phase 4, the parent debugger must check:

- `direct vs deeper cause`: did you explain why the direct failure became possible, not only where it crashed?
- `masked downstream failure`: could the first failure be hiding a later failure that will appear after this one is fixed?
- `path coverage`: does the same class of issue enter through other paths, actors, states, configs, or retry/resume flows?
- `architecture-brake`: do repeated fixes reveal hidden dependency, shared state, layer movement, or design-level instability?
- `evidence quality`: is the claim backed by direct source/runtime evidence rather than substring hints, conversation memory, stale local artifacts, or an unverified subagent report?

Gate outcomes:

- `passed`: root-cause claim may be reported and Phase 4 may begin.
- `blocked: direct-cause-only`: trace deeper or reframe the hypothesis.
- `blocked: masked-downstream-risk`: expand reproduction or inspect the next boundary before fixing.
- `blocked: path-coverage-gap`: inspect alternate entry paths or add defense-in-depth evidence.
- `blocked: stale-or-delegated-evidence`: revalidate with current parent-owned evidence.
- `architecture-brake`: stop local patching and reclassify the work as a design problem.

If the gate fails, do not soften the wording into a root-cause claim. Return to investigation, expand path coverage, rerun or repair delegated context, classify architecture-brake, or report an explicit blocker.

## Debugging Output Contract

While debugging, communicate in this shape:
- `Symptom:` what is failing
- `Expected:` what should happen
- `Reproduced:` yes, no, or partial
- `Evidence:` logs, traces, diffs, or comparisons gathered so far
- `Tier:` trivial, standard, complex, or architecture-brake
- `Current hypothesis:` one candidate root cause, or `none/not ready` when reproduction is unavailable, evidence is insufficient, or the issue currently passes
- `Hypothesis space:` for complex debugging, the competing candidates and what would eliminate each one
- `Delegated evidence status:` not used, usable, unavailable, partial, stale, contradictory, unsourced, or out-of-lens
- `Debug packet status:` not used, missing, usable, partial, stale, contradictory, unsourced, out-of-lens, or cleaned up
- `Root Cause Claim Gate:` passed, blocked with reason, not ready, or architecture-brake
- `Next step:` one experiment or verification action
- `Fix gate:` blocked until root cause is evidenced

Use `references/debug-report-template.md` for the exact template.

## Project Integration

When used in this repository:
- Check spec artifacts only when the issue is actually connected to a feature spec or contract
- If relevant, start from the direct SSOT for that scope: `spec.md`, `contracts.md`, `tasks.md`, or the active phase review document
- If not spec-related, start from code, runtime behavior, logs, config, and recent diffs
- Do not force every issue into `spec mismatch` or `implementation bug`
- Use the categories in `references/debug-report-template.md` to keep classification honest

Repository-specific operating rules:
- When adding diagnostic instrumentation, avoid leaking secrets or PII
- Remove temporary instrumentation after the investigation unless it should become permanent observability
- Prefer parallel evidence gathering for search, working-example comparison, and environment diffing when collaboration tools are available
- Do not move into implementation until the evidence is strong enough that another engineer could understand why the fix is justified
- `debugging/<debug-id>/` may be used as ignored, local-only, optional diagnostic working context. It is non-authoritative supporting context only, never SSOT, policy clearance, progress truth, scheduler truth, task queue state, canonical spec or contract, product acceptance evidence, or root-cause authority.
- Debug packet updates are parent-owned. Context-loader and hypothesis agents may read packet context and report evidence for parent summaries, but they must not mutate `debugging/<debug-id>/` directly.
- Recommended packet notes include the investigation slug, related requirement/task/repo/worktree, source files/logs/commands/artifacts/results, last parent revalidation point, current hypothesis status, delegated evidence status, and Debug packet status.
- `requirements/<id>/evidence.md` may cite packet material only when it summarizes the claim, evidence, command or artifact, result, and files. Path-only citation to `debugging/<debug-id>/` is not evidence.
- For managed repo debugging, generated screenshots, browser captures, reference HTML, temporary JSON metadata, and task evidence still belong in the managed repo `contexts/<work-id>` owner path. For Autopilot root debugging, use root `contexts/<work-id>` or the documented canonical runtime path for generated work-context artifacts.
- If packet content remains stale, contradictory, partial, unsourced, or out-of-lens after parent revalidation, downgrade or block the root-cause/fix/closeout claim instead of reporting success.
- Closeout should state the Debug packet status and whether any temporary packet was cleaned up. If no packet was created, say so.
- If the investigation surfaces a separable, non-blocking issue and the user explicitly approves creating a diagnostic handoff report, route only that observation packet to `discovered-issue-handoff`; do not create a report automatically.

## Red Flags

If you catch yourself thinking any of these, stop and return to Phase 1:
- Quick fix for now, investigate later
- Just try changing X and see if it works
- Add multiple changes, then run tests
- Skip the test, manual verification is enough
- It is probably X, let me fix that
- I do not fully understand but this might work
- One more fix attempt
- The issue must be in the code I touched most recently

## Trivial-Issue Exception

For obvious syntax, import, or wiring mistakes, you may compress the process.

Use this exception only when the failure evidence is singular and local. If minimum verification reveals a downstream failure, mixed evidence, state/config drift, or the user asked for related subagents, leave the compressed path and reclassify the debugging tier.

Even then, do not skip:
- Reading the actual error
- Verifying the precise cause
- Running minimum verification after the fix

## Supporting Techniques

Available supporting documents in this directory:
- `references/phase-gates.md`
- `references/test-layer-selection.md`
- `references/debug-report-template.md`
- `root-cause-tracing.md`
- `defense-in-depth.md`
- `condition-based-waiting.md`

## Outcome

The goal of this skill is not to make debugging slower.

The goal is to prevent guess-driven edits, force evidence before fixes, and make it obvious when the problem is still not understood.
