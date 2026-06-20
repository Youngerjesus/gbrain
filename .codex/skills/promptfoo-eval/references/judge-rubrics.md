# Judge Rubrics

Use this reference before relying on LLM judge assertions.

## Rubric-First Standard

Every qualitative judge assertion must define:

- evaluation target: one behavior being judged
- pass criteria: what must be present
- fail criteria: what must be absent or unacceptable
- negative examples or failure modes
- threshold or pass/fail expectation when supported by the assertion

Promptfoo `llm-rubric` supports scoring thresholds. Use a threshold when score quality matters, because score alone may not determine pass/fail unless the assertion is configured to enforce it.

## Rubric Pattern

Write rubrics like this:

```text
Pass if the answer directly addresses the user's request, gives the final recommendation before caveats, and does not invent unsupported facts.
Fail if it avoids the main question, buries the answer behind generic caveats, introduces facts not present in the input, or asks for unnecessary clarification.
Negative examples: generic safety caveat first; unsupported specific claim; "it depends" without a decision.
```

## Anti-Patterns

Avoid:

- "Is this good?"
- "Does this follow the prompt?"
- "Prefer concise answers"
- one rubric that combines tone, factuality, format, and refusal behavior
- judge-only validation for JSON shape, exact labels, or forbidden strings

Split broad concerns into deterministic assertions plus one or more focused judge rubrics.

## Handling Flaky Judges

If judge results are unstable:

- rerun only the affected slice when cost allows
- tighten the rubric
- add negative examples
- add deterministic assertions for hard requirements
- report residual flakiness instead of hiding it
