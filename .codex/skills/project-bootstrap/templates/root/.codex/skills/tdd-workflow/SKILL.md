---
name: tdd-workflow
description: Use this skill for most bounded implementation, bugfix, or behavior changes. Prefer failing-test-first TDD, but apply it pragmatically.
---

# Test-Driven Development Workflow

reference @./references/tdd-rules.md
reference @./references/verification-checklist.md

This skill is the default workflow for bounded implementation work. Use it when the next step is a small or medium code change that should be driven or constrained by automated verification, even if a bit of context gathering is still needed before the first test.

## Use When

- Implementing a bounded feature or bugfix
- Changing observable behavior
- Adding regression coverage before or during refactoring
- Converting a bug report into a reproducible failing test
- Making a small or medium code change where tests should lead or tightly constrain the implementation

## Do Not Use

- Writing or clarifying product specs
- Large multi-milestone orchestration with no clear next implementation slice
- Pure documentation changes
- Configuration-only changes with no meaningful automated verification path
- Refactors with no observable behavior and no realistic regression coverage to add

## Workflow

1. State the target behavior and success condition in one sentence.
2. Convert the requirement into executable acceptance criteria before choosing the test shape.
3. Classify the verification problem and name the evidence type that can honestly prove it.
4. Load only the minimum code context needed to write the next test.
5. Write one test for one behavior using real code paths whenever possible.
6. Run that test and confirm it fails for the expected reason.
7. Write the minimum production code needed to make that test pass.
8. Re-run the targeted test, then the relevant broader suite, and keep the output clean.
9. Refactor only after green, while preserving passing tests.
10. Report proof that red was observed, green was observed, and broader verification ran.

## Verification Strategy Selection

Before writing a test, decide what kind of proof the change needs:

- Deterministic verification: use PASS/FAIL tests for convergent behavior such as business rules, parsers, data mapping, state transitions, and pure logic.
- Empirical verification: use browser runs, screenshots, accessibility checks, or performance measurements for UI, layout, interaction, and runtime-behavior claims.
- Probabilistic verification: use LLM judges, rubrics, median-of-N scoring, and deterministic guardrails for divergent LLM or subjective-quality outputs.
- Runtime verification: use production metrics, logs, alerts, staged rollout checks, and rollback criteria when correctness depends on real traffic or environment shape.
- Migration verification: for DB, Flyway, schema, backfill, or compatibility work, verify upgrade, downgrade or repair assumptions, data integrity, old/new version overlap, and rollback or forward-fix paths.

When one request mixes multiple proof types, decompose it by subtask and use
the canonical label for each item. Example: tax rounding uses `Deterministic
verification`, dashboard visual polish uses `Empirical verification`, and LLM
summary quality uses `Probabilistic verification`. Give each subtask executable
acceptance criteria before choosing its test or rollout evidence.

Turn vague requirements into executable acceptance criteria:

- Name the observable behavior, invariant, or user-visible outcome.
- State the evidence that makes it pass or fail.
- Name the verification commands before coding when the task contract or repo policy makes them knowable.
- Prefer Example-Based Testing when named examples define the contract.
- Add property-based testing when invariants should hold for all generated inputs.
- For parsers and file formats, combine Example-Based Testing for named cases with property-based checks that valid and invalid generated inputs return a clear result or error instead of a crash.
- Use round-trip, metamorphic, property, or formal constraint checks when no single expected output exists.
- Keep runtime verification as an added rollout contract, not a substitute for local verification that can run before deploy.

## Pragmatic Exception Path

Use failing-test-first as the default for observable behavior changes, bugfixes, and refactors where a realistic regression test can be written.

Do not force a new failing test when the work is limited to UI polish, documentation, configuration, verification scripts, formatting, generated metadata, or a tiny change already covered by existing tests. In those cases:

1. Name why a new failing test would be artificial or duplicative.
2. Identify the existing tests, snapshots, checks, screenshots, or manual inspection that constrain the change.
3. Make the smallest scoped edit.
4. Run the narrowest relevant verification, then the repo-required broader verification.
5. Report the exception evidence instead of claiming a red/green cycle happened.

If an exception reveals behavior risk, convert it back into the normal failing-test-first workflow before editing production behavior.

For verification scripts, a failing command or failing fixture can be the red proof when it demonstrates the missing verifier behavior directly.

## Output Format

Report the implementation proof in this shape:

- `Target behavior`: the one behavior or bounded change being made.
- `Acceptance criteria`: the executable PASS/FAIL, empirical, probabilistic, runtime, or migration contract.
- `Verification strategy`: one canonical label, or a subtask map using `Deterministic verification`, `Empirical verification`, `Probabilistic verification`, `Runtime verification`, and `Migration verification`.
- `TDD path`: `red/green/refactor` or `pragmatic exception`.
- `Red proof`: failing test command and expected failure, or `not applicable` with exception evidence.
- `Green proof`: targeted verification that passed.
- `Broader verification`: relevant suite or `scripts/verify` result.
- `Remaining gaps`: any live, visual, manual, runtime, or broader proof that could not run.

## Non-Negotiables

- No production behavior code before a failing test unless the pragmatic exception path applies.
- Do not choose the test shape before naming the acceptance criteria and proof type.
- If the test passes immediately, the test is wrong or already-covered behavior; fix the test before coding.
- Do not keep prewritten implementation as reference while writing the test.
- Prefer behavior tests over mock-heavy implementation tests.
- Do not expand scope beyond the current failing test.

## Anti-Patterns

- Treating UI polish, documentation, configuration, or verification script cleanup as if it must always invent a failing product test.
- Claiming TDD when no red proof was observed.
- Using the exception path to avoid testing a behavior change.
- Reporting existing tests vaguely instead of naming the concrete exception evidence.
- Using runtime verification to skip local proof that can be run before deploy.
- Using only example tests where a clear invariant calls for property-based testing.
- Expanding from a small test-led fix into opportunistic cleanup.
