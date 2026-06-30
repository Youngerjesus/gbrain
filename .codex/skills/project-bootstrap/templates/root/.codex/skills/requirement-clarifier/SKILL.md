---
name: requirement-clarifier
description: Turn ambiguous feature ideas, grill-me syntheses, deep-interview requests, vague implementation asks, product/UI concepts, or partially formed plans into a root requirements/{requirement-id}/requirements.md contract before planning or implementation. Use when the user asks to clarify requirements, run a deep interview, avoid assumptions, convert pressure-question answers into requirements, define acceptance criteria, capture non-goals, decision boundaries, edge cases, constraints, verification methods, or create a handoff-ready requirements source of truth for design-consultation, technical-design, plan-eng-review, Plan Mode, or implementation planning.
---

# Requirement Clarifier

Act as the Product Builder. Transform raw ideas, `grill-me` syntheses, deep-interview style answers, or partially formed plans into a clear requirements contract that leaves little room for misinterpretation by an engineering or design agent.

Do not implement. Do not create execution plans. Define the What, Why, desired outcome, boundaries, acceptance criteria, avoid conditions, verification method, iteration policy when relevant, and handoff route.

## Contract

This skill is ready when it produces a requirement contract with explicit intent, scope, non-goals, acceptance criteria, verification, decision boundaries, residual risk, evidence provenance, and one clear next handoff route. It must not rely on unavailable or ambiguous routing names as if they were installed skills.

The output is:

```text
requirements/<requirement-id>/requirements.md
```

Use a short kebab-case `<requirement-id>` from the feature name unless the user provides one. The root `requirements/` directory is the requirements source read before Plan Mode and implementation planning.

When creating a new generated requirement id, inspect the existing sibling directories under `requirements/` and prefix the id with the next three-digit sequence number, starting at `001`. Use the highest existing leading three-digit numeric prefix plus one, such as `001-login-flow`, `002-login-tests`, then `003-login-docs`. Ignore sibling directories without that prefix when calculating the next number. If the user provides an exact requirement id or path, preserve it as given. Do not renumber existing requirement directories.

Do not create `contracts.md`. If strict executable contracts are needed after requirements stabilize, route to `technical-design` for module design or `plan-eng-review` for implementation-plan review unless the user explicitly selects another installed spec tool.

## Workflow

1. Run preflight context intake before asking factual questions.
2. Audit requirement readiness against the required fields and depth gate.
3. Ask one high-impact clarification question at a time until the remaining uncertainty no longer changes scope, verification, safety, or handoff.
4. Run an alignment check against repo evidence, product direction, and avoid conditions.
5. Play back the requirement before finalization when enough context exists.
6. Apply the requirement quality gate and post-draft reviewer policy.
7. Finalize `requirements/<requirement-id>/requirements.md` only with a structured readiness status, provenance, evidence, and a clear next step.
8. When the requirement is expected to continue across sessions, use
   `gbrain-protocol` to create or update the matching
   `projects/<project-id>/task-card` with Goal / Outcome, Inputs, Verification,
   Constraints, and durable Decisions.

## Session Provenance

Plan Mode must not automatically include, cite, or link a previously created `requirements/<requirement-id>/requirements.md` just because it exists on disk.

Only include a requirements document in the final Codex plan when it was created or updated in the current requirement-clarifier session, or when the user explicitly asks to reuse that exact existing document. If no current-session document provenance exists, do not present older requirements documents as product source-of-truth or required read-before-implementation artifacts in the Plan.

## Depth

Use the smallest depth that can produce a usable requirements contract.

- **Quick**: Narrow feature or already grilled idea. Ask up to 3 clarification questions.
- **Standard**: Default. Ask up to 7 clarification questions.
- **Deep**: Broad, high-risk, multi-surface, user-facing, or architecture-shaping work. Ask up to 12 clarification questions.

The question budget is a ceiling, not a target. Stop asking when remaining uncertainty would not change requirements, handoff route, or implementation safety.

## Deep-Interview Gates

When the user asks for a deep interview, wants to avoid assumptions, or the input is broad enough that Plan Mode would otherwise invent product decisions, run the clarification loop as a deep-interview gate before finalizing requirements.

Use the same depth labels, but add a readiness target:

- **Quick**: target ambiguity `<= 0.30`.
- **Standard**: target ambiguity `<= 0.20`.
- **Deep**: target ambiguity `<= 0.15`.

Ambiguity is a practical planning-risk score, not a mathematical proof. The named readiness gates below are authoritative; the numeric score is an advisory summary of unresolved readiness gaps. Do not block or unblock a requirement from the number alone.

Score from named gaps:

- Start from `0.00`.
- Add `0.05` for each required readiness field that is explicit but not yet testable.
- Add `0.10` for each required readiness field that is missing, contradictory, or based on an unconfirmed decision-bearing inference.
- Add `0.10` when brownfield context was needed but relevant code, docs, UI, or contracts were not inspected.
- Cap the score at `1.00`.

Re-score after material answers using the required fields from the readiness audit:

- Intent / desired outcome
- Target user and user story
- Scope and non-goals
- Constraints and avoid conditions
- Success, failure, and verification signals
- Edge cases and iteration policy
- Decision boundaries
- Brownfield context when existing code, docs, UI, or contracts are involved

Do not finalize merely because the numeric target is met. These readiness gates are mandatory:

- `Out of Scope / Avoid` must be explicit.
- `Decision Boundaries` must separate what the agent may decide from what the user must confirm.
- At least one pressure pass must revisit an earlier answer through evidence, assumption, tradeoff, iteration, or boundary pressure unless the request is narrow, explicit, and low-risk.
- A closure audit must find that another question would not materially change requirements, verification, safety, or handoff route.

If the user asks to proceed while ambiguity remains above target, preserve the residual risk in the requirements document and mark the readiness status as `Risky but usable` or `Blocked` depending on whether planning can proceed safely.

## 1. Preflight Context Intake

Before asking the user, inspect available local context when it can answer factual questions:

- Existing requirements, PRDs, specs, tickets, docs, README files, `DESIGN.md`, plans, and issue notes.
- Relevant code, routes, components, tests, configs, schemas, API contracts, screenshots, or existing UX patterns.
- Prior `grill-me` synthesis or user-provided interview transcript.

Do not ask the user for facts that can be discovered from repository files, docs, configs, schemas, tests, or existing UI. Ask the user only for judgment, intent, priority, tradeoffs, business rules, or unresolved product decisions.

Record findings mentally or in the draft as:

- `[from-code][auto-confirmed]`: exact descriptive facts from source evidence.
- `[from-code]`: source-backed inference that may need confirmation.
- `[from-doc]`: facts from repo docs, requirements, specs, or design notes.
- `[from-research]`: externally sourced facts such as API behavior, standards, compatibility, or official guidance.
- `[from-user]`: goals, preferences, decisions, scope, non-goals, acceptance criteria, and business logic.

For `[from-research]`, record source URL or publication identifier, access date, and whether the source is official/primary or secondary. Prefer official sources for APIs, laws, standards, compatibility, pricing, or temporally unstable facts. If evidence is unavailable or incomplete, explicitly mark the item as `insufficient` and document what is missing before advancing readiness.

Treat descriptive facts as context, not user interview rounds. Any decision-bearing interpretation still belongs to the user.

## 2. Requirement Readiness Audit

Audit the input before writing final requirements. Required fields:

- User story
- Problem / intent / desired outcome
- Acceptance criteria
- Out of scope / avoid conditions
- Success metric(s)
- Failure condition
- Edge cases
- Constraints
- Contract preservation and capability gaps
- Verification method
- Iteration policy
- Decision boundaries
- Recommended next step
- Ambiguity / readiness summary when the deep-interview gate was used

For narrow single-pass work, `Iteration policy` may be explicitly recorded as `Not applicable: single-pass requirement`. For long-running Codex goal handoffs, it must define continuation, stop, escalation, and checkpoint rules.

When the feature includes LLM agents, subagents, reviewer agents, repair agents, worker agents, generated compiler artifacts, or any generated artifact crossing an agent/runtime boundary, the requirement must include an **Artifact Handoff Contract** before it can be marked `Ready`.

The Artifact Handoff Contract must capture at least:

- producer role
- consumer role
- artifact path or path-producing rule
- artifact purpose
- failure classification
- verification method

Treat "agent reads prior conversation context" as insufficient for generated artifact handoff unless the user explicitly accepts that risk in the requirement. Ask or record who reads each artifact before requirements are finalized when the feature includes subagents, reviewer agents, repair agents, worker agents, or generated compiler artifacts.

If the input came from `grill-me`, do not treat that synthesis as final requirements. First run this readiness audit and ask at least one clarification question unless every required field is explicitly answered and testable.

Do not finalize from inferred fields. Mark inference as an assumption or ask a clarification question.

Use this readiness status:

- **Ready**: all required fields are explicit, testable, and non-contradictory.
- **Risky but usable**: minor unresolved questions remain, but planning can proceed if risks are preserved.
- **Blocked**: unresolved questions would materially change scope, success, safety, design direction, or handoff path.

## 3. Clarification Loop

Ask one question at a time unless the user explicitly asks for a batch. Each question must be high-impact enough that a plausible answer could change at least one of:

- Whether the feature should proceed
- Who it is for
- The problem or desired outcome
- Acceptance criteria or verification
- Scope, non-goals, avoid conditions, constraints, or edge cases
- Iteration and stop conditions for long-running goal execution
- Decision boundaries
- The next skill or handoff path

Prioritize questions in this order:

1. Intent and problem
2. Target user and user story
3. Success and failure conditions
4. Scope, non-goals, avoid conditions, and constraints
5. Edge cases, verification, and iteration policy
6. Decision boundaries and handoff route

If an answer is vague, press once for specificity before moving on. If the answer reveals a more important uncertainty, follow that thread instead of mechanically covering every category.

Before finalization, run at least one pressure pass unless the requirement is already explicit and low-risk. Revisit an earlier answer through one of:

- Evidence: "What observable signal proves this?"
- Assumption: "What must be true for this to work?"
- Tradeoff: "What would you reject or defer to keep this bounded?"
- Iteration: "What should the agent keep trying, stop trying, or ask you about during a long-running goal?"
- Boundary: "What may the next agent decide without asking you?"

## 4. Alignment Check

Verify the requirement aligns with the project's North Star:

- Logical, data-driven, and testable
- Clear user value and problem framing
- Clear desired outcome, boundaries, anti-goals, and avoid conditions
- No vague success criteria
- No poor UX or hidden implementation guesswork
- No conflict with discovered repo evidence, existing design contracts, or stated constraints

If a conflict exists, ask the next clarification question or record the conflict under Open Questions. Do not quietly resolve product contradictions for the user.

## 5. Playback

When enough context exists, play the requirement back before finalization using:

- **User Story**
- **Problem / Intent / Outcome**
- **Acceptance Criteria**
- **Out of Scope / Avoid**
- **Success Metrics**
- **Failure Condition**
- **Edge Cases**
- **Constraints**
- **Iteration Policy**
- **Decision Boundaries**
- **Verification Method**
- **Readiness Status**
- **Recommended Next Step**

If the playback exposes a blocking gap, ask the next clarification question instead of writing a final document.

## Original Intent Preservation

Preserve the user's original intent before applying interpretation, normalization, decomposition, or implementation-oriented wording.

Do not reinterpret the user's request into a narrower, easier, more conventional, more locally convenient, or more agent-friendly version unless the user explicitly approves that change.

Flexible interpretation may clarify ambiguity, but it must not change the requested outcome, requested behavior, artifact class, execution boundary, evidence level, fidelity/completeness expectation, source/reference preservation, or success standard.

If the user's wording is ambiguous, preserve the broader plausible intent, ask a clarification question, or mark the requirement `Blocked`. Do not silently choose the narrower interpretation.

If implementation constraints make the original intent difficult or impossible, record the capability gap and ask the user before substituting a weaker target.

Interpretation may clarify intent, but it must not replace intent.

## Strict Target And Flexible Clause Priority

When a requirement contains both a strict user target and a flexible interpretation clause, the strict user target is authoritative.

A strict user target includes any explicit requirement about requested behavior, artifact class, execution boundary, evidence level, acceptance threshold, source or reference preservation, parity, fidelity, completeness, user-visible output, non-goals, or disallowed substitutions.

A flexible interpretation clause includes any language that gives the agent discretion, such as adapting style, improving fit, simplifying, modernizing, aligning with local conventions, using judgment, preserving intent, or making reasonable substitutions.

Flexible clauses are secondary constraints only. They may guide execution inside the strict target, but they must not reduce, replace, reinterpret, bypass, or weaken the strict target.

If a flexible clause could plausibly be used to narrow the user's requested outcome, the requirement must do one of the following before it can be marked `Ready`:

- bound the flexible clause to a specific allowed range
- record explicit disallowed uses of the flexible clause
- require a deviation ledger for any intentional difference
- ask the user to choose priority
- mark the requirement `Blocked`

Agent discretion is allowed only inside the user's strict target, never as authority to narrow it.

## Requirement Quality Gate

Before a requirement can be accepted as `Ready`, validate the draft against this gate. This gate is the contract that turns a plausible requirements document into a handoff-ready requirements source of truth.

Required checks:

- Section completeness: every required section exists, is non-empty, and contains no placeholder text outside `Open Questions` or `Assumptions`.
- Acceptance criteria quality: every criterion is pass/fail testable, states an observable behavior, state, output, artifact, or user-visible result, and includes an AC-to-verification mapping.
- Contract preservation quality: the requested behavior, execution boundary or artifact class, evidence level, known capability gaps, and allowed or disallowed substitutions are explicit enough that a later agent cannot silently downgrade the work.
- Original intent preservation: the requirement must not narrow, normalize, simplify, or reinterpret the user's original request into a weaker target without explicit user approval. Ambiguous requests must preserve the broader plausible intent, ask for clarification, or mark the requirement `Blocked`.
- Escape-hatch quality: no flexible interpretation clause may weaken a strict user target. Any clause that permits discretion must be bounded, subordinate to strict targets, and paired with explicit downgrade rules when ambiguity could affect scope, fidelity, artifact class, evidence level, execution boundary, source/reference preservation, completeness, or user-visible behavior.
- Evidence quality: every source-backed claim appears in `Evidence Reviewed` with source type, location or reference, extracted fact, and confidence.
- Provenance quality: front matter records `session_provenance`, `readiness_status`, and `reviewer_status` when a persisted requirements file is created or updated.
- Decision Boundaries quality: both `Agent may decide` and `User must confirm` are specific, and user-visible behavior, data model, security posture, pricing, irreversible migration, or scope changes remain user-confirmed.
- Readiness consistency: `Ready` must not contain decision-bearing open questions; `Risky but usable` must preserve residual risk; `Blocked` must identify the blocking question or evidence gap.
- Reviewer status handling: machine-consumed readiness may use only structured `reviewer_result_status` or an explicit fallback status, never prose praise or substring matches.

## Conditional Coverage Ledger Gate

Before a broad or high-risk requirement can be accepted as `Ready`, create a machine-readable coverage decision and, when required, a separate coverage ledger.

Use `requirements/<requirement-id>/coverage-decision.yml` to record the structured decision. The decision must include `requirement_id`, `decision_version`, `ledger_required`, `trigger_evaluation`, `source_refs`, `decided_by_gate`, and `decided_at`.

Set `ledger_required: true` when any strong omission-risk trigger applies, including 10+ subtasks, 10+ screens or screenshots, multi-state UI, bulk data/table migration, multiple modules/packages, many acceptance criteria, or similar high-risk scope. Then create `requirements/<requirement-id>/coverage-ledger.yml` and keep readiness blocked until schema/readiness validation can pass.

Set `ledger_required: false` only with structured `ledger_not_required.reason`, `ledger_not_required.risk_assessment`, and `ledger_not_required.accepted_scope_refs`. A high-count but low-risk mechanical-edit case may use this path only when the accepted scope is explicitly narrow and the rationale is recorded.

`coverage-ledger.yml` is a separate artifact. Do not embed required coverage rows only in `progress.md` or `evidence.md`. `progress.md` records gate state and recheck routing; `evidence.md` records human-readable verification history.

Semantic acceptance for coverage-ledger readiness belongs to `scripts/coverage_ledger.py` or an equivalent structured validator. Skill prose, substring checks, route existence, or reviewer praise are drift hints only and must not be treated as authoritative coverage proof.

## Source Obligation Gate

Before a broad or high-risk requirement can be accepted as `Ready`, decide whether source-obligation state is required. This gate protects the upstream source universe before requirements, plans, or coverage rows can silently narrow it.

Set `trigger_evaluation.signals.source_obligation_inventory_required: true` in `coverage-decision.yml` when source-derived obligations must be preserved, including reference-parity work, codebase ports, migrations, multi-screen or multi-state UI, prompt/schema contracts, broad agent handoffs, or any slice where examples could be mistaken for total scope. When required, create or update:

- `source-inventory.yml`
- `scope-reconciliation.yml`
- `coverage-decision.yml`
- `coverage-ledger.yml`

`source-inventory.yml` records raw source truth. `scope-reconciliation.yml` records the accepted-scope candidate. requirements are a projection of reviewer-approved accepted scope, and coverage-ledger rows are proof obligations for included accepted scope. Progress, evidence, reviewer prose, and closeout prose cannot override structured source-obligation conflicts.

Run or record the `source-obligation-reviewer` result before `Ready`. Machine-consumed source review must use `source_obligation_review_status`; prose-only approval, reviewer praise, source-less scope narrowing, or a requirement draft that omits source artifacts cannot satisfy this gate. Required source-obligation readiness must also pass:

```text
scripts/coverage_ledger.py validate --mode readiness --requirement-dir requirements/<requirement-id>
```

A structured source-obligation not-required decision is allowed only when the accepted scope is explicitly narrow and records the reason, risk assessment, and accepted scope refs. Do not replace required source-obligation artifacts with a prose checklist.

Reviewer unavailable policy:

- If the post-draft reviewer is available, `Ready` requires structured `SHIP` or resolved material findings.
- If the post-draft reviewer is unavailable in an ordinary, non-production-bound requirement, run the built-in self-review fallback and record `reviewer_status: BLOCKED_UNAVAILABLE` plus `reviewer_fallback_status: FALLBACK_SELF_REVIEW_USED`; the document may be at most `Risky but usable` unless the user explicitly accepts the residual risk.
- If the requirement is production-bound, launch-bound, MVP-bound, or controls irreversible/safety-critical behavior, reviewer unavailability is blocking.
- Never silently claim external reviewer approval. A self-review fallback must not silently claim external reviewer approval and must not be recorded as `SHIP`.

## 6. Post-Draft Reviewer Gate

After drafting the requirements and before finalization, invoke the registered Codex post-draft reviewer agent `requirement-clarifier-post-draft-reviewer` when the runtime allows subagents.

The post-draft reviewer is read-only. It reviews capture fidelity and material readiness; it does not own final requirements, rewrite the document, or decide product scope.

Reviewer input must include:

- the draft `requirements/<requirement-id>/requirements.md`
- prior `grill-me` synthesis when available
- prior `grill-me` synthesis as input, not final requirements
- prior discussion and source-tagged user decisions
- unresolved assumptions and open decisions
- any explicitly preserved residual risk

For direct non-`grill-me` entry, do not fail merely because there is no `grill-me` synthesis. Provide the available prior discussion, source evidence, and clarification answers instead, and make that input boundary explicit.

The reviewer must return a structured `reviewer_result_status`:

- `SHIP`: no material finding blocks readiness
- `FINDINGS`: material findings exist and require revision
- `BLOCKED_INVALID`: the draft or reviewer input is malformed, contradictory, or insufficient to review
- `BLOCKED_UNAVAILABLE`: the required reviewer agent or runtime is unavailable

Do not treat free-form `SHIP` text, substring matches, or prose-only praise as the reviewer gate. Machine-consumed pass/fail status must come from `reviewer_result_status`.

Reviewer findings:

- The reviewer may return at most 3 material findings, with 1 preferred when only one issue truly matters.
- A material finding is one that changes scope, success or failure criteria, verification, safety, non-goals, decision boundaries, unresolved assumptions, or handoff route.
- Ignore minor polish, tone, wording, formatting, or non-material completeness comments unless the user explicitly asks for polish.

If `reviewer_result_status` is `FINDINGS`, revise the draft to address the material findings before finalization. After revision, rerun the reviewer gate unless a future explicit contract allows a different user-accepted path.

If the reviewer is unavailable, returns `BLOCKED_INVALID`, returns `BLOCKED_UNAVAILABLE`, returns contradictory status such as `SHIP` plus material findings, or returns more than 3 material findings, preserve the blocker or invalid-output state. The requirement must not claim `Ready` until the reviewer gate returns structured `SHIP` or all material findings have been addressed through the contracted gate.

## 7. Finalization

When the requirement is stable, create or update:

```text
requirements/<requirement-id>/requirements.md
```

Use this structure:

```markdown
---
requirement_id: <requirement-id>
feature_name: <Feature Name>
created_by: requirement-clarifier
created_at: <ISO-8601 timestamp>
updated_at: <ISO-8601 timestamp>
session_provenance: current-session | reused-by-user-request | unknown
readiness_status: Ready | Risky but usable | Blocked
reviewer_status: SHIP | FINDINGS | BLOCKED_INVALID | BLOCKED_UNAVAILABLE | NOT_RUN
reviewer_fallback_status: none | FALLBACK_SELF_REVIEW_USED | production_bound_blocker | unavailable_no_policy
---

# <Feature Name>

## Readiness Status

Ready | Risky but usable | Blocked

## User Story

## Problem / Intent / Outcome

## Acceptance Criteria

## Out of Scope / Avoid

## Success Metrics

## Failure Condition

## Edge Cases

## Constraints

## Contract Preservation

- Original user intent:
- Interpreted requirement:
- Narrowing risk:
- Confirmed interpretation changes:
- Strict targets:
- Flexible clauses:
- Priority rule:
- Allowed deviations:
- Disallowed downgrades:
- Requested behavior / artifact:
- Execution boundary:
- Required evidence level:
- Known capability gaps:
- Allowed substitutions:
- Disallowed substitutions:
- Downgrade approval rule:

## Iteration Policy

State `Not applicable: single-pass requirement` when this requirement is not intended for a long-running Codex goal.

### Continue when

### Stop when

### Ask user when

### Checkpoint cadence

## Decision Boundaries

### Agent may decide

### User must confirm

## Verification Method

## Evidence Reviewed

- Record each source-backed claim as a structured evidence row:
  - source_type:
  - location_or_reference:
  - extracted_fact:
  - confidence:
- If evidence is missing or unavailable, mark it as `insufficient` with the exact gap and what would change without it.

## Artifact Handoff Contract

Include this section when requirements cross agent/runtime boundaries.

- producer role:
- consumer role:
- artifact path or path-producing rule:
- artifact purpose:
- failure classification:
- verification method:

## Ambiguity / Readiness Summary

- Not applicable: deep-interview gate not used.
- Depth used:
- Final ambiguity:
- Target ambiguity:
- Unresolved readiness gaps used to score ambiguity:
- Mandatory gates:
  - Non-goals explicit:
  - Decision boundaries explicit:
  - Pressure pass completed:
  - Closure audit passed:
- Residual risk:

## Assumptions

## Recommended Next Step

- design-consultation | technical-design | plan-eng-review | direct implementation plan | decision-brake | scenario-brake | grill-me
- Reason:

## Planning Handoff

Before writing the final Codex plan or starting implementation, read this requirements document and treat it as the product requirements source of truth only when this document was created or updated in the current planning session, or when the user explicitly selected this exact document for reuse. If the implementation plan conflicts with these requirements, pause and reconcile the conflict before editing code.

Preserve the handoff bridge:

- Do not repeat already-satisfied requirement discovery by default.
- Do preserve intent, non-goals, decision boundaries, acceptance criteria, verification method, and residual risk.
- Do not let the next planning or implementation agent silently turn an assumption into a product decision.
- If residual risk is non-trivial, the next skill must either reduce it or carry it explicitly into its own plan/review artifact.

## Open Questions
```

If any required field remains unresolved, keep it under `Open Questions` and do not claim the requirement is final. If unresolved questions block planning or implementation, ask the next clarification question instead of writing a final requirements document.

When the finalized requirement is part of long-running or multi-session work,
route to `gbrain-protocol` to save or update compact project task memory at
`projects/<project-id>/task-card`. The Task Card is a recall and handoff aid,
not the product requirements source of truth. It must link the Requirement path
and, when known, the Sequence path; preserve Goal / Outcome, Verification,
Constraints, and durable Decisions; and avoid duplicating the full requirements
document.

## Handoff Routing

Recommend exactly one primary next step:

- Use `design-consultation` when product, UI/UX, frontend, visual language, IA, design-system, or interaction decisions need a durable `DESIGN.md` contract first.
- Use `technical-design` when stable requirements need HOW-level module design, architecture tradeoffs, API/data shape choices, or technical contract decisions before implementation planning.
- Use `plan-eng-review` when requirements are clear enough and the next need is implementation plan consensus, scope/reuse review, test strategy, or execution readiness.
- Use `decision-brake` when the direction, value, alternatives, or proceed/no-proceed decision remains unresolved.
- Use `scenario-brake` when state paths, recovery, entry paths, edge cases, or scenario separation are the dominant risk.
- Use `grill-me` when the idea still needs product shaping, wedge selection, audience reasoning, or demand validation.
- Use `direct implementation plan` only when the feature is small, low-risk, and all required fields are explicit and testable.

Do not route to implementation when Readiness Status is `Blocked`.

## Anti-Patterns

- Naming unavailable or ambiguous skills as authoritative next steps.
- Treating a strong-looking requirements template as sufficient when non-goals, decision boundaries, verification, or residual risk are still vague.
- Asking the user for facts that local repo evidence can answer.
- Finalizing from inferred fields without labeling assumptions or preserving open questions.
- Claiming reviewer approval from prose, substring matches, or an unavailable reviewer fallback.
- Creating execution plans, implementation details, or `contracts.md` from this skill.
- Assuming a skill is usable simply because it appears in an installed skillpack without repo-level verification of behavior or evidence contract.

## Stop Rules

Stop clarifying and synthesize when:

- All required fields are explicit and testable.
- Remaining uncertainty would not materially change scope, verification, safety, or handoff.
- The user asks to stop, in which case preserve residual risk and open questions.
- The depth budget is reached, in which case write only a `Risky but usable` or `Blocked` document depending on unresolved gaps.

Never hide residual risk to make the requirement look complete.
