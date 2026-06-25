---
name: skill-optimizer
description: Improve an existing Codex skill with a SkillOpt-style benchmark loop that treats SKILL.md as trainable parameters while preserving body-only edits, validation gates, held-out checks, and version history.
---

# Skill Optimizer

Use this skill when the user wants to optimize, tune, benchmark, or improve an existing Codex skill. This is the Codex-native port of gbrain `skill-optimizer`: `SKILL.md as trainable parameters`, a frozen executor, benchmark-defined quality, and validation-gated edits.

reference @./references/skillopt-process.md

## Contract

The optimizer is allowed to improve only when:

- A benchmark defines what better means.
- Candidate edits are body-only and never mutate frontmatter.
- Acceptance uses median-of-3 scoring with epsilon=0.05 by default.
- Bootstrap benchmarks with `BOOTSTRAP_PENDING_REVIEW` are reviewed and strengthened before use.
- Bundled or shared skills default to `proposed.md`; direct mutation requires explicit user approval and an independent held-out set.
- Version artifacts preserve `best.md`, `versions/`, `history.json`, and `rejected.json` semantics.

## Workflow

1. Locate the target skill under `.codex/skills/<name>/SKILL.md`.
2. If no benchmark exists, create `.codex/skills/<name>/skillopt-benchmark.jsonl` from the skill and append `# BOOTSTRAP_PENDING_REVIEW`.
3. Review and strengthen generated judges before deleting the sentinel.
4. Run preflight: clean target file unless overridden, benchmark parses, `D_sel >= 5`, cost/runtime budget acknowledged, and no duplicate active run.
5. Score the baseline on the selection set.
6. For each iteration, run candidate rollouts, split failures and successes, reflect on both, rank and clip edits by the learning-rate budget, and apply only body-safe edits.
7. Run the validation gate: median-of-3 per selected task, mean per-task medians, accept only when candidate score is greater than best score plus epsilon=0.05.
8. If accepted, write history-intent-first artifacts. If mutation is not allowed, write `proposed.md` or `skillopt/best.md` for review.
9. Run the held-out gate before mutating shared skills.
10. Finish with final test-set scoring and a run receipt.

## Local Runner

Use `.codex/skills/skill-optimizer/scripts/skillopt_runner.py` for the
Codex-native deterministic runner:

```bash
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-from-skill
# Review and strengthen skillopt-benchmark.jsonl, then delete # BOOTSTRAP_PENDING_REVIEW.
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --dry-run
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --candidate candidate.md --proxy-from-skill-text
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --candidate candidate.md --rollouts rollouts.json --baseline-score 0.72
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --live --max-llm-calls 80
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --live --provider codex --max-llm-calls 80
# Optional held-out safety gate:
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --candidate candidate.md --rollouts rollouts.json --baseline-score 0.72 --held-out held-out.jsonl --held-out-rollouts held-out-rollouts.json
python3 .codex/skills/skill-optimizer/scripts/skillopt_runner.py my-skill --bootstrap-reviewed --split 1:1:1 --live --held-out held-out.jsonl --mutate
```

The local runner does not hide live LLM execution inside a deterministic script.
It supports two deterministic evidence modes:

- `--proxy-from-skill-text` scores rule judges against baseline and candidate
  skill text. This is benchmark-based proxy evidence, not live task execution.
- `--rollouts` accepts externally generated median-of-3 rollout evidence plus
  an explicit `--baseline-score`.

It also supports `--live`, which calls the Gemini API directly by default using
`GEMINI_API_KEY`. Default live models are `gemini-2.5-flash` for target/judge
rollout evaluation and `gemini-3.5-flash` for optimizer edit synthesis. Pass
`--provider codex` to use `codex exec` with Codex defaults. Codex rollout calls
are allowed at least 10 minutes each. The live path executes benchmark tasks with the
target model, asks the optimizer model for body-only edits, and validates the
candidate with median-of-3 rule or LLM judge scoring. It records a live lock,
checkpoint, trace, receipt, rejected edit buffer, LLM call count, and Codex JSON
event-derived tool call records when the CLI provides them.

For smoke tests, using the same model for target and optimizer is acceptable.
For real optimization, prefer the target model that represents normal skill use
and a stronger optimizer model such as `gemini-3.5-flash`; the optimizer is doing
meta-level edit synthesis from rollout failures and benefits from extra
reasoning strength.

All modes apply body-only and validation gates, then write `proposed.md`,
`skillopt/best.md`, `skillopt/versions/`, `history.json`, `rejected.json`, trace
artifacts, and live receipts when applicable. Direct `--mutate` requires an
independent disjoint held-out gate; the live path runs that gate itself when
`--held-out` is supplied.

No repo-level live smoke script is bundled. When live API auth is available,
run the `--live` command directly with explicit `--provider`, model flags,
`GEMINI_API_KEY`, or the `SKILLOPT_*` environment variables. Live evidence is
intentionally separate from the secret-free baseline `scripts/verify`.

## Output Format

Report:

- Outcome: `accepted`, `no_improvement`, `aborted`, or `errored`.
- Baseline score, best selection score, final test score, and held-out result when present.
- Files written: `proposed.md`, `skillopt/best.md`, version snapshots, history, rejected buffer.
- Verification commands and any missing live evidence.

## Anti-Patterns

- Optimizing without a benchmark.
- Bypassing the validation gate because a candidate "looks better".
- Editing frontmatter, routing metadata, or trigger descriptions during optimization.
- Trusting bootstrap judges without human strengthening.
- Accepting a candidate that improves proxy checks while regressing held-out workflows.
