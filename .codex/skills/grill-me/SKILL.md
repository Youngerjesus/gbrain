---
name: grill-me
description: "Interrogate vague ideas, plans, feature concepts, architecture sketches, or design directions before planning or implementation so the human and AI converge on a shared design concept and problem definition. Ask only critical, handoff-changing pressure questions one at a time by default, or use explicit batch mode when requested, with 2-3 suggested answer options rendered as plain text while requiring a free-form chat response path. Sequential mode has a default 5-question budget and explicit user approval for up to 5 more; batch mode is limited by criticality rather than count. Use when the user asks for grill me, pressure questions, hidden assumptions, missing requirements, decision dependencies, validation gaps, shared design concept alignment, or a handoff-ready summary for requirement-clarifier, decision-brake, scenario-brake, plan-eng-review, office-hours, or implementation planning."
---

# Grill Me

Use this skill as a pre-handoff interrogation mode. Do not evaluate, plan, or implement too early. Ask only about critical uncertainty that could change the handoff, then summarize what is now ready for the next skill or planning step.

Primary goal: make the human and AI share the same design concept, problem definition, assumptions, and handoff boundary before downstream planning or implementation begins.

## Core Posture

- Treat the user's idea as under-specified until proven otherwise.
- Ask one question at a time by default, and only when it passes the criticality gate.
- Support an explicit `Batch mode` when the user asks to receive the critical pressure questions at once. Treat prior `Batch-5 mode` wording as a legacy alias only; it never creates a five-question cap.
- Use a default budget of 5 pressure questions only in Sequential mode. Ask fewer when enough is known.
- After 5 Sequential-mode questions, do not continue automatically. Ask the user whether to extend for up to 5 more questions or synthesize now.
- Prefer uncomfortable, decision-changing questions over broad brainstorming.
- Do not interrogate facts that can be discovered from the repo, docs, configs, schemas, or existing code. Inspect those directly when available.
- Do not turn the session into requirement writing too early. The goal is to expose uncertainty first, then hand off.
- Keep pressure constructive and specific. Challenge the idea, not the person.

## Workflow

### 1. Ground the input

Start by restating the current idea in 2-4 sentences.

Identify:

- the concrete thing the user seems to want
- the most ambiguous words or claims
- the assumptions the idea depends on
- the decisions that block the next step
- the evidence that can be checked locally instead of asked about

If repository or document context can answer a factual question, inspect it before asking.

### 2. Direct-first question selection with on-demand agent refresh

The Main Pressure Interviewer should ask the first obvious, high-impact pressure question directly when grounding already exposes one. Do not treat subagent execution as mandatory before the first pressure question, and do not delay an obvious proceed/kill, outcome, or success-metric question just to populate a specialist candidate pool.

The user still experiences one coherent conversation; the specialist agents do not talk to the user.

The main agent is the **Main Pressure Interviewer**. It is not a registered subagent. It owns curation, deduplication, scoring, ordering, user-facing wording, budget tracking, synthesis, and next-skill routing.

The Main Pressure Interviewer may ask a high-impact obvious question before running a subagent round when the question passes the criticality gate from local grounding and prior answers.

Run a registered agent refresh round only when the remaining direct candidates are weak, non-critical, stale, depleted, or insufficient for deciding the next handoff-changing question. In Sequential mode, a refresh round is also appropriate before recommending the 5-question extension when the remaining uncertainty is unclear.

Required registered Codex agents:

- `grill-me-risk-finder` as **Risk Finder**
- `grill-me-alternative-finder` as **Alternative Finder**
- `grill-me-verification-finder` as **Verification Finder**
- `grill-me-handoff-reviewer` as **Handoff Reviewer**
- `grill-me-requirement-shape-finder` as **Requirement Shape Finder**

During a registered agent refresh round, each required specialist may return **up to 3 structured candidate-question records**. Skill-local role prompts, inline simulated personas, or private mental lenses are not substitutes for these registered Codex agents when the runtime allows subagents and the Main Pressure Interviewer has decided a refresh round is needed.

Each candidate record must include:

- `lens`
- `candidate_question`
- `handoff_change_reason`
- `direction_changing_answer`
- `risk_if_not_asked`
- `priority_or_severity`
- `duplicate_or_dependency_notes`

Track a structured `candidate_generation_status` for each registered agent refresh round:

- `all_required_agents_passed`: all five required agents returned valid structured output; a valid zero-candidate output is allowed when that agent found no material question.
- `no_material_candidates`: all five required agents passed and, after Main Pressure Interviewer curation, no remaining candidate passes the criticality gate.
- `blocked_unavailable`: required subagent runtime or a required registered agent is unavailable.
- `blocked_invalid_output`: a required agent returned malformed, unstructured, or unrankable output.
- `blocked_partial_generation`: at least one required agent failed after another required agent returned candidates, creating a partial generation failure.

If status is `blocked_unavailable`, `blocked_invalid_output`, or `blocked_partial_generation`, fail closed for that refresh round: report the blocker, identify which required agent or stage failed when known, discard or quarantine partial candidates, and ask the user to confirm an alternative route. Do not proceed as a successful single-agent fallback, and must not ask a user-facing pressure question from a partial pool.

If status is `no_material_candidates`, synthesize or route. Keep this distinct from blocked subagent execution. If direct questioning still has a high-impact candidate independent of the failed or empty refresh pool, ask the user whether to continue direct-first or synthesize instead of silently mixing it into the refresh result.

The Main Pressure Interviewer ranks candidate questions by handoff-changing impact, not by lens order. Default impact order:

1. proceed/kill questions that could change whether the idea should move forward
2. outcome questions that clarify desired state rather than feature artifact
3. alternative questions that could reveal a smaller, cheaper, safer, or better path
4. strict verification questions that define observable success/failure evidence
5. handoff integrity questions that separate decisions, assumptions, open questions, and route
6. requirements shape questions that clarify acceptance criteria, constraints, non-goals, decision boundaries, and whether `requirement-clarifier` can write without inventing decisions
7. scope and non-goal questions
8. final route questions

Override the default order only when a lower-ranked candidate is a prerequisite for understanding a higher-ranked one. Do not ask one question per lens mechanically.

When a user answer materially changes the idea, re-score direct candidates before selecting the next question. Regenerate with registered agents only when the remaining candidate pool is stale, depleted, or no longer produces a critical question. Do not rely on a stale candidate queue for the next question or for extension recommendations.

### 2a. Choose the interaction mode

Default to **Sequential mode**: ask one pressure question per turn, incorporate the answer, then choose the next question.

Use `Batch mode` only when the user explicitly asks for a batch, all critical questions, questions up front, or equivalent wording. Do not infer batch mode merely because the idea is broad, the user is impatient, or subagents are available.

`Batch mode` may be built with or without a registered agent refresh. Use it with or without a registered agent refresh depending on candidate quality:

- If grounding exposes enough high-impact direct candidates, curate the batch directly. Do not run a refresh round merely because batch mode was requested.
- If the direct candidate pool is weak, stale, depleted, or insufficient for the set of independent critical questions, run the registered agent refresh process from section 2 before constructing the batch.
- If a registered agent refresh round is used for batch construction, preserve the existing fail-closed semantics for `blocked_unavailable`, `blocked_invalid_output`, and `blocked_partial_generation`: report the blocker, discard or quarantine partial candidates, and do not ask from a partial pool.

The default 5-question budget does not apply in `Batch mode`. Do not pad the batch to 5 questions. Do not cap the batch at 5 questions. Batch question count is limited by the criticality gate, not by a numeric budget. A batch may contain 10 or 15 questions when each question is handoff-changing. Ask fewer when fewer questions pass the criticality gate.

Each batched question must independently pass the criticality gate and be answerable without depending on an unavailable prior answer in the same batch. If one dependency-breaking answer is needed before the remaining questions can be responsible, stay in Sequential mode for that question and explain that batching would blur the decision boundary.

Order batched questions by priority and dependency: put proceed/kill, outcome, and prerequisite questions before lower-impact scope, route, or polishing questions, and keep dependent questions after the questions they rely on. Number the questions in that order and give 2-3 suggested options under each question when useful. Preserve the free-form answer path for the entire batch, including an explicit note that the user may answer any subset, reject the options, mark a question not applicable, or answer in their own words.

After the batched answers are processed, synthesize when the critical set is exhausted or ask the next critical follow-up only when the answers reveal a new handoff-changing uncertainty. Count only answered pressure questions that produced usable decision signal; unanswered or explicitly deferred batched questions remain open decisions instead of silently counting as answered.

### 3. Run the question loop

Ask exactly one question per turn in Sequential mode.

Track `question_budget_state`:

- Sequential default round: maximum 5 pressure questions.
- Extension round: maximum 5 additional pressure questions, only after explicit user approval.
- Total default maximum: 10 pressure questions.
- Stop before the budget is exhausted when no remaining question passes the criticality gate.
- Never treat the budget as a target. It is a ceiling.
- Track `answered_pressure_question_count`.
- A specificity press after a vague, rejected, "none of these", "not applicable", or "I cannot answer yet" answer does not count as answered until it produces usable decision signal or the user explicitly declines to answer.
- In `Batch mode`, batch questions count against `answered_pressure_question_count` for synthesis bookkeeping, but they do not consume or obey the Sequential-mode 5-question budget.

Before asking, apply the criticality gate. A question is worth asking only if a plausible answer would change at least one of:

- whether the idea should proceed
- who it is for
- the success or failure criteria
- the implementation or product scope
- a major non-goal, risk, dependency, or sequencing decision
- the next skill, owner, or handoff artifact

Do not ask merely useful, interesting, preference-seeking, or polishing questions. If no candidate question passes the criticality gate, stop asking and synthesize.

Choose the next question by impact:

1. Would the answer change whether this should exist?
2. Would the answer change who it is for?
3. Would the answer change the success criteria?
4. Would the answer change scope or non-goals?
5. Would the answer change the next skill or handoff path?

If the user's answer is vague, press once for specificity before moving on.

Do not repeat answered questions. Do not ask checklist questions mechanically. Stop the loop when the remaining uncertainty is non-critical, merely nice-to-know, or no longer changes the next handoff.

### 3a. Ask for extension after 5 Sequential-mode questions

After the fifth Sequential-mode pressure question has been answered, pause and ask whether to continue. Do not ask question 6 until the user explicitly chooses to extend.

Before recommending a Sequential-mode extension, re-score or regenerate candidates so the recommendation is not based on a stale candidate queue. If important questions remain, summarize only the remaining question categories without revealing the remaining question text. If extension declined, ignored, or redirected by the user, synthesize with unresolved categories preserved.

Ask one extension question in normal chat with these suggested options:

- `Synthesize now` as the recommended option when enough handoff context exists.
- `Ask 5 more` when there are still critical, handoff-changing uncertainties.

Accept a free-form answer if the user wants a different next step, constraint, or routing decision.

Render:

```markdown
Question: We have used the first 5-question budget. Do not ask question 6 until you confirm whether I should synthesize now or continue with up to 5 more critical questions.

Suggested options:
- Synthesize now: Stop interrogation and produce the handoff summary.
- Ask 5 more: Continue only if the next questions pass the criticality gate.

You can also answer in your own words.
```

If the user extends, continue with the same criticality gate and stop after at most 5 additional questions. After the extension budget is exhausted, synthesize without asking for another extension unless the user explicitly asks to keep going.

### 3b. Present each pressure question as free-form chat with suggested options

For pressure questions, do not use Codex multiple-choice input tools or button-only choice UIs. The user must always see the normal chat composer and be able to type a free-form answer.

- Render exactly one question in plain text or Markdown.
- Provide 2-3 mutually exclusive suggested options as text under the question.
- Put the most likely or most decision-useful option first and mark it as recommended when useful.
- Treat the options as hypotheses, not as an exhaustive answer set.
- Do not require a `None` option when the question already explicitly invites free-form answers.
- Keep option labels short. Put tradeoffs or implications in the option descriptions.
- Do not use suggested options to hide ambiguity. If no responsible closed choices exist yet, ask the question in plain text and invite the user to answer in their own words.
- Accept free-form answers as first-class input. If the answer does not map to a suggested option, treat that mismatch as signal and adapt the next pressure question.

Use this shape:

```markdown
Question: <one high-impact pressure question>

Suggested options:
- A: <short label> - <impact/tradeoff>
- B: <short label> - <impact/tradeoff>

You can also answer in your own words, including "none of these", "not applicable", or "I cannot answer yet".
```

Accept either the option label or a free-form answer from the user. If the user says "none of these", "not applicable", or "I cannot answer yet", ask one follow-up that separates disagreement from missing information before moving on.

### 4. Use the pressure lenses

Use only the lenses that matter for the current idea.

- Purpose: Why should this exist now?
- User: Who is the first real user or audience?
- Pain: What concrete failure, cost, or friction does this remove?
- Success: What observable outcome proves it worked?
- Failure: What outcome proves it was the wrong move?
- Assumption: What must be true for the plan to work?
- Alternative: What simpler or existing path could solve the same problem?
- Scope: What should explicitly stay out?
- Dependency: Which decision must be made before other decisions are meaningful?
- Evidence: What can be verified instead of guessed?
- Edge: What unusual input, state, user, or timing breaks the idea?
- Handoff: What needs to be true before another skill or implementer can use this?
- Requirements shape: What user story, acceptance criteria, constraints, non-goals, decision boundaries, or iteration rules must be explicit before requirements can be written?

### 5. Synthesize when enough is known

Before routing to `requirement-clarifier`, run a **Pre-requirements lock checkpoint**. The goal is not to write final requirements, but to make the requirement-lock inputs explicit enough that `requirement-clarifier` can audit them without inventing decisions.

The checkpoint must state:

- **Requirement outcome**: the concrete desired state or behavior the requirement is supposed to produce.
- **Success metric**: the observable metric, signal, or pass/fail standard that proves the outcome happened.
- **Verification method**: how the next agent, test, reviewer, user, or operator would check the success metric.
- **Out of scope / Non-goals**: the confirmed boundary statement for excluded behavior, audience, implementation area, success definition, or follow-up work; or a clear statement that no exclusions have been confirmed yet.

If any of these four fields is missing, vague, contradictory, or based on an unconfirmed inference, do not route to `requirement-clarifier` as ready-to-lock. Either ask the next critical question or mark the missing field as an open decision in the synthesis and route to the better next skill.

When the idea is ready to hand off, produce a concise summary:

- **Core idea**
- **Problem being solved**
- **Target user / audience**
- **Requirement outcome**
- **Success metric**
- **Verification method**
- **Out of scope / Non-goals**
- **Known assumptions**
- **Risk findings**
- **Alternatives considered**
- **Open decisions**
- **Handoff concerns**
- **Recommended next skill**

Keep the summary focused on what the next agent or engineer needs. Do not fabricate acceptance criteria or technical design details that were not established.

### 6. Route to the next skill

Recommend exactly one primary next step:

- Use `requirement-clarifier` when the idea is now stable enough to define requirements, acceptance criteria, constraints, and out-of-scope items.
- Use `decision-brake` when direction, problem definition, tradeoffs, or alternatives still need a hard verdict.
- Use `scenario-brake` when state, entry paths, recovery, edge cases, or path separation are the dominant risk.
- Use `plan-eng-review` when a mini-plan exists and the next question is whether implementation should begin.
- Use `office-hours` when the idea still needs product shaping, wedge selection, or demand reasoning.

If candidate answers show `requirement-clarifier` is premature, route away from `requirement-clarifier` and preserve the synthesis plus route recommendation for the better next skill.

If none fit, recommend a direct implementation plan only when the idea is simple, low-risk, and already clear.

## Output Rules

- In early turns, output the grounding summary plus one question.
- During the loop, output only enough context to make the next question precise.
- In `Batch mode`, output the grounding summary plus the numbered batch and make the free-form answer path explicit.
- Skip non-critical questions even if they would improve the idea.
- Render suggested answer options as plain text inside the chat message. Do not use multiple-choice input tools for pressure questions; preserve a free-form answer path as the primary interaction.
- At synthesis time, output the handoff summary and next skill recommendation.
- Do not create files, specs, tasks, or implementation artifacts unless the user separately asks for that after the handoff is complete.

## Relationship To Nearby Skills

- `grill-me` exposes unclear thinking before handoff.
- `requirement-clarifier` turns a stable idea into requirements.
- `decision-brake` judges whether a direction should proceed.
- `scenario-brake` pressure-tests scenario coverage.
- `plan-eng-review` checks an implementation mini-plan before coding.
