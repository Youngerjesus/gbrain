---
name: visual-qa-hardening
description: Conditional post-implementation visual QA gate for UI-bearing requirements. Use after browser screenshot verification and before implementation-brake when a requirement changes user-facing UI, layout, design tokens, responsive behavior, or reference-driven visual output; requires an independent read-only visual-qa-reviewer companion and, for reference-driven work, a reference-fidelity-reviewer companion when runtime allows subagents.
---

# Visual QA Hardening

Use this skill as a quality gate for a UI-bearing requirement after implementation has browser screenshot verification and before `implementation-brake`.

This skill is not a substitute for `implementation-brake`. It owns visual readiness only: rendered hierarchy, layout, responsive behavior, state presentation, trust quality, and screenshot evidence sufficiency. `implementation-brake` still owns implementation ship-readiness.

## When To Run

Run this gate only for a UI-bearing requirement, including any change that touches:

- user-facing pages, components, layout, CSS, design tokens, typography, icons, or visual assets
- responsive behavior, mobile sheets, dropdowns, modals, forms, navigation, or interactive UI states
- loading, empty, error, disabled, pending, failed, or success states visible to users
- reference-driven visual work, visual QA acceptance criteria, screenshot comparison, or design fidelity language

Do not run this gate for backend-only APIs, database migrations, internal scripts, test-only changes, or copy changes that cannot affect layout or user-facing visual hierarchy.

## Required Inputs

Before this gate starts, gather or create:

- the current requirement, accepted plans, and relevant visual acceptance criteria
- browser screenshot verification artifacts for desktop and mobile
- reference/app screenshot artifacts when the work is reference-driven
- at least one realistic stress state when relevant, such as long labels, missing optional user data, loading/error/payment states, dense lists, or mobile narrow width
- notes on known accepted differences from the reference
- a `frontend_verification_artifact` record following `../_shared/frontend-verification-artifact-schema.md`

Pixel score 단독 PASS 금지: same-run browser evidence and human-readable visual review findings are required. Static screenshot score alone is not enough.

## Workflow

Add this reporting order to every gate result, including blocked results:

- `scope`: UI-bearing or `not_required`, with reason.
- `evidence`: desktop, mobile, stress states, and reference artifacts reviewed or missing.
- `companion_status`: invoked reviewer ids, unavailable companions, or fallback approval status.
- `verification_artifact`: current `frontend_verification_artifact` ref, or `not recorded` with the first missing field.
- `four_axis_scores`: `design_quality`, `originality`, `craft`, and `functionality` scores with one-sentence rationale each.
- `checklist_findings`: concise checklist-style findings, or `not reviewed` with the first missing contract item.
- `reconciliation`: accepted/rejected/deferred/blocked companion or fallback findings when any exist.
- `verdict`: one of `[VISUAL QA PASS]`, `[VISUAL QA FIX REQUIRED]`, or `[VISUAL QA BLOCKED]`.

When the result is blocked before full inspection, still report the ordered steps completed and name the first missing contract item in the verdict sentence.

1. Confirm the change is UI-bearing. If it is not, record `not_required` with the reason and stop.
2. Read the current requirement, accepted plan, visual acceptance criteria, and `DESIGN.md` when present.
3. Collect browser evidence before judging: desktop screenshot, mobile screenshot, required reference artifacts, accepted differences, and at least one relevant stress state.
4. Decide companion reviewer availability for this runtime before the visual review begins.
5. Invoke the required companion reviewers when available, or obtain and record a structured no-subagent fallback approval before continuing.
6. Create or update the shared `frontend_verification_artifact` record, binding screenshots to route, viewport, state, run, interaction, inspection, reviewer, and verdict evidence.
7. Inspect the rendered UI with the Review Checklist and the Four-Axis Rubric, then classify findings as must-fix, should-fix, polish, blocked, or not-applicable.
8. Reconcile companion or fallback findings. Preserve only decision-changing accepted, rejected, deferred, and blocked findings.
9. If fixes are required, return to implementation, make the smallest safe UI change, re-run affected browser screenshots, update the verification artifact, and repeat this gate.
10. Update `progress.md` and `evidence.md` with the final visual QA verdict, verification artifact ref, evidence paths, fallback or companion records, four-axis scores, and unresolved risks.

## Companion Reviewer Contract

When the runtime allows subagents, invoke the required read-only companion reviewers:

- `visual-qa-reviewer`: independent rendered UI reviewer for hierarchy, spacing, typography, color/state treatment, clipping, overflow, responsive behavior, interaction affordance, product trust quality, and common visual error patterns.
- `reference-fidelity-reviewer`: required for reference-driven work, reference screenshots/images, reference-app captures, or design fidelity acceptance criteria; reviews detailed similarity against references and accepted differences.

Do not let the reviewer edit files, update tests, rewrite requirements, or decide final ship-readiness. The reviewer is evidence input only.

If a UI-bearing requirement needs this gate and the `visual-qa-reviewer` cannot be invoked, return `[VISUAL QA BLOCKED]` unless the user explicitly accepts a no-subagent fallback and the fallback approval record is captured. If the work is reference-driven and the `reference-fidelity-reviewer` cannot be invoked, return `[VISUAL QA BLOCKED]` unless the user explicitly accepts a no-subagent reference fallback and the reference fallback approval record is captured. Record unavailable companion delegation in the current requirement's `progress.md` and `evidence.md`.

Companion finding reconciliation is mandatory. The main `visual-qa-hardening` pass must classify each companion finding as accepted, rejected, deferred, or blocked with concise evidence. For reference-driven work, reconcile the `reference-fidelity-reviewer` recommendation separately from the general `visual-qa-reviewer` recommendation before the final visual QA verdict. Do not copy every companion note into final state; preserve only decision-changing findings.

## No-Subagent Fallback Approval

A fallback approval must be current to the requirement and run under review. Standing, global, historical, or blanket approvals are too broad unless they name the current requirement/run scope, substitute evidence, and accepted independent-review risk.

A no-subagent fallback is a controlled exception, not the default path. Use it only when the runtime cannot invoke the required reviewer, the user or requirement owner explicitly accepts the exception for the current requirement/run, and the main agent can still collect enough browser evidence to make a visual judgment.

Record one fallback approval entry per unavailable companion with these fields:

- `requested_companion`: `visual-qa-reviewer` or `reference-fidelity-reviewer`.
- `unavailable_reason`: runtime/tooling limitation, timeout after retry, or explicit environment restriction.
- `approval_source`: user chat approval, accepted requirement note, or owner-approved plan/evidence entry.
- `scope`: requirement id or task scope, viewports, states, and reference artifacts covered by the fallback.
- `substitute_evidence`: extra screenshots, stress states, reference comparisons, browser inspection notes, or same-run rendered evidence used instead of companion review.
- `risk_accepted`: concise statement of the independent-review risk the owner accepted.
- `recorded_in`: `progress.md`, `evidence.md`, or chat-only fallback note when no requirement files exist.

If fallback approval is missing, stale, too broad, or does not name substitute evidence, return `[VISUAL QA BLOCKED]` with the reason `missing fallback approval`. A fallback can still end in `[VISUAL QA FIX REQUIRED]` or `[VISUAL QA PASS]`, but only after the main pass records the approval entry, applies the Review Checklist, and explains the remaining independent-review risk.

## Review Checklist

Inspect rendered UI in this order:

1. First impression and product trust
2. Information hierarchy, focal point, and CTA priority
3. Layout rhythm, alignment, spacing, card density, and section separation
4. Typography scale, wrapping, readability, and numeric/date stability
5. Semantic color and state treatment
6. Stray elements, debug/prototype artifacts, broken icons, and unexplained text
7. text clipping, overlap, horizontal overflow, clipped section headers, and incoherent wrapping
8. Desktop and mobile responsive intent, not just stacked desktop UI
9. Touch targets, focus/hover affordances, sheet/dropdown/modal visual safety
10. Realistic stress state/data variants relevant to the requirement
11. Reference evidence sufficiency when a reference exists: reference artifacts, implementation screenshots, accepted differences, and `reference-fidelity-reviewer` findings
12. AI-template smell: generic dashboard, card spam, decorative icon circles, arbitrary gradients, ornamental filler, or equally loud sections

## Four-Axis Rubric

In addition to checklist findings, score every UI-bearing gate on these axes using `0-10` plus one concise rationale. The scores do not replace the verdict; unresolved must-fix evidence still blocks pass.

- `design_quality`: color, typography, layout, imagery, and interaction treatment form one trustworthy product identity.
- `originality`: the surface avoids template defaults, generic AI slop, decorative filler, and arbitrary component spam.
- `craft`: spacing, alignment, contrast, wrapping, density, responsive adaptation, and visual states are executed cleanly.
- `functionality`: users can understand the state, identify the primary action, complete the flow, and recover from loading/error/empty/disabled states.

If the four-axis scores and final verdict appear to disagree, explain the gating reason. Example: `functionality=9` can still be `[VISUAL QA FIX REQUIRED]` when mobile craft has a must-fix overlap.

## Verdicts

Blocked verdicts must be specific. Prefer: `[VISUAL QA BLOCKED] <first missing item>: <required next evidence or approval>`. Examples include missing mobile same-run browser evidence, missing stress-state evidence, missing `visual-qa-reviewer` fallback approval, missing `reference-fidelity-reviewer` fallback approval, or stale pixel-score-only proof.

The final verdict is owned by the main skill:

- `[VISUAL QA PASS]`: no unresolved must-fix visual findings; evidence is sufficient.
- `[VISUAL QA FIX REQUIRED]`: one or more must-fix findings must be repaired and re-verified before `implementation-brake`.
- `[VISUAL QA BLOCKED]`: required browser evidence, reference evidence, stress state, or companion reviewer delegation is unavailable.

최종 `[VISUAL QA PASS]` / `[VISUAL QA FIX REQUIRED]` / `[VISUAL QA BLOCKED]` verdict 는 항상 main `visual-qa-hardening` 이 소유합니다.

## Must-Fix Standard

Classify a finding as must-fix when it can make a user distrust, misunderstand, or fail to use the UI, including:

- visible broken or stray elements
- incoherent overlap, clipping, or horizontal overflow
- mobile layout that breaks the intended hierarchy
- primary action hidden, ambiguous, or visually weaker than secondary/status elements
- semantic state color/copy that exaggerates or hides user impact
- reference-only prototype chrome or debug UI leaking into product
- missing visual evidence for required viewport/state coverage
- unresolved must-fix reference fidelity gaps from `reference-fidelity-reviewer`

Should-fix and polish findings may be deferred only when they do not block user trust, comprehension, or task completion.

## Evidence Output

Update the current requirement evidence with:

- `frontend_verification_artifact` ref or inline record when no artifact path exists
- viewport and state coverage reviewed
- screenshot/reference artifact paths
- companion reviewer ids or explicit blocked/fallback reasons
- accepted/rejected/deferred findings
- four-axis scores and rationale
- fixes made after the gate and re-verification evidence
- final verdict

After `[VISUAL QA FIX REQUIRED]`, return to implementation with the smallest safe styling or markup changes, re-run browser screenshot verification for affected viewports/states, and run this gate again.

## Anti-Patterns

- Treating pixel score, screenshot diff, or static image inspection as sufficient without same-run browser evidence.
- Auto-approving no-subagent fallback because the runtime lacks companion reviewers.
- Passing with missing mobile, desktop, stress-state, or reference evidence required by the requirement.
- Letting a companion reviewer edit files, rewrite requirements, or own the final verdict.
- Copying every companion note into durable evidence without accepted/rejected/deferred/blocked reconciliation.
- Hiding unresolved must-fix visual issues as polish or follow-up work.
- Reviewing design taste in isolation from the requirement, accepted plan, browser evidence, and `DESIGN.md` when present.
- Creating route-local visual rules or duplicate UI foundations when an accepted shared foundation exists.
