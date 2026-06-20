# Promptfoo Eval Design

Use this reference when a prompt change needs new or updated promptfoo coverage.

## Coverage Contract

Define the eval before trusting the prompt edit:

- feedback: the concrete user or reviewer feedback being addressed
- behavior delta: what should change in model output
- non-regression: what must stay true
- evidence strength: baseline-versus-candidate, candidate-only, or static-only blocked evidence
- assertion strategy: deterministic, LLM judge, or mixed

## Baseline And Candidate

Prefer this sequence:

1. Run baseline eval on the current prompt and save artifacts.
2. Edit the prompt.
3. Run candidate eval using the same config, provider, vars, filters, and assertions.
4. Compare targeted cases and regression cases separately.

Candidate-only is acceptable when baseline is unavailable, but the report must say that it proves current behavior, not improvement from the prior prompt.

## Assertion Selection

Use deterministic assertions when the expected property can be mechanically checked:

- exact or partial text requirements
- forbidden content
- JSON validity or schema shape
- numeric thresholds
- classification labels
- JavaScript or Python predicates

Use LLM judge assertions when the expected property requires qualitative judgment:

- helpfulness or completeness
- tone or brevity
- instruction hierarchy
- refusal quality
- reasoning quality
- policy interpretation

Use both when an output must satisfy a hard interface and a qualitative standard.

## Test Case Shape

Good cases include:

- a clear input or vars set
- metadata labeling target versus regression cases
- assertions tied to one behavior each
- at least one negative or adversarial case for meaningful judge rubrics

Avoid broad "is better" tests. Split them into observable claims.

## Result Reporting

Report at least:

- command run
- config path
- prompt paths
- provider or provider family
- result artifact path
- targeted pass/fail summary
- regression pass/fail summary
- evidence strength
- blockers or skipped checks

Do not treat overall pass rate as sufficient when targeted feedback cases failed or regressions worsened.
