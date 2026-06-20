---
name: plan-ux-review
description: Review user-facing plans before implementation by interrogating personas, task success, first value, recovery paths, trust, accessibility, and measurable user outcomes.
---

# Plan UX Review

Use this skill when the user asks for a user experience review, UX plan review, journey review, onboarding review, flow review, usability review, or "will users understand this?" review for a plan, spec, requirement, or product idea.

This is a planning skill. Do not implement code. Do not silently rewrite project docs unless the user explicitly asks for edits. Your job is to surface user journey gaps, force the few experience decisions that matter, and leave a clear UX implementation checklist.

## Relationship To Other Skills

- Use `plan-design-review` when the central question is visual structure, design-system fit, screen hierarchy, UI specificity, or responsive layout.
- Use `plan-ux-review` when the central question is whether the target user can complete the job, reach value, recover from failure, trust the product, and know what to do next.
- Use `ux-review` after something is runnable and the experience can be tested live.
- Use `plan-eng-review` after the UX plan is stable and implementation readiness needs architecture, scope, and test review.

## Contract

A complete review provides:

- product surface and applicability decision
- target user persona and job-to-be-done
- first-value target and journey assumptions
- first-person empathy narrative
- key task map with success, failure, and re-entry paths
- eight-pass UX scorecard using [review-sections.md](./references/review-sections.md)
- UX implementation checklist
- flat implementation tasks derived from findings
- unresolved decisions, if any
- final verdict: `GO`, `GO WITH CHANGES`, or `STOP`

If the plan has no user-facing behavior, exit gracefully and recommend a more relevant skill.

## Core Posture

- The output is a better user experience plan, not a decorative critique.
- The unit of analysis is task success: can the right user do the right thing with confidence?
- Ground every finding in a persona, job, scenario, plan line, existing product pattern, or measurable outcome.
- Ask the user only for genuine trade-offs. Recommend obvious fixes directly.
- One issue equals one decision. Do not batch unrelated user pains into one question.
- Accessibility, recovery, and empty states are not polish; they are part of the product contract.

## Workflow

### 1. Ground The Plan

Read the direct source of truth first:

- selected `plan.md`, `secondary_plan.md`, `spec.md`, `contracts.md`, or requirement docs
- `AGENTS.md` and `DESIGN.md` when present
- relevant existing UI, flow, docs, support copy, analytics notes, or tests
- screenshots, browser evidence, or prior review artifacts if the user provides them

Map:

- user-facing surface changed by the plan
- primary job-to-be-done
- current entry point and first-value moment
- existing UX patterns the plan should reuse
- states involved: first visit, returning, loading, empty, error, partial, success, permission denied, offline or delayed

### 2. Applicability Gate

Proceed when the plan changes any of:

- onboarding, navigation, task flow, form, dashboard, search, content, support, settings, account, notification, or checkout behavior
- user-visible state, copy, permission, recovery, trust, accessibility, or measurement
- AI/chat flow, recommendation, explanation, review result, or decision support experience

If none applies, say this is not a UX review target and stop.

### 3. Step 0 Investigation

Do this before scoring.

#### 0A. User Persona And Job

Infer the likely user and their job from the plan. If multiple personas would change the review, offer 2-3 concrete options and ask the user to choose.

Produce:

```text
TARGET USER PERSONA
Who:
Context:
Goal:
Tolerance:
Constraints:
Success looks like:
```

#### 0B. First-Value Target

Define the moment when the user first feels progress or relief. Estimate the target time or number of steps to reach it.

Use:

- under 30 seconds: instant confidence
- 30 seconds to 2 minutes: acceptable first value for focused tools
- 2-5 minutes: tolerable for complex or high-stakes workflows
- over 5 minutes: likely friction unless the user intent is unusually strong

#### 0C. Empathy Narrative

Write a 150-250 word first-person narrative from the user's perspective. Trace the planned or current path from entry to first value. Include what they see, what they think, what they try, what reassures them, and where they hesitate.

If the narrative depends on uncertain assumptions, ask for correction before using it as evidence.

#### 0D. Scenario Set

Select realistic scenarios before reviewing:

- happy path
- first-time user with no data
- returning user with existing state
- failed or delayed operation
- partial success
- back, refresh, resume, or reopen path
- permission, quota, or account limitation when relevant

For narrow work, choose the minimum scenario set that can expose real UX risk. For broad plans, cover all relevant paths.

#### 0E. Review Mode

Pick one mode explicitly:

- `UX EXPANSION`: new or strategically important experience; propose ambitious opt-in improvements.
- `UX POLISH`: scope is right; make every touchpoint clear, recoverable, and trustworthy. Default for most reviews.
- `UX TRIAGE`: urgent or narrow work; flag only task blockers and ship-critical confusion.

Do not drift modes mid-review without saying why.

#### 0F. Journey Trace

Trace the actual or planned journey:

1. Arrive
2. Orient
3. Act
4. Wait or interpret
5. Recover if needed
6. Complete
7. Continue, return, or escalate

For each stage, identify friction and resolve it as fixed, deferred, accepted, or blocked.

#### 0G. First-Time User Roleplay

Produce a timestamped confusion report:

```text
FIRST-TIME USER REPORT
Persona:
Attempting:

T+0:00
T+0:15
T+0:30
T+1:00
T+2:00
Final state:
```

Ground this in plan or product evidence. Do not invent a path that contradicts the source of truth.

### 4. Run The Eight UX Passes

Read [review-sections.md](./references/review-sections.md) before running the passes.

Every pass follows this pattern:

1. recall relevant Step 0 evidence
2. score 0-10
3. explain what a 10 looks like for this product and persona
4. identify the gap
5. recommend a plan change or ask one trade-off question
6. re-rate the plan assuming accepted fixes

Mode behavior:

- `UX EXPANSION`: after a solid baseline, propose best-in-class moves as opt-in scope.
- `UX POLISH`: close every material gap and tie each to a plan obligation.
- `UX TRIAGE`: block only on gaps below 5/10 or task success risks.

### 5. Synthesize Tasks

Convert accepted findings into flat implementation tasks. Each task must derive from a specific finding.

Use:

```markdown
## Implementation Tasks

- [ ] **T1 (P1)** - <surface> - <imperative title>
  - Surfaced by: <pass or Step 0 finding>
  - Files: <likely files or docs>
  - Verify: <test, browser check, accessibility check, or manual scenario>
```

Priorities:

- `P1`: blocks user task success or ship-readiness
- `P2`: should land in the same branch
- `P3`: useful follow-up UX debt

### 6. Close The Review

Return:

1. **Plan Under Review**
2. **Persona And First Value**
3. **Top UX Findings**
4. **UX Scorecard**
5. **Journey Map**
6. **Implementation Checklist**
7. **Implementation Tasks**
8. **Unresolved Decisions**
9. **Recommended Next Step**

Final verdict:

- `GO`: UX plan is ready for implementation.
- `GO WITH CHANGES`: bounded changes are needed before or during implementation.
- `STOP`: task success, trust, recovery, or accessibility gaps are too unclear to implement safely.

## Output Format

Scorecard template:

```text
UX PLAN REVIEW - SCORECARD
Dimension                 Score   Target/Gap
First Value               __/10   <gap>
Core Task Flow            __/10   <gap>
Information Architecture  __/10   <gap>
Interaction States        __/10   <gap>
Recovery And Re-entry     __/10   <gap>
Trust And Clarity         __/10   <gap>
Accessibility             __/10   <gap>
Measurement               __/10   <gap>
Overall UX                __/10
Mode                      <UX EXPANSION|UX POLISH|UX TRIAGE>
Verdict                   <GO|GO WITH CHANGES|STOP>
```

Implementation checklist:

```text
UX IMPLEMENTATION CHECKLIST
[ ] target user and job are explicit
[ ] first-value moment is reachable in <target>
[ ] primary task has a clear start, middle, and finish
[ ] empty, loading, partial, error, and success states are defined
[ ] user can recover, retry, go back, refresh, or resume
[ ] trust cues explain source, confidence, cost, risk, or consequence
[ ] accessibility and keyboard behavior are covered
[ ] mobile and desktop paths are addressed when relevant
[ ] analytics, feedback, or support loop can measure friction
```

## Anti-Patterns

- Rebranding visual design review as UX review.
- Treating persona as a demographic instead of a job and context.
- Scoring before persona, first value, and journey evidence.
- Asking vague preference questions instead of specific trade-off questions.
- Ignoring recovery paths because the happy path is clear.
- Calling accessibility a later polish task.
- Implementing code during the plan review.
