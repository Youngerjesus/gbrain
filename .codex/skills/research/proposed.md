---
name: research
description: Resolve decision-bearing technical unknowns as a goal-requirements conditional hard gate, writing requirement-local research.md before technical-design or plan-eng-review. Use when a selected goal-requirements slice needs evidence-backed technical decisions; this is not a general browsing or narrative research skill.
---

# Research

This skill is the `goal-requirements` conditional hard gate for technical research. It is not a general browsing or narrative research skill.

Use it after `requirement-clarifier` and before `technical-design` or `plan-eng-review` when the current requirement has decision-bearing technical unknowns, external dependencies, platform/API/library choices, temporally unstable facts, domain constraints, security/compliance concerns, model behavior, cost/pricing, or architecture pattern choices that would make implementation planning guessy.

## Contract


## Evidence Taxonomy

Classify every evidence item before using it in a research decision:

- `repo_local`: Requirement source, progress state, decisions, evidence files, specs, plans, docs, tests, and code in this repo. Use for repo-specific behavior, accepted contracts, implementation constraints, current interfaces, configuration, and verification expectations.
- `official_primary`: Vendor documentation, API references, standards/RFCs, official policy/pricing/security/compliance pages, release notes, source repositories, or authoritative platform documentation. Use for external facts, platform behavior, legal/compliance constraints, pricing, model behavior, and temporally unstable claims.
- `degraded_secondary`: Blogs, tutorials, forums, summaries, search snippets, generated answers, vendor-adjacent articles, or stale/undated references. Use only for discovery or weak corroboration unless explicitly recorded as degraded evidence.

For each evidence item, record what specific RD claim it supports, its source class, freshness date or retrieved date when facts may change, and any confidence limitation. Do not produce generic citation dumps or treat all citations equally. If a decision depends on `degraded_secondary` evidence, classify whether that limitation blocks downstream planning; use `blocked` or `stale_needs_recheck` when authoritative support is still required.

The research gate is complete only when it converts decision-bearing unknowns into evidence-backed decisions, explicit unresolved-item classifications, and synchronized goal-requirements state.

The skill must:

- Decide whether research is `required` or `not_required` from the requirement source of truth, not from a desire to create an artifact.
- Use local docs and code first for repo-specific questions, and primary or official external sources for external or temporally unstable facts.
- Keep the accepted requirement scope stable unless a Requirement Impact is explicitly recorded and held for user approval.
- Record decisions, source evidence, artifact paths, and downstream blockers in the owning requirement files.
- Stop before `technical-design` or `plan-eng-review` when gate state, evidence, decisions, or approval status disagree.

## Inputs

- Required: `requirements/<requirement-id>/requirements.md`
- Required state: `requirements/<requirement-id>/progress.md`, `decisions.md`, and `evidence.md`
- Optional: existing local docs, code, specs, plans, prior research, or official/primary external sources when required by the research question

## Output

Write or update:

```text
requirements/<requirement-id>/research.md
```

Also update:

- `requirements/<requirement-id>/progress.md`
- `requirements/<requirement-id>/decisions.md` for material decisions
- `requirements/<requirement-id>/evidence.md` for source evidence and artifact paths

If research is not required, do not create a narrative artifact just to fill the gate. Record `Gate status: not_required` with the reason in `progress.md`.

## Scope Protection

- Do not change requirement scope.
- Do not add, remove, weaken, or reinterpret accepted functional requirements.
- Do not reject a requirement only because implementation is difficult.
- Requirement Impact must be marked explicitly and requires user approval before downstream gates continue.
- If user approval changes `requirements.md`, prior research decisions become `stale_needs_recheck` until revalidated or rerun.

## Workflow


Before marking a decision settled, check for contradictions between `repo_local` and `official_primary` evidence, or between current and prior evidence. If a contradiction exists, name the contradiction explicitly, record both sides in `evidence.md` with source class and supported claim, classify whether it blocks downstream planning, and use `blocked` or `stale_needs_recheck` unless the conflict is resolved by a documented decision. Do not smooth over disputed facts or present them as settled.

1. Read `requirements/<requirement-id>/requirements.md`, then current `progress.md`, `decisions.md`, and `evidence.md`.
2. Determine whether the research gate is required. If there are no decision-bearing unknowns, update `progress.md` with `Gate status: not_required`, record the reason, and stop without creating `research.md`.
3. Extract the research questions that affect implementation planning, including external dependencies, cost, security, compliance, performance, model behavior, or architecture pattern choices.
4. Gather evidence from local repo sources first for repo-specific questions; use web or external sources only when the facts are external, current, source-sensitive, or required by policy.
5. Write `research.md` with decisions, rationale, alternatives, risks, Requirement Impact, unresolved items, and gate self-review.
6. Update `decisions.md` with material research decisions and `evidence.md` with source evidence plus the `research.md` artifact path.
7. Reconcile the gate tuple across `progress.md`, `research.md`, `decisions.md`, and `evidence.md`.
8. Mark the gate `completed` only when every unresolved item is classified, no Requirement Impact is awaiting approval, and the tuple is coherent; otherwise mark `blocked`, `awaiting_user_approval`, or `stale_needs_recheck`.
9. Report the artifact path, decision count, blocking unresolved count, Requirement Impact status, and state-file updates.

## Gate State Contract

Use the requirement progress vocabulary:

- `not_evaluated`
- `required_pending`
- `in_progress`
- `completed`
- `not_required`
- `blocked`
- `awaiting_user_approval`
- `stale_needs_recheck`

Artifact existence alone is insufficient. A completed research gate requires a coherent tuple:

- `progress.md` records `Gate: research`, `Gate status: completed`, reason, and artifact path.
- `research.md` exists under the owning requirement folder.
- `evidence.md` records source evidence and the artifact path.
- `decisions.md` records or references material decisions.
- Every unresolved item is classified as `blocking` or `non_blocking` with rationale and downstream owner.
- No Requirement Impact is awaiting user approval.

If these surfaces disagree, record `stale_needs_recheck` or `blocked` and do not continue to `technical-design` or `plan-eng-review`.

## Research Topics

Look for:

- technical unknowns or `NEEDS CLARIFICATION` items
- external APIs, third-party services, standards, pricing, model behavior, or platform rules
- security, privacy, compliance, performance, scalability, cost, or operability constraints
- domain-specific constraints
- architecture pattern choices that affect downstream design

Prefer local repository docs and code when the question is repo-specific. Use web research only when required by current policy or when the facts are external, temporally unstable, or source-sensitive. Prefer primary/official sources for technical decisions.

## Artifact Shape

Use this structure:

```markdown
# Technical Research: <Requirement Title>

Created: <YYYY-MM-DD>
Status: Complete | Partial | Blocked | Awaiting User Approval
Requirement source: requirements/<requirement-id>/requirements.md

## Research Decisions

### RD-001: <Topic>

- Question:
- Decision:
- Rationale:
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
- Risk:
- Evidence:

## Requirement Impact

- None, or:
- Impact:
- Affected requirement:
- Alternatives:
- Approval status: requires user approval

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |

## Gate Self-Review

- All technical unknowns from the requirement were addressed or classified.
- Every decision has rationale and alternatives, unless a standard path is justified.
- Requirement Impact is absent, approved, or explicitly recorded as blocking/awaiting approval with the gate not completed.
- Every unresolved item is classified as blocking or non_blocking.
- Evidence paths/sources are recorded in evidence.md.
```

## Completion

Report:

- `research.md` path
- decision count
- unresolved blocking count
- Requirement Impact status
- progress/decisions/evidence updates

Return blocked instead of completed when blocking unresolved items, degraded research sources, stale evidence, or Requirement Impact approval remain open.

## Anti-Patterns

- Creating a narrative `research.md` when the gate should be `not_required`.
- Treating artifact existence as completion while `progress.md`, `decisions.md`, or `evidence.md` are missing or inconsistent.
- Using broad web summaries when repo docs, source code, official docs, standards, or primary sources are required.
- Changing, weakening, or rejecting accepted requirements under the cover of research.
- Leaving Requirement Impact implied instead of explicitly recording approval status.
- Passing blocking unresolved items downstream as ordinary implementation notes.
- Continuing to `technical-design` or `plan-eng-review` after stale evidence, degraded sources, or gate-state disagreement.
