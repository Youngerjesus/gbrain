# Primary Plan: <Plan Title>

Plan id: `<plan-id>`
Status: <draft | accepted>
Created: <YYYY-MM-DD>
Last updated: <YYYY-MM-DD>
Secondary plan: <Pending until secondary-plan | [secondary_plan.md](secondary_plan.md)>
Requirements source: <link or "None selected in this session">

## Goal Objective

- Codex goal objective:
- User-visible outcome:
- Why this is the right unit of work:
- Goal completion standard:

## Scope

- In scope:
- Out of scope:
- Non-goals:
- Assumptions:
- Dependencies or required inputs:

## Execution Plan

1. <Step name>: <action and expected evidence>
2. <Step name>: <action and expected evidence>
3. <Step name>: <action and expected evidence>

## Acceptance Evidence

- Required artifact changes:
- Required behavior or state changes:
- Required tests or verification commands:
- Evidence that is insufficient by itself:
- Manual checks, if any:

## Goal Completion Audit

- Requirements evidence map:
  - `<requirement or acceptance criterion>` -> `<file/test/command/artifact/manual evidence required>`
- Plan step evidence map:
  - `<plan step>` -> `<observable evidence required>`
- Secondary guardrail evidence map:
  - `<guardrail>` -> `<inspection/test/review evidence required>`
- Review gate evidence map for gates used or requested:
  - `<gate name>` -> `<evidence required>`
  - Unused gates: `Not applicable: <reason>`
- Deliverables evidence map:
  - `<deliverable>` -> `<path, behavior, or artifact proving it exists>`
- Verification evidence map:
  - `<command/check>` -> `<expected passing signal and what it proves>`
- Insufficient completion signals:
  - `<signal that must not be treated as completion by itself>`
- Residual risk accepted for this goal:

## Context Sources

- Files or docs to read first:
- Related requirements/spec/contracts:
- Related local planning or review artifacts:
- External references, if any:

## Continuation And Stop Rules

- Continue while:
- Ask the user when:
- Stop without changing files when:
- Mark the goal blocked only when:
- Mark the goal complete only when:

## Drift Checks

- The final Codex proposed plan agrees with this primary plan.
- The secondary plan's guardrails do not contradict this primary plan.
- Requirements/spec/contracts, when present, remain the product behavior source of truth.
- Any implementation-changing Plan Engineer Review or Scenario Brake decision has been reflected here.

## Goal Handoff Checklist

- [ ] Objective is concrete enough for `create_goal`.
- [ ] Execution steps are ordered and independently checkable.
- [ ] Acceptance evidence is explicit.
- [ ] Verification commands are listed.
- [ ] Goal completion audit maps requirements, plan steps, guardrails, review gates, deliverables, and verification to evidence.
- [ ] Stop, escalation, blocked, and completion rules are clear.
- [ ] Secondary plan has been read and reconciled.
- [ ] No hidden chat-only requirement is needed to execute this goal.
