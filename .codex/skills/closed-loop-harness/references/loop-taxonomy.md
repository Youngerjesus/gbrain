# Loop Taxonomy

Use this reference when choosing a closed-loop family, deciding whether convergence is plausible, or combining loop styles.

## Convergence Gate

A loop is allowed only when the design can name all of these:

- target state: what good enough means for the artifact, search result, diagnosis, or decision;
- current state: the artifact, candidate, hypothesis set, score, or failure state being improved;
- distance signal: deterministic score, structured finding delta, rubric result, branch ranking, narrowed hypothesis set, or other observable gap;
- failure-cause signal: why the current state failed or what evidence can narrow the cause;
- intervention size: the smallest meaningful change per iteration, normally one `critical` or `major` issue at a time;
- stop condition: pass, accept, reject, retry budget, no remaining high-severity issue, fail-fast, or escalation;
- fail-fast condition: evidence that more iteration is not worthwhile, unsafe, too costly, non-convergent, or blocked by missing input;
- regression signal: how worsening is separated from targeted improvement;
- convergence economics: estimated expensive calls, deferred finding count, repeated failure categories, safe batchability, fail-fast cost triggers, and retry budget rationale.

If distance cannot be measured or failure causes cannot be narrowed, do not build a revise or hard-gate loop yet. Use exploration, instrumentation, rubric design, or human clarification.

Minor issues may be logged, but they should not keep a loop running unless the user explicitly requests polish.

Default to one primary intervention per iteration. Deterministic batch repair is appropriate only when the adapter defines safe grouping criteria, non-conflicting target scope, and regression checks. If a batch partially succeeds, introduces regressions, or touches conflicting scopes, split back to single-finding repair, do not promote the candidate, roll back where the repo workflow supports it, or fail fast.

## Hard Gate Loop

Use for strict acceptance where evidence can be checked as `PASS` or `FAIL`.

- Best evidence: deterministic tests, schemas, parsers, executable checks, validated score thresholds, or structured policy outputs.
- State: `RUNNING`, `PASS`, `FAIL`, `FAIL_FAST`, `BLOCKED`.
- Continue when a major or critical failure has a plausible next repair.
- Stop when the gate passes, retry budget is exhausted, the failure repeats without a new cause, or a fail-fast condition is met.
- Avoid: using vague judge text as the gate authority, or treating a high aggregate score as pass while a critical requirement fails.

## Attempt And Reject Loop

Use when feasibility is uncertain and attempts may legitimately fail.

- State: `ACCEPT`, `RETRY`, `REJECT`, plus `BLOCKED` when evidence or input is missing.
- Generator proposes or executes an attempt.
- Evaluator reports result quality and risks.
- Judge decides whether more retry is worthwhile.
- Reject when evidence shows the path is infeasible, unsafe, too costly, lacks a measurable signal, or repeatedly fails for the same major cause.
- Accept only with evidence mapped to the original target, not only because attempts improved.

## Exploration / Search And Prune Loop

Use for hard problems where the answer path is unknown.

- Track explored branches, branch scores or findings, prune reasons, remaining candidates, and the next search direction.
- Prune weak branches with explicit evidence. Do not silently discard branches.
- Move from exploration to revise or hard-gate only after a candidate target, distance signal, and failure-cause signal are clear.
- Good search records include: candidate id, premise, evidence collected, result, prune/keep decision, reason, and unresolved uncertainty.

## Revise / Evaluator-Generator Loop

Use for bounded artifact improvement.

- Required 1.5 validation shape: first generator output, evaluator feedback, second generator action.
- The second generator must make a focused revision that links to evaluator feedback.
- Evaluator feedback should classify issues as `critical`, `major`, or `minor`; broad unrelated feedback must be split before repair.
- When findings are used, evaluator feedback should prefer a single primary finding or next-focus item for the next revision. Additional findings may be logged as secondary context.
- Continue on unresolved `critical` or `major` findings with a clear next change.
- Stop when major/critical findings are closed, retry budget is reached, only minor polish remains by default, or regressions outweigh improvement.

## Diagnosis Loop

Use when the main problem is unknown cause, not artifact polish.

- Track hypotheses, evidence for and against, tests performed, eliminated causes, remaining causes, and confidence.
- Each iteration should narrow the hypothesis space or identify the next bounded diagnostic step.
- Stop when a likely root cause is identified with enough evidence to intervene, when no safe diagnostic action remains, or when human input/instrumentation is required.
- Avoid jumping to fixes before the loop has evidence that the chosen cause explains the observed failure.

## Hybrid Loops

Hybrid loops are allowed when state transitions are explicit:

- exploration -> revise after a promising candidate is selected;
- diagnosis -> hard gate after a cause is fixed and a deterministic gate exists;
- revise -> attempt/reject when repeated feedback shows uncertain feasibility;
- hard gate -> diagnosis when repeated failures cannot be repaired without cause analysis.

Do not mix loop families by blurring actor authority. The generator generates, evaluator evaluates, judge/adjudicator decides retry/accept/reject when required, and reviewer finds risks.
