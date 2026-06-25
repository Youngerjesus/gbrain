# SkillOpt Process

## Ported From Gbrain

This reference preserves the gbrain SkillOpt internal process in Codex-native terms.

The original decomposition maps cleanly:

- `benchmark`: JSONL loader, schema validation, deterministic train/sel/test split, `D_sel >= 5`.
- `score`: rule, LLM, or retrieval-style judges. The Codex deterministic helper currently implements rule scoring; LLM and retrieval judges are adapter-owned live boundaries.
- `apply-edits`: body-only `add`, `replace`, and `delete` with frontmatter and code-fence guards.
- `validate-gate`: median-of-3, epsilon margin, selection-set acceptance.
- `held-out`: independent benchmark-disjoint safety set before direct mutation.
- `version-store`: history-intent-first writes to avoid half-accepted skill states.
- `rejected-buffer`: bounded record of edits that were tried and did not pass.
- `preflight`: dirty target check, budget check, benchmark validation, and runtime dependency declaration.

## Codex Harness Boundary

The shared deterministic core lives at
`.codex/skills/skill-optimizer/scripts/skillopt_core.py`. It owns parsing,
splitting, scoring, safe edit application, and validation math.

The local runner lives at
`.codex/skills/skill-optimizer/scripts/skillopt_runner.py`. It owns the
Codex-native bootstrap, reviewed dry-run, candidate validation gate, and version
artifact writes. The gbrain command flow maps to:

```bash
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-from-skill
# Human strengthens judges and deletes # BOOTSTRAP_PENDING_REVIEW.
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --dry-run
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --candidate candidate.md --proxy-from-skill-text
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --candidate candidate.md --rollouts rollouts.json --baseline-score 0.72
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --live --max-llm-calls 80
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --live --provider codex --max-llm-calls 80
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --live --held-out held-out.jsonl --mutate
```

Pass `--held-out held-out.jsonl --held-out-rollouts held-out-rollouts.json` to
the deterministic candidate path to require an independent disjoint held-out
gate before promotion. Pass `--held-out held-out.jsonl` to the live path to run
the held-out gate with target-model rollouts. Direct mutation requires held-out
evidence in both paths.

`--proxy-from-skill-text` is a local rule-judge proxy mode. It is useful for
checking whether a candidate skill body covers benchmark criteria, but it is not
evidence that a live agent executed the benchmark tasks.

`--live` is the closed-loop mode: it runs target-model rollouts over benchmark
tasks through the Gemini API by default, scores them, asks the optimizer model
for body-only edits, applies safe edits, and reruns the selection gate before
promotion. Default live models are `gemini-2.5-flash` for target/judge
evaluation and `gemini-3.5-flash` for optimizer edit synthesis. Pass
`--provider codex` to use `codex exec` with Codex defaults. Codex rollout calls
are allowed at least 10 minutes each. The repo baseline uses a fake chat client to verify
loop wiring. Real API smokes are request-local: run the `--live` command directly
with explicit `--provider`, model flags, `GEMINI_API_KEY`, or the `SKILLOPT_*`
environment variables when live auth is present.
Same-model target/optimizer runs are useful for low-cost smoke tests. For real
optimization, keep the target model representative of normal skill execution
and use a stronger optimizer model such as `gemini-3.5-flash` for edit
synthesis.
The live runner records a duplicate-run lock, checkpoint, trace, receipt,
rejected edit buffer, LLM call count, and Codex JSON event-derived tool calls
when the CLI emits them.

The live adapter owns:

- how the candidate skill is executed;
- how LLM reflect calls are made;
- which model/provider/subagent executes target rollouts;
- how tool-call traces are captured;
- how cost or call budgets are enforced.

Do not hide live execution behind a deterministic script without declaring the runtime dependencies and evidence gaps.

## Benchmark Shape

Each benchmark row is one JSON object:

```json
{"task_id":"x-001","task":"User-like prompt","judge":{"kind":"rule","checks":[{"op":"max_chars","arg":1800}]}}
```

Rule operations include `contains`, `regex`, `section_present`, `max_chars`,
`min_citations`, `tool_called`, `tool_not_called`, and `mapping_contains`.
Use `mapping_contains` when a benchmark needs structured Markdown evidence such
as task-to-strategy mappings instead of independent phrase presence checks:

```json
{"op":"mapping_contains","arg":{"items":[{"key":"tax rounding","value":"Deterministic verification"}]}}
```

Rule judges are cheap proxies. They can drive local loop wiring, but direct mutation of shared skills should also use held-out checks or human review.
