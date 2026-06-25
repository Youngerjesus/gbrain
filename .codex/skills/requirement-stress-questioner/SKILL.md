---
name: requirement-stress-questioner
description: Generate high-impact stress questions for already-written requirements, specs, PRDs, or feature briefs, with an intent-contraction lens that catches weaker interpretations before implementation.
---

# Requirement Stress Questioner

Use this skill after a requirement draft already exists and the user wants the holes exposed before planning or implementation. The job is to generate sharp questions, not to rewrite the source requirement.

## When To Use

Use this skill when the input is an already-written requirement draft, PRD, spec, feature brief, or `requirements/<id>/requirements.md` after initial requirement creation.

Good triggers include:

- "Review this requirement and find the questions we should answer before implementation."
- "What could be missing from this PRD?"
- "Could an implementer shrink the intent here?"
- "Generate good questions for this completed spec."

Do not use this skill as the first pass for raw vague ideas, brainstorming, or problem discovery before a requirement exists. Use `grill-me` or `requirement-clarifier` first in those cases.

## Relationship To Nearby Skills

- `grill-me` interrogates early ideas before a requirement is locked.
- `requirement-clarifier` creates or revises requirement contracts.
- `scenario-brake` pressure-tests scenario coverage when scenario separation is the dominant risk.
- `decision-brake` reviews whether a direction or decision should proceed.
- this skill generates post-draft stress questions and does not rewrite by default.

Route back to `requirement-clarifier` only after the user answers questions that should update the requirement source of truth.

## Contract

This skill returns a concise set of handoff-changing questions for an existing requirement. It must:

- preserve the user's original requested behavior, artifact class, execution boundary, fidelity, and evidence level;
- prioritize blocker and downgrade-prevention questions before refinement questions;
- include lens labels on every emitted question;
- explain why each question matters and what downstream requirement field, decision, or verification proof the answer could change;
- inspect local repo evidence before asking factual questions that files, docs, code, tests, or existing contracts can answer;
- ask the user only for judgment, priority, intent, tradeoff, or unresolved product decisions;
- avoid modifying, normalizing, narrowing, or replacing the source requirement unless the user explicitly asks.

## Workflow

1. Ground the source. Identify the referenced requirement, PRD, spec, feature brief, or `requirements/<id>/requirements.md`.
2. Inspect the source. Specifically, read the referenced requirement and relevant nearby docs or contracts when available. Do not ask factual questions that repo evidence can answer.
3. Summarize the current handoff risk in one or two sentences.
4. Run the question lenses. Do not ask one question per lens mechanically. Select only questions that could change acceptance criteria, verification, scope, non-goals, decision boundaries, or handoff readiness.
5. Prioritize blocker and downgrade-prevention questions before refinement questions.
6. Default to a concise batch of roughly 5-8 high-impact questions. Ask fewer when fewer questions pass the criticality gate.
7. Use one-question-at-a-time interview mode when the user asks for a loop, wants to answer as they go, or a prerequisite answer is needed before responsible follow-ups.
8. Include skipped-lens rationale when a normally relevant lens is omitted from the output.
9. Recommend the next step: answer questions in chat, route to `requirement-clarifier`, use `scenario-brake`, use `decision-brake`, or proceed to planning only when the draft is handoff-ready.
10. When the output is saved as an artifact or used as gate evidence, run `scripts/validate_output.py <artifact.md>` from this skill directory and fix structural failures before treating it as evidence.

Ask the user only for judgment, priority, intent, or unresolved decisions. If repo evidence contradicts the requirement, report the contradiction instead of silently resolving it.

## Question Lenses

Use these lenses as selection tools, not a checklist. Each emitted question must carry a lens label.

- Intent-contraction lens: Ask whether an implementer could satisfy the draft with a narrower artifact, weaker behavior, lower evidence level, smaller execution boundary, reduced fidelity, or unapproved substitute. Each downgrade-prevention question must name the original intent, a plausible weaker interpretation, the impacted requirement field or evidence level, and what answer would block the downgrade.
- Failure lens: Ask why the requirement could fail even if implemented as written, what the failure would look like to the user or operator, and which assumption would break first.
- Ambiguity lens: Ask which terms, outputs, actors, states, priorities, or quality bars could be read in multiple implementation-valid ways.
- Missing-scenarios lens: Ask which entry paths, user types, data shapes, states, retries, errors, re-entry flows, or edge cases are not covered by the current acceptance criteria.
- Verification lens: Ask what observable evidence proves completion, what evidence disproves it, which checks are deterministic versus judgment-based, and whether the evidence level matches the user's requested standard.
- Scope lens: Ask what is explicitly in scope, what is out of scope, what could be accidentally added, and what could be accidentally removed while still appearing to satisfy the draft.
- User-value lens: Ask what user pain or desired outcome the requirement is meant to change, whether the stated feature is only a proxy for that outcome, and what result would make the work valuable.
- Dependency lens: Ask what external systems, source documents, prior requirements, permissions, data availability, model behavior, runtime capabilities, or sequencing assumptions the requirement depends on.
- Decision-boundary lens: Ask which decisions the next agent may make alone, which decisions require user confirmation, and which assumptions must remain explicit rather than becoming implementation choices.
- Handoff-readiness lens: Ask whether a planning or implementation agent can act from the document without inventing product decisions, weakening the artifact class, lowering evidence, or losing source/reference obligations.

## Output Format

Use this shape by default:

```markdown
**Source reviewed**
<requirement path, PRD/spec title, or quoted source reference used for this review>

**Readiness summary**
<2-4 sentences on whether the draft is handoff-ready and what kind of risk remains.>

**Highest-risk gaps**
- <gap and requirement field/evidence area affected>

**Prioritized good questions**
1. Lens: <lens label>
   Priority: <blocker | high-risk ambiguity | verification gap | refinement>
   Question: <one concrete question>
   Why it matters: <what can break or be misread>
   Answer impact: <requirement field, acceptance criterion, verification proof, decision boundary, non-goal, or implementation handoff that could change>

**Skipped-lens rationale**
- <lens>: <why no question from this lens passed the criticality gate>

**Recommended next step**
<answer now, revise via requirement-clarifier, use scenario-brake/decision-brake, or proceed to planning>
```

Every question must be specific enough that a useful answer could change a requirement field or downstream decision. Do not pad the list to reach a target count.

## Verification Helper

Use `scripts/validate_output.py` to validate saved Requirement Stress Questioner output before relying on it as durable evidence. The helper checks the required sections, question field shape, supported lens labels, priority values, and non-empty answer-impact fields. It is a structural guard only; the main agent is still responsible for judging whether the questions are specific, evidence-grounded, and handoff-changing.

## Companion Review

This skill works as a single-agent requirement-draft review by default.

Use optional companion review only when the user asks for delegated review or the runtime already provides compatible read-only reviewers. Treat companion findings as candidate inputs, not final output.

When companion review is used, the main agent must:

- deduplicate overlapping questions;
- accept/reject each material companion finding;
- mark plausible but unproven findings as evidence-needed;
- exclude out-of-scope or speculative findings;
- report reviewer unavailability when it affects confidence;
- preserve the single synthesized question list as the authoritative result.

Invalid, partial, or malformed companion output must not be mixed into authoritative results. Companion review cannot overrule the main synthesis, cannot silently create a partial-pool question set, and cannot become mandatory for ordinary narrow drafts.

## Anti-Patterns

- Asking generic checklist questions that would fit any requirement.
- Avoid praise-only review or soft reassurance when handoff risks remain.
- Avoid excessive question volume that hides the few questions that matter.
- Avoid hidden scope downgrades in the name of simplicity, feasibility, local convention, or implementation convenience.
- silent rewriting of the requirement, or editing the requirement when the user only asked for questions.
- Avoid normalizing the requirement into an easier task.
- Accepting a weaker substitute, mock, route-only artifact, documentation-only artifact, lower-fidelity output, or weaker evidence level without explicit user approval.
- Treating lens names as coverage when responsibilities and answer impact are missing.
- Asking factual questions before checking the referenced requirement and nearby repo evidence.
- Treating optional companion output as approval or as a source of truth.
