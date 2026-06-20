# Verification And Review

Use this reference before claiming a harness is verified, using LLM judges, handing work to independent reviewers, handling stalls, or reporting blocked checks.

## Evaluation Design

Each loop needs at least one explicit evaluation method:

- deterministic score or test;
- external tool metric;
- structured finding review;
- LLM judge rubric;
- direct artifact inspection;
- justified combination of the above.

Prefer deterministic checks for objective facts, schema, formats, executable behavior, and merge gates. Use LLM judges for qualitative criteria only when they have:

- a rubric written before judging;
- observable criteria;
- pass and fail standards;
- severity calibration;
- examples or failure modes where practical.

Vague natural-language approval is weak evidence and must not override deterministic failures.

## Goodhart Safeguards

Do not optimize a proxy score while hiding real-objective regressions. Every evaluation report should separate:

- targeted improvement;
- aggregate or proxy score movement;
- critical/major blockers;
- regressions or worsening;
- latency, cost, safety, UX, maintainability, or other non-target risks;
- why the current decision is not just score chasing.

A high aggregate score is not sufficient if a critical requirement fails.

## 1.5 Validation Gate

A produced harness is not verified until it executes or deterministically simulates:

```text
generator -> evaluator -> generator
```

Required evidence:

- first generator output;
- evaluator feedback with stable feedback id or category;
- second generator action naming or linking the consumed feedback;
- artifact change, diff, branch choice, or diagnostic narrowing caused by that feedback;
- next evaluation result or explicit stop/retry decision.

If the real first generator output already passes, record that pass evidence, but do not call the produced harness verified from that path alone. Run a deterministic fixture or simulation where the evaluator returns at least one meaningful issue and the second generator consumes it, or report produced-harness verification as incomplete or blocked.

Use the target repo's focused tests for shared state transitions, stop conditions, and at least one adapter or fixture. A deterministic fake runner, local fixture, or dry-run harness test is acceptable when live subagents, providers, or real-domain checks are unavailable. Report those fallbacks as harness wiring evidence, not proof of production domain quality.

Run a real domain pilot when the project has a safe local target and evaluation path. The pilot only needs to demonstrate loop wiring, trace capture, adapter criteria, artifact target binding, and evaluator feedback consumption unless the user explicitly requires production-quality domain performance.

## Contract Gauntlet Preflight

Before full live execution, run a small deterministic fixture, parser/schema check, artifact inspection, renderer/tool smoke, or mini 1.5 loop when the full path is expensive, slow, quota-limited, provider-dependent, or crosses multiple agent/runtime/downstream-consumer boundaries.

This preflight is evidence of wiring and objective handoff facts, not proof of production domain quality. If deterministic preflight is unavailable, record the weaker evidence and the missing check explicitly instead of treating full live execution as equivalent contract proof.

Preflight reports should distinguish:

- `contract_preflight_failed`;
- `runtime_dependency_blocked`;
- `provider_blocked`;
- `quota_blocked`;
- `credential_blocked`;
- `stale_artifact_rejected`;
- `evaluator_quality_failed`;
- `fixture_only_evidence`;
- `weak_or_missing_preflight`.

Malformed, partial, stale, provider-blocked, quota-blocked, credential-blocked, or stalled runtime output is blocked/error evidence, not success. A valid-looking structured envelope still fails preflight when artifact identity, provenance, evidence refs, runtime snapshot, or cache freshness is invalid.

## Artifact Inspection

For visual, rendered, generated, or otherwise inspectable artifacts, direct inspection is required when tools are available:

- screenshot or rendered browser output;
- local image viewing;
- generated files;
- logs;
- traces;
- command output;
- serialized state.

Do not rely only on a text summary of an artifact when the actual artifact can be opened safely.

## Malformed, Partial, Flaky, Or Stale Evidence

- Malformed evaluator or judge output: mark the iteration `BLOCKED` or rerun with a schema repair path; do not coerce text into success.
- Partial output: record what is missing and whether the missing field blocks state transition.
- Flaky evaluator: rerun or cluster results according to the target repo's reliability rules; do not let a lucky pass become completion proof.
- Stale artifact: reject feedback or scores unless their artifact ref matches the current candidate.
- Quota, credential, provider, browser, or subagent unavailability: report blocked or skipped evidence separately.
- Runtime dependency mismatch: block or record an adapter exemption when a child agent, subprocess, worker, browser, plugin, provider, or MCP dependency did not receive the intended run-local environment.

## Independent Review

Independent reviewers are useful because the producing session is prone to rationalization and confirmation bias. Handoff packets should include:

- diff or artifact;
- requirements;
- verification method;
- execution trace;
- evaluation output;
- relevant artifact evidence;
- known constraints and blockers.

Use a small number of high-signal perspectives, approximately three when multi-review is useful. Track review quality through false positives, false negatives, missed issues, severity calibration, and actionability.

If multiple reviewers are used, an adjudicator or judge must reconcile findings before they become required work. Count of reviewers is not evidence by itself.

## Stall Recovery

For subagent, external tool, or `codex exec` verification flows:

- treat about 10 minutes without meaningful update as a stall signal unless the project defines a longer expected silence;
- record last meaningful update, command or agent id if safe, partial trace, attempted recovery, and reason for restart/resume;
- restart or resume according to project context instead of waiting indefinitely;
- do not claim a stalled run passed.

## Blocked-Run Report

When verification cannot run, report:

- required check;
- why it could not run;
- what evidence exists instead;
- why that evidence is weaker;
- what would unblock the check;
- whether completion is blocked or only a future domain pilot remains.

## Semantic Coverage Checklist

For a new or updated closed-loop harness skill or harness, check coverage semantically rather than by keyword:

- target repo context inspection before implementation;
- shared harness versus adapter ownership and "must not own" boundaries;
- all selected loop family state semantics;
- convergence gate and reject path;
- critical/major before minor polish;
- one meaningful intervention per iteration unless deterministic batch repair exists;
- deterministic and LLM judge evidence separation;
- Goodhart and regression safeguards;
- artifact inspection when possible;
- trace and running-log fields;
- independent review and adjudication;
- stall recovery and blocked-run reporting;
- runtime dependency allowlists with declared required tools/MCPs allowed and ambient/global inheritance rejected by default;
- Contract Gauntlet stages before expensive/full live execution when objective handoff facts can be checked;
- downstream artifact contract preflight for producer, consumer, artifact identity, schema/format, evidence/provenance owner, failure classification, and verification method;
- stale, partial, provenance-invalid, and structured-but-wrong outputs rejected separately from malformed outputs;
- weak/no deterministic preflight reported as weaker evidence;
- artifact bundle or graph handoffs and dynamically discovered downstream consumers;
- preflight re-entry, duplicate/concurrent handling, freshness binding, and failed-stage quarantine/no-promotion behavior;
- deterministic batch repair policy with safe grouping, non-conflicting scope, regression checks, and rollback/split/fail-fast handling;
- 1.5 validation with feedback consumption linkage;
- portability across project roots, languages, and domains.
