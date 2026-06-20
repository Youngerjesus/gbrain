---
name: secondary-plan
description: Use in Plan Mode or planning handoffs when the user asks for a secondary plan, wants a goal-ready primary plan written to a local file, wants planning context preserved beyond the compressed Codex proposed plan, wants a /plan output backed by detailed reasoning, or wants decision-brake, plan-design-review, plan-ux-review, plan-devex-review, plan-eng-review, or scenario-brake details retained in local planning artifacts.
---

# Secondary Plan

reference @./references/primary_plan_template.md
reference @./references/secondary_plan_template.md

This skill creates local-only planning documents under `plans/<plan-id>/` when the compressed Codex `<proposed_plan>` would lose execution detail, rationale, risks, review details, or conversation constraints that a later implementer or Codex goal needs.

## Trigger

Use this skill when any of the following are true:

- The user asks for a "secondary plan", "detailed plan artifact", "preserve planning context", or "keep the reasoning somewhere".
- The user wants to actively use Codex goals and asks for the Plan Mode plan to be written to a separate file.
- A planning handoff needs a reusable primary plan that can be pasted into, linked from, or reconciled with a Codex goal.
- The user wants `/plan` output backed by more detailed reasoning than the compressed Codex plan can hold.
- A planning turn includes decision-brake, plan-design-review, plan-ux-review, plan-devex-review, plan-eng-review, scenario-brake, or similar review details that should survive context compression.
- The next engineer or agent needs guardrails, rejected alternatives, file/test pointers, or conversation constraints, but the Codex plan should stay short.

Do not use this skill for ordinary implementation notes, code review findings, or final summaries where no separate handoff artifact is needed.

## Output Contract

- Create or update a primary plan file: `plans/<plan-id>/plan.md`.
- Create or update a secondary plan file: `plans/<plan-id>/secondary_plan.md`.
- When requirement-goal plan reviews run, create or update review artifacts beside the plan: `plans/<plan-id>/reviews/plan-design-review.md`, `plans/<plan-id>/reviews/plan-ux-review.md`, `plans/<plan-id>/reviews/plan-devex-review.md`, and `plans/<plan-id>/reviews/plan-eng-review.md` for the gates that ran. Record `not_required` gates in `plan.md` or `secondary_plan.md` instead of creating empty review files.
- If `plans/<plan-id>/plan.md` is created before review as a requirement-based Draft Plan, set `Status: draft`, use the primary plan template shape, fill the required primary sections with task-specific content, and treat it only as review input. When this skill reconciles the completed review artifacts for `plan-design-review`, `plan-ux-review`, `plan-devex-review`, `plan-eng-review`, and `scenario-brake` findings, update that same primary plan and move it out of draft only when it is accepted for implementation.
- Treat `plans/` as local runtime planning state; it must stay ignored by Git.
- Use a concise kebab-case `plan-id` from the task name. If the user provided an id, use it. If the path already exists for a different plan, append a short disambiguator.
- If `plans/<plan-id>/plan.md` already exists for the same task, update it instead of creating a parallel primary plan. Preserve still-valid goal, scope, acceptance, and verification constraints; replace stale steps explicitly.
- If an earlier primary plan for the same task exists under a different `plan-id` and the user explicitly selects it, update that selected plan and write the secondary plan beside it.
- The final Codex plan must link to both artifacts as `[primary plan](plans/<plan-id>/plan.md)` and `[secondary plan](plans/<plan-id>/secondary_plan.md)`. When review artifacts were produced in the current session, also link the relevant `plans/<plan-id>/reviews/*.md` files.
- The final Codex plan must make the links operational, not merely informational: include a clear instruction such as `Before implementation or goal creation, read the [primary plan](plans/<plan-id>/plan.md) and [secondary plan](plans/<plan-id>/secondary_plan.md), then reconcile any drift with this plan.`
- If a `requirement-clarifier` document created or explicitly selected in the current session exists at `requirements/<requirement-id>/requirements.md`, read it before writing the final Codex plan and link it from the plan with a clear instruction such as `Before implementation, read the [requirements document](requirements/<requirement-id>/requirements.md); it is the product requirements source of truth.`
- The primary plan stores the executable planning contract for goal-driven work; the secondary plan supplements it with rationale and review guardrails. Neither file silently overrides the final Codex plan shown to the user.
- Executable contract compatibility findings from `plans/<plan-id>/reviews/plan-eng-review.md` must be preserved when they are blocking implementation-readiness findings for schema, prompt, runtime, generated-artifact, or mutation-vocabulary work. Reflect execution-changing blockers in the primary plan and preserve the review rationale in `secondary_plan.md`.

## Session Provenance Rule

- Plan Mode must not automatically include, cite, or link a previously created `plans/<plan-id>/plan.md`, `plans/<plan-id>/secondary_plan.md`, or `requirements/<requirement-id>/requirements.md` just because it exists on disk.
- Include a primary plan, secondary plan, or requirements document in the final Codex plan only when the document was created or updated in the current planning session, or when the user explicitly asks to reuse that exact existing document.
- If no current-session document provenance exists, ignore older planning and requirements documents for final Plan inclusion. Do not present them as required read-before-implementation artifacts.

## Drift Rule

- The Codex `<proposed_plan>` owns the user-visible execution summary for the current Plan Mode response.
- `plan.md` owns the goal-ready objective, scope, ordered work, acceptance evidence, verification, continuation rules, and stop/escalation conditions.
- `secondary_plan.md` owns rationale, risks, guardrails, files/tests to inspect, review notes, and preserved conversation details.
- `plans/<plan-id>/reviews/*.md` owns the durable source result for each plan-stage review gate that ran; `plan.md` and `secondary_plan.md` summarize and reconcile those files instead of becoming the only copy of review evidence.
- Do not copy the full execution sequence into `secondary_plan.md`; keep it in `plan.md`.
- If the Codex plan, `plan.md`, and `secondary_plan.md` conflict, pause and reconcile before implementation or goal creation.

## Goal-Ready Primary Plan Rule

- Write `plan.md` so it can support an explicit Codex goal without requiring hidden chat context.
- Include a concrete objective, non-goals, assumptions, ordered steps, done criteria, verification commands, artifact links, continuation rules, and stop/escalation conditions.
- Keep steps actionable but not overfit to incidental code choices the implementer can decide after inspecting files.
- Prefer checkable evidence over vague completion claims. State what must be true before `update_goal(status="complete")` would be appropriate.
- State when the goal should be marked blocked: only after the same blocking condition repeats for the required goal turns and meaningful progress is impossible without user input or external-state change.
- Include a goal completion audit checklist that maps requirements, primary plan steps, secondary guardrails, review gates, deliverables, and verification commands to evidence. Passing tests alone are insufficient unless they cover the whole goal contract.

## RALPLAN-DR And ADR Rule

When the planning handoff follows `ralplan`, consensus planning, Plan Engineer Review, or any non-trivial implementation choice with more than one viable path, preserve the decision record instead of only the chosen task list.

In `secondary_plan.md`, include a RALPLAN-DR summary with:

- **Principles**: 3-5 task-specific principles the implementation should preserve.
- **Decision Drivers**: the top criteria that made one approach better than another.
- **Viable Options**: at least two plausible approaches with bounded pros and cons, or an explicit rationale for why alternatives were invalid.
- **Rejected Alternatives**: what was rejected and why it should not be reopened during implementation.
- **Premortem and expanded test plan** when the task is high-risk: auth/security, data migration, destructive or irreversible changes, production incident, compliance/PII, public API breakage, scheduler/runtime state, or cross-repo control-plane behavior.

Also include an ADR section:

- Decision
- Drivers
- Alternatives considered
- Why chosen
- Consequences
- Follow-ups

Keep canonical product behavior in `requirements.md`, `spec.md`, or `contracts.md`. The RALPLAN-DR and ADR sections explain planning judgment and guard against drift; they do not override requirements.

## Guardrail Content Rule

- Include implementation details when they constrain correctness, ownership boundaries, compatibility, security, data integrity, recovery behavior, observability, or required test coverage.
- Include Executable contract compatibility findings when `plan-eng-review` reports that legal executable contract evidence is missing, contradicted, or must block implementation readiness.
- Do not include incidental coding choices that the implementer can safely decide while editing.
- State both required constraints and allowed implementation freedom so the plan prevents regressions without over-constraining local implementation choices.
- Keep canonical product behavior, acceptance criteria, and external contract decisions in `requirements.md` or later `spec.md` / `contracts.md`; use the secondary plan only to preserve implementation constraints and review context that would otherwise disappear.

## Workflow

1. Decide whether the task needs preserved planning context beyond the compressed Codex plan.
2. Choose `plans/<plan-id>/plan.md` and `plans/<plan-id>/secondary_plan.md`.
3. If a relevant `requirements/<requirement-id>/requirements.md` was created or explicitly selected in the current session, read it before drafting the secondary plan or final Codex plan. Treat it as canonical product requirements and acceptance criteria for this planning workflow. Do not pull in older requirements documents by path existence alone.
4. Read `references/primary_plan_template.md` and `references/secondary_plan_template.md`.
5. Fill every required primary plan section with task-specific content:
   - status (`draft` before review input, `accepted` only after review findings are reconciled)
   - objective suitable for a Codex goal
   - scope, non-goals, assumptions, and dependencies
   - ordered execution steps
   - acceptance evidence and verification commands
   - artifact links and context sources
   - continuation, stop, and escalation rules
   - final goal completion checklist
   - goal completion audit checklist with evidence mappings for requirements, plan steps, guardrails, review gates, deliverables, and verification
6. For every plan-stage review gate that ran, create or update its review artifact under `plans/<plan-id>/reviews/`:
   - `plans/<plan-id>/reviews/plan-design-review.md`
   - `plans/<plan-id>/reviews/plan-ux-review.md`
   - `plans/<plan-id>/reviews/plan-devex-review.md`
   - `plans/<plan-id>/reviews/plan-eng-review.md`
   Each artifact must include the reviewed Draft Plan path, review scope trigger, verdict, findings, blockers, required plan changes, deferred items, and whether the Draft Plan must be reconciled before the next gate.
7. Fill every required secondary plan section with task-specific content:
   - why the chosen approach is valid
   - RALPLAN-DR principles, decision drivers, viable options, and rejected alternatives when the plan involved meaningful choices
   - ADR decision record when the chosen path has architectural, operational, UX, data, or workflow consequences
   - rejected alternatives and assumptions
   - required implementation constraints, allowed freedom, boundaries, and regression risks
   - files to inspect before editing
   - tests to run or add and what failures mean
   - links to review artifacts and summary notes from decision-brake, plan-design-review, plan-ux-review, plan-devex-review, plan-eng-review, and scenario-brake
   - conversation details likely to disappear after compression
   - a locked handoff checklist
8. When Plan Design Review, Plan UX Review, Plan DevEx Review, Plan Engineer Review, or Scenario Brake has been used or requested, put links and conclusions in `secondary_plan.md` and reflect any execution-changing decisions back into `plan.md`.
   - If Plan Engineer Review produced Executable contract compatibility findings, preserve blocking implementation-readiness findings in `plans/<plan-id>/reviews/plan-eng-review.md` and `secondary_plan.md`, then reflect the required guardrail or stop condition into the primary plan before implementation starts.
9. Keep the final Codex plan concise and include both plan links with an explicit instruction that the implementer must read them before implementation or goal creation. If review artifacts or a requirements document exist, include those links and the same read-before-implementation instruction.
10. Before implementation, compare the Codex plan, requirements document, primary plan, secondary plan, and review artifacts for drift.

## Plan Mode And Write Constraints

- When file writes are available, create or update `plans/<plan-id>/plan.md` and `plans/<plan-id>/secondary_plan.md` before presenting the final Codex plan.
- When plan-stage review gates ran, create or update their `plans/<plan-id>/reviews/*.md` artifacts before presenting the final Codex plan.
- When file writes are not available, do not pretend the files exist. Include the intended paths, provide the complete primary and secondary plan content in the response, and mark the links as pending creation.
- If an existing secondary plan is being updated, preserve still-valid user constraints and review notes; replace stale guardrails explicitly.
- If an existing primary plan is being updated, preserve still-valid goal, scope, acceptance, and verification content; replace stale steps explicitly.

## Constraints

- Do not store secrets, credentials, private runtime logs, or unrelated conversation history in `secondary_plan.md`.
- Do not store secrets, credentials, private runtime logs, or unrelated conversation history in `plan.md`.
- Do not add extra files beyond `plan.md`, `secondary_plan.md`, and required `plans/<plan-id>/reviews/*.md` review artifacts unless the user explicitly asks for a larger planning package.
- Do not duplicate decision-brake, plan-design-review, plan-ux-review, plan-devex-review, plan-eng-review, or scenario-brake skills. Summarize the retained conclusions and link or cite local artifacts when they already exist.
