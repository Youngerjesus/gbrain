# Result Artifact Contract

Every promptfoo-backed run must preserve enough evidence for a later reader to understand what was tested.

## Required Files

Result directories must contain:

```text
results.json
report.html
```

Prefer:

```text
.runtime/promptfoo/<timestamp>-<label>/
```

## Required Report Fields

Report:

- prompt or instruction files evaluated
- execution mode
- config path
- command
- provider
- result artifact path
- baseline-vs-candidate or candidate-only
- targeted pass/fail summary
- regression pass/fail summary
- skipped, flaky, provider-dependent, or blocked checks
- supplemental evidence such as static checks, subagent review, or unit tests

## Evidence Strength

- **baseline-versus-candidate** proves an observed behavior delta when baseline and candidate used comparable configs, providers, vars, and assertions.
- **candidate-only** proves current behavior only. It does not prove improvement from the prior prompt.
- **static-only blocked** is not promptfoo-backed evidence. Use it only when promptfoo execution failed or could not be run, and preserve the blocker.

Do not use overall pass rate alone. Targeted feedback and regression suites must be reported separately.
