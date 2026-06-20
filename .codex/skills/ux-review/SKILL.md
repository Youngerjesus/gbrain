---
name: ux-review
description: Run a live user experience audit by testing real task flows, measuring first value and completion, capturing browser evidence, and producing usability findings.
---

# UX Review

Use this skill when the user asks to test UX, run a usability audit, dogfood a flow, inspect onboarding, verify a user journey, or check whether a running product is understandable and usable.

This is a live audit skill. It is not a static design critique and not a plan review. Start from the rendered or runnable experience whenever possible.

## Relationship To Other Skills

- Use `design-review` when the user wants visual polish, layout quality, design-system consistency, or source fixes to rendered UI.
- Use `ux-review` when the user wants to know whether users can complete tasks, recover from failures, and understand what is happening.
- Use `plan-ux-review` when the flow is still a plan or spec.
- Use `browser-testing` or `browse` workflows when local browser evidence is needed.

## Contract

A complete audit provides:

- target surface and user persona assumptions
- scenario set and primary task under test
- measured or explicitly inferred time to first value and task completion
- evidence for every score: screenshots, browser observations, terminal output, file references, or a clearly marked unavailable check
- scores for the eight UX dimensions in [review-sections.md](./references/review-sections.md)
- comparison against any available `plan-ux-review` targets
- prioritized fixes tied to concrete user pain

Do not make product code changes unless the user explicitly asks you to fix findings after the audit.

When `ux-review` runs as a goal-requirements gate, the audit must also produce a durable gate output that can be copied into requirement state files. A chat-only scorecard is not enough for requirement completion.

## Core Posture

- Test like a user, not like a maintainer.
- Measure first value, task completion, confusion, and recovery.
- Screenshots, browser observations, and real interaction traces beat source-only critique.
- Mark the evidence method for each dimension: `TESTED`, `PARTIAL`, `INFERRED`, or `BLOCKED`.
- The happy path is not enough. Test empty, error, delayed, returning, and re-entry paths where relevant.
- Accessibility and recovery are core UX evidence, not optional polish.

## Workflow

### 1. Discover The Target

Read the direct task context first, then inspect:

- `AGENTS.md` and `DESIGN.md` if present
- README, docs, local app instructions, routes, and relevant tests
- current branch diff if no explicit URL is provided
- plan or requirement artifacts if the user references prior UX targets

Identify:

- target user and job
- primary task flow
- entry URL or local runnable path
- available demo data or setup steps
- key states worth testing

If no runnable URL, app command, or concrete target can be discovered, ask the user for the missing target before continuing.

### 2. Establish Evidence Path

Use the strongest available evidence:

- Browser evidence for pages, forms, flows, dashboards, modals, and state transitions.
- Terminal evidence for setup or app commands.
- File evidence for states that cannot be triggered without secrets, private data, or external services.

If a flow requires unavailable credentials, paid services, private auth, or destructive operations, mark that slice `BLOCKED` or `INFERRED` and explain the gap.

### 3. Define Scenarios

Test the smallest realistic scenario set that exposes UX risk:

- first-time user
- returning user
- empty or no-data state
- normal success path
- validation or error path
- delayed or loading path
- back, refresh, retry, resume, or reopen path
- mobile and desktop when layout or touch behavior matters

### 4. Measure First Value And Task Completion

Record:

```text
TASK FLOW AUDIT
Step 1: <user action>    Time: <measure/estimate>    Friction: <low|med|high>    Evidence: <screenshot/browser/file>
Step 2: ...
TOTAL: <steps>, <time>, <final state>
First value reached: <yes/no/partial> at <time/step>
Task completed: <yes/no/partial>
```

### 5. Run The Eight UX Passes

Read and apply [review-sections.md](./references/review-sections.md).

The eight passes are:

1. First Value And Onboarding
2. Core Task Flow
3. Information Architecture
4. Interaction States
5. Recovery And Re-entry
6. Trust, Safety, And Clarity
7. Accessibility And Responsive Use
8. Measurement And Feedback Loops

Every pass must produce a score or an explicit `BLOCKED` reason.

### 6. Boomerang Against Plan Targets

If the user provides a prior `plan-ux-review` report, requirement evidence, plan scorecard, or acceptance target, compare planned vs. live reality.

Flag:

- live score more than 2 points below plan score
- first value slower than planned
- task completion fails or requires undocumented knowledge
- recovery path missing despite plan target
- accessibility or state coverage promised but not testable

If no prior plan evidence exists, state `No boomerang baseline found`.

### 7. Produce The Audit

Lead with findings, then scorecard.

Use this structure:

1. **Target And Persona**
2. **Top Findings**
3. **Task Trace**
4. **UX Scorecard**
5. **Boomerang Comparison**
6. **Evidence Inventory**
7. **Recommended Fixes**
8. **Verification Gaps**
9. **Gate Output**

### 8. Write Gate Output For Requirement State

When the review belongs to a requirement slice, close with a `Gate Output` block using these fields:

```text
Gate Output
gate_name: ux-review
gate_status: passed | changes_required | blocked | not_required
completion_impact: may_continue | must_fix_before_completion | blocked_until_evidence | not_applicable
evidence_method_summary: TESTED=<n>, PARTIAL=<n>, INFERRED=<n>, BLOCKED=<n>
state_updates:
  progress.md: <one-line status to record>
  decisions.md: <decision entries or none>
  evidence.md: <audit artifact, browser evidence, screenshot paths, or explicit gap>
unresolved_items:
  - <owner, blocker or follow-up, and required evidence>
```

Set `gate_status: passed` only when the primary task is complete or deliberately out of scope, no P1/P2 UX issue blocks the requirement's acceptance criteria, and every required evidence gap is either `PARTIAL` with a concrete fallback or `INFERRED` with low completion risk.

Use `changes_required` when the product can be inspected but a P1/P2 finding must be fixed before requirement completion.

Use `blocked` when the primary flow, required persona, or required browser evidence is unavailable and that gap prevents a trustworthy completion decision. Browser evidence absence should usually produce `completion_impact: blocked_until_evidence` unless the requirement explicitly allows file-only UX review and the affected dimensions are marked `INFERRED`.

Use `not_required` only when the selected requirement has no user-facing experience surface and record the reason in `progress.md`.

## Output Format

Scorecard template:

```text
UX LIVE AUDIT - SCORECARD
Dimension                 Score   Evidence              Method
First Value               __/10   <screenshots/trace>   TESTED
Core Task Flow            __/10   <screenshots/trace>   TESTED
Information Architecture  __/10   <screenshots>         TESTED
Interaction States        __/10   <screenshots/files>   PARTIAL
Recovery And Re-entry     __/10   <screenshots/trace>   PARTIAL
Trust And Clarity         __/10   <screenshots>         TESTED
Accessibility             __/10   <browser/manual>      PARTIAL
Measurement               __/10   <files/pages>         INFERRED
First value time          __
Task completion           <yes|no|partial>
Overall UX                __/10
```

For each issue, include:

- severity: `P1 task blocker`, `P2 meaningful friction`, or `P3 polish`
- evidence
- user impact
- recommended fix
- verification method after the fix

## Anti-Patterns

- Auditing from source alone when the flow can be tried.
- Reviewing visual beauty instead of user task success.
- Scoring without evidence.
- Hiding untested dimensions inside an overall score.
- Ignoring error, empty, delayed, or re-entry paths.
- Calling accessibility out of scope without a product reason.
- Making product changes during an audit unless explicitly requested.
