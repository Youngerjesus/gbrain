---
name: closed-loop-harness
description: Design and implement repo-native closed loop agent harnesses. Use when a task needs loop convergence design, hard-gate PASS or FAIL loops, attempt/reject ACCEPT RETRY REJECT loops, evaluator-generator or revise loops, scored improvement loops, exploration/search-prune loops, diagnosis loops, contract gauntlet preflight, runtime dependency allowlists, downstream artifact handoff checks, trace-driven agent improvement, independent review and adjudication for loop work, artifact inspection for harness verification, stall recovery for loop verification flows, or proof that a produced harness ran generator to evaluator to generator before claiming completion.
---

# Closed Loop Harness

Use this skill to turn complex agent work into a bounded loop with explicit evaluation, trace evidence, and stop/retry/reject rules. The default output is a repo-native minimal shared harness plus one or more domain adapters, not a universal evaluator or a language-locked framework.

## Workflow

1. Inspect the target project before designing the loop:
   - Read the nearest `AGENTS.md` and any project-specific guidance.
   - Find existing architecture, test commands, eval commands, scoring scripts, review flows, trace/log conventions, and partial loop harnesses.
   - If an existing or partial harness is present, decide whether to reuse, extend, replace, or defer. Do not overwrite an existing loop blindly.
2. Run the loop-fit gate:
   - Name the target state, current state, distance signal, failure-cause signal, allowed intervention size, iteration budget, stop condition, fail-fast condition, and evidence source.
   - If distance cannot be measured or failure causes cannot be narrowed, do not pretend a reliable loop can be built. Recommend exploration, instrumentation, a clearer rubric, or human clarification.
   - If the task is simple enough for a direct pass, say that a loop is unnecessary.
3. Choose the loop family or hybrid:
   - Hard gate for strict `PASS` / `FAIL`.
   - Attempt/reject for uncertain feasibility with `ACCEPT`, `RETRY`, and `REJECT`.
   - Exploration/search-prune for hard problem search.
   - Revise/evaluator-generator for bounded feedback-driven artifact improvement.
   - Diagnosis for narrowing causes before intervention.
   - Read [references/loop-taxonomy.md](references/loop-taxonomy.md) when loop choice, convergence, or hybrid transitions are non-trivial.
4. Write a harness design packet before coding:
   - Use [assets/templates/harness-design-packet.md](assets/templates/harness-design-packet.md) when the project lacks its own format.
   - Include shared harness responsibilities, adapter responsibilities, actors, states, evaluation method, trace schema, running log fields, stop/retry/reject rules, Goodhart risks, contract gauntlet checks, runtime dependency allowlists, downstream artifact contract preflight, convergence cost controls, deterministic batch repair policy, and 1.5 validation evidence.
   - Apply the same packet update when reusing, extending, replacing, or deferring an existing or partial harness. Prior preflight evidence is reusable only when freshness is proven for the current artifact, adapter, runtime dependency snapshot, evaluator contract, and downstream consumers.
5. Implement repo-native code only after the design packet is coherent:
   - Put common lifecycle mechanics in the shared harness.
   - Put domain judgment in adapters.
   - Prefer existing project test/eval tooling and local conventions.
   - Improve one meaningful `critical` or `major` issue per iteration unless the repo or domain has a deterministic batch repair mechanism.
   - When evaluator feedback has findings, prefer one primary finding or next-focus item per iteration. Secondary observations may be recorded, but they should not diffuse the next generator action unless a deterministic batch repair path exists.
   - Before expensive, provider-dependent, multi-agent, renderer/deployer/tool, or full live execution, run a small Contract Gauntlet when objective handoff facts can be checked. Identify each generated-output boundary, downstream consumer, required runtime dependency, candidate artifact identity, and deterministic or structured preflight available.
   - Use structured state, typed records, schemas, parsers, or deterministic validators where available. Do not decide `PASS`, `FAIL`, `ACCEPT`, `RETRY`, `REJECT`, severity, or evidence quality from substring presence.
   - Read [references/harness-contract.md](references/harness-contract.md) before coding shared state, trace, actor, adapter, resume, or multi-root behavior.
6. Validate any produced harness with at least 1.5 iterations:
   - Required flow: `generator -> evaluator -> generator`.
   - Prove the second generator action consumed evaluator feedback using trace linkage: feedback id or category -> generator action -> changed artifact or diff -> next eval result or decision.
   - Run focused tests for shared harness state/stop behavior and at least one adapter or fixture.
   - Run a deterministic smoke fixture with a sample adapter when practical; run a real domain pilot only when a safe local target and verification path exist.
   - The harness is not verified from file existence, green structural checks, or a repeated first generation.
7. Evaluate and review:
   - Prefer deterministic checks for objective facts, schema, formats, executable behavior, and merge gates.
   - Use LLM judges only with explicit rubrics, observable criteria, and accept/reject standards.
   - Read [references/llm-judge-design.md](references/llm-judge-design.md) before adding or changing an LLM judge, judge prompt, verdict schema, or judge-driven retry/reject decision.
   - Inspect visual or file artifacts directly when available through screenshots, image tools, rendered output, logs, traces, or local files.
   - Use independent reviewers when review quality matters. Use about three high-signal perspectives for multi-review and an adjudicator to filter false positives and conflicting findings.
   - Read [references/verification-and-review.md](references/verification-and-review.md) before claiming verification, using LLM judges, handling malformed evaluator output, running review agents, or dealing with stalls.
8. Report honestly:
   - Separate skill or harness validation from real domain pilot quality.
   - Separate targeted improvement from regressions and worsening.
   - Record skipped, blocked, flaky, quota-limited, provider-dependent, or stalled checks as missing evidence, not success.
   - Stop only by explicit pass, accept, reject, retry budget, fail-fast, or human-escalation rules.

## Minimum Produced-Harness Contract

Every harness produced by this skill must define:

- shared lifecycle, state transitions, iteration budget, stop/retry/reject/fail-fast conditions, trace schema, evaluation record shape, reviewer/judge contracts, artifact inspection hooks, and running-log requirements;
- adapter-owned domain goals, artifact targets, downstream artifact consumers, runtime dependency allowlist, artifact contract preflight, scoring or rubric criteria, severity classification, prune criteria, thresholds, and evidence sufficiency rules;
- a running log with current best score or state, what changed this round, what improved, what worsened, next thing to try, and remaining risks;
- trace evidence for task/request, input artifact or candidate, generator output, evaluator feedback, next generator action, evaluation result, stop/retry decision, and unresolved risk.

## Starter Prompt

Use this starter when invoking the skill in a target project:

```text
Use $closed-loop-harness for this task. Read AGENTS.md first. Find existing scoring, eval, test, trace, artifact inspection, and runtime dependency patterns. Decide whether a loop is appropriate and convergent. If it is, design a repo-native shared harness plus adapter, declare runtime dependency allowlists, identify downstream artifact consumers, run contract gauntlet preflight before expensive/full live execution when objective handoff facts can be checked, improve one major or critical issue at a time unless deterministic batch repair is safe, rerun eval after each improvement, record score or finding changes, inspect visual or file artifacts directly when relevant, and stop only by explicit pass, accept, reject, budget, fail-fast, blocked, or escalation rules. Do not claim the harness is verified until generator -> evaluator -> generator ran with trace evidence that the second generator consumed evaluator feedback.
```

## Resources

- Read [references/loop-taxonomy.md](references/loop-taxonomy.md) for loop families, convergence prerequisites, reject paths, and hybrid selection.
- Read [references/harness-contract.md](references/harness-contract.md) for shared harness versus adapter ownership, actor authority, state and trace records, existing-harness reuse, polyglot targets, and resume behavior.
- Read [references/llm-judge-design.md](references/llm-judge-design.md) for measurable LLM judge design, verdict schemas, evidence refs, false-pass/false-fail calibration, and rubric criteria.
- Read [references/verification-and-review.md](references/verification-and-review.md) for evaluation design, Goodhart safeguards, artifact inspection, independent review, adjudication, stall recovery, blocked-run reporting, and semantic coverage checks.
- Copy [assets/templates/harness-design-packet.md](assets/templates/harness-design-packet.md) when the target project lacks a harness design or report format.
