---
name: promptfoo-eval
description: Design and run promptfoo evals for prompt changes. Use when modifying prompts, prompt templates, system or agent instructions, LLM judge prompts, or promptfoo configs; when feedback needs eval coverage; when comparing baseline versus candidate prompt behavior; or when verification must use deterministic assertions, rubric-first LLM judges, result artifacts, and evidence reporting.
---

# Promptfoo Eval

Use this skill to verify prompt changes with promptfoo evidence instead of subjective output inspection. Treat prompt edits as a small TDD loop: define the intended behavior delta, create or update eval coverage, run baseline when practical, edit the prompt, run candidate evals, then report targeted behavior separately from regressions.

## Workflow

1. Identify the prompt under change, the requested feedback, the expected behavior delta, and the risk level.
2. Inspect the project before adding anything: package scripts, existing `promptfooconfig.*`, prompt files, tests, assertion files, result directories, and project conventions.
3. Complete the portability discovery matrix and choose one execution mode before creating files or running commands.
4. Decide whether existing eval coverage catches the requested feedback. If not, add or propose promptfoo tests before claiming verification.
5. Choose assertions by failure mode:
   - deterministic assertions for exact format, required or forbidden text, JSON/schema validity, numeric checks, and other mechanically checkable output.
   - LLM judge assertions for qualitative judgment, tone, reasoning quality, refusal behavior, policy interpretation, instruction following, or usefulness.
   - both when the prompt change has objective and qualitative requirements.
6. For qualitative judge checks, write the rubric first. Include pass criteria, fail criteria, and negative examples or failure modes. Do not treat vague expectations as strong judge evidence.
7. Run a baseline eval before editing when practical. If the prompt was already changed or no prior result exists, candidate-only evaluation is allowed only when reported as weaker evidence.
8. Run the candidate eval with the same config, provider, vars, filters, and assertions unless the change explicitly requires different coverage.
9. Compare targeted feedback cases separately from regression cases. Overall pass rate is never enough by itself.
10. Report commands, configs, prompt paths, result artifacts, provider, targeted result, regression result, evidence strength, and blockers.

## Portability Discovery Matrix

Before running promptfoo in any project, inspect and record:

- Existing config: `promptfooconfig.*`, `promptfoo.yaml`, `promptfoo.yml`, `promptfoo.json`, or project-specific eval folders.
- Package manager and scripts: `package.json`, lockfiles, `npm`, `pnpm`, `yarn`, `bun`, Makefile, task runners, CI eval commands.
- Runtime support: Node and npm availability, writable runtime directory, shell environment, and whether `npx` is acceptable.
- Provider availability: existing provider config, API keys, local provider, `echo`, `exec`, or no usable provider.
- Prompt surface: exact prompt, template, system instruction, agent instruction, judge prompt, or config under change.
- Baseline availability: unchanged prior prompt, previous result artifact, git ref, or no reproducible baseline.
- Output policy: where local runtime artifacts should live, and whether generated eval files must be ignored or committed.

Do not ask the user for facts you can inspect locally. Ask only for missing credentials, provider preference, risk tolerance, or whether a generated eval harness should be committed.

## Execution Modes

Choose one mode and state it in the report:

- **existing-config**: Use the project's existing promptfoo config and package script when it covers the feedback or can be minimally extended according to local conventions.
- **ephemeral-config**: When no suitable config exists, create a temporary harness under `.runtime/promptfoo-eval/<eval-id>/` and run it without adding permanent project files unless the user asks.
- **deterministic-only**: When no LLM provider or API key is available but mechanical checks are enough, use deterministic assertions with `echo`, `exec`, JavaScript, JSON/schema, `contains`, or `not-contains`.
- **blocked**: When promptfoo cannot run because Node/npm, package install, provider access, config validity, or write permissions are unavailable. In blocked mode, do not claim promptfoo-backed verification.

Static checks, subagent reviews, unit tests, and pytest are supplemental evidence. They must not be silently substituted for promptfoo-backed evidence after this skill has been invoked. If promptfoo cannot run, say `promptfoo execution blocked` and explain why.

## Running Promptfoo

Prefer project-local commands when they exist, for example `npm run eval`, `pnpm promptfoo eval`, `yarn promptfoo eval`, `bunx promptfoo eval`, or a repo script documented near the config.

Use the bundled wrapper only when a project has no better local convention:

```bash
~/.codex/skills/promptfoo-eval/scripts/run_promptfoo_eval.sh promptfooconfig.yaml .runtime/promptfoo candidate --filter-metadata suite=targeted
```

The wrapper delegates to `npx promptfoo@latest eval`, writes timestamped JSON and HTML artifacts in a unique run directory, passes through extra promptfoo flags, forces `--no-share` for local-only fallback runs, and preserves promptfoo's exit status. It is not a custom eval engine. Use direct project commands instead when a project intentionally wants sharing or cloud-specific behavior.

When `npx` cache corruption or concurrent install errors occur, retry once with an eval-local cache, for example:

```bash
NPM_CONFIG_CACHE=.runtime/npm-cache ~/.codex/skills/promptfoo-eval/scripts/run_promptfoo_eval.sh <config> .runtime/promptfoo <label>
```

Treat failed promptfoo runs as evidence too: preserve their result directory and then run a corrected candidate in a new result directory. Do not overwrite failed artifacts.

## Resources

- Read `references/eval-design.md` when creating or changing promptfoo coverage.
- Read `references/judge-rubrics.md` before using LLM judge assertions.
- Read `references/portability.md` when a project has no promptfoo setup or you are unsure which mode applies.
- Read `references/provider-strategy.md` before choosing between `echo`, `exec`, or a real LLM provider.
- Read `references/result-artifact-contract.md` before reporting or committing eval evidence.
- Copy from `assets/templates/` only when a project lacks its own promptfoo setup or reporting format.
- Use `scripts/scaffold_ephemeral_eval.sh` to create a portable `.runtime/promptfoo-eval/<eval-id>/` harness when no project-local convention exists.

## Evidence Rules

Final responses after using this skill must state:

- prompt or instruction files evaluated
- execution mode
- promptfoo config and command used
- result artifact path
- whether evidence is baseline-versus-candidate or candidate-only
- targeted feedback pass/fail result
- regression pass/fail result
- any flaky, skipped, blocked, or provider-dependent checks
- whether supplemental static/subagent/test evidence was used and why it is not a replacement for promptfoo evidence

If promptfoo cannot run because dependencies, API keys, provider access, network, or config are missing, do not claim behavioral verification. Report the blocker and any partial static checks separately.
