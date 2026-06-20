---
name: skill-review
description: Review Codex skills for routing, workflow quality, question gates, safety, validation, portability, and agent/user experience; produce a findings-first scorecard without modifying the skill.
---

# Skill Review

Use this skill when the user asks to review, audit, check, score, or ship-gate a
Codex skill such as `.codex/skills/<name>/SKILL.md`, a skill reference file, a
skill template, or a skill ported from another host. This is the Codex-native
version of the gstack meta-review process: decide whether future agents will
invoke the skill at the right time, follow it correctly, recover from failure,
and produce trustworthy output.

HARD GATE: this skill is report-only. Do not edit skill files. If you find fixes,
describe exact changes and file locations, but leave implementation to a separate
turn or skill.

## Contract

A review is complete only when it:

- Resolves the target skill and names the reviewed source of truth.
- Reads the skill union: `SKILL.md` plus directly referenced one-hop files,
  templates, scripts, or fixtures that materially affect the workflow.
- Runs the cheapest relevant static validation or records why each check was not
  run.
- Scores every rubric dimension from 0-10 with evidence.
- Leads with findings before summary praise.
- Distinguishes observed evidence from inference.
- Produces a verdict, scorecard, recommended fix order, and residual risk.

## When To Invoke

Use for:

- Reviewing a new or changed Codex skill before it is shared.
- Checking whether a skill is ready to ship.
- Auditing trigger quality, tool expectations, safety gates, and test coverage.
- Comparing generated or templated skill output against the editable source.
- Reviewing a host-portable skill copied from gstack, Claude, OpenClaw, or a
  browser/domain skill bundle.

If the user asks to create or update a skill, use `skill-creator` or `skillify`
first. Use `skill-review` after the skill exists.

## Workflow

1. Resolve The Target

   If the user provided a path or skill name, resolve it. Common forms include
   `skill-review plan-eng-review`, `.codex/skills/plan-eng-review/SKILL.md`, or a
   path to a skill directory. If no target was provided, inspect the current diff
   for changed `SKILL.md`, reference, template, script, or fixture files. If
   exactly one skill directory appears, review that skill. If several appear, ask
   the user which one to review. If none appear, ask for a path or skill name.

   Print:

   ```text
   Reviewing: <skill name>
   Source of truth: <path>
   Generated output: <path or none>
   References/scripts/fixtures: <count>
   Mode: <codex-skill | hosted-port | browser/domain-skill | external-skill>
   ```

2. Read The Skill Union

   Read `SKILL.md` and every directly referenced one-hop file that changes how
   the skill runs. Include scripts, templates, fixtures, and reference files when
   they define validation, output shape, parsing, or safety behavior. Do not read
   huge fixtures unless parser behavior or evidence fidelity is under review.

   For templated skills, identify the editable source and generated output. In
   Codex skillpacks, `SKILL.md` is normally the source of truth unless a repo-local
   contract explicitly says otherwise.

3. Static Validation

   Run the cheapest validation first and capture the result. Do not fix failures.
   Prefer these checks when available:

   ```bash
   python3 .codex/skills/skillpack-check/scripts/skillpack_check.py --root <repo>
   python3 tests/verify_skill_lifecycle_pack.py
   rg -n "<skill-name>|SKILL.md" tests .codex/skills 2>/dev/null
   scripts/verify
   ```

   If the skill has targeted tests, run those before the full baseline. If a
   command is unavailable, too broad, or already known to fail for unrelated
   reasons, mark it as `NOT RUN` or `FAIL (pre-existing)` with the reason.

4. Review Rubric

   Score every dimension 0-10 using file and command evidence:

   - Routing and discoverability: name, description, trigger language, aliases,
     and "when to invoke" text match realistic user requests without
     over-triggering.
   - Scope and non-goals: the skill says what it does, what it refuses to do, and
     when another skill is more appropriate.
   - Executable workflow: steps are ordered, concrete, and possible for an agent
     to follow without guessing.
   - Question gates: user questions appear only where judgment matters; options
     are complete; destructive, expensive, or one-way actions have clear gates.
   - Tool expectations and safety: required tools are sufficient but not
     excessive; writes, network, auth, destructive commands, and generated
     artifacts have explicit safety rules.
   - Validation and testability: deterministic checks, fixtures, dry-runs, or
     narrow smoke tests match the skill's risk.
   - Template and generation hygiene: generated files are fresh, editable sources
     are named, placeholders are valid, and catalog/docs entries are aligned.
   - Failure recovery and idempotency: failures stop at the right place, retries
     are bounded, and re-runs do not duplicate work or corrupt state.
   - Host and model portability: host-specific assumptions are isolated or
     removed; Codex tool names and fallback behavior are clear.
   - Agent/user experience: outputs are crisp, evidence-rich, and understandable
     without drowning the user.

   Calibration:

   - 9-10: Ready to ship. Clear, safe, tested, and easy to invoke.
   - 7-8: Usable with minor gaps.
   - 5-6: Works but likely causes confusion or maintenance drag.
   - 3-4: Risky. Agents will skip steps, over-ask, or misuse tools.
   - 0-2: Broken or unsafe.

5. Required Checks

   Explicitly check:

   - Frontmatter includes `name` and a routing-useful `description`.
   - Tool references match the workflow and Codex host. Flag unused powerful tools,
     broad shell mutation, or web access when not justified.
   - If a template or generator exists, contributors are told which file to edit
     and how to verify generated output freshness.
   - References are one hop from `SKILL.md` unless the skill explains the deeper
     boundary.
   - Any stop point includes the next action.
   - Any write, commit, push, delete, deploy, credential, or external-service path
     has a gate or deterministic safety rule.
   - Report claims are backed by commands, file refs, screenshots, fixtures, logs,
     or clearly labeled inference.
   - Parser, browser, or domain skills have fixture replay or assertions stronger
     than "does not throw".
   - Long-running or costly optional checks are opt-in or clearly scoped.
   - The skill has a completion shape: report, artifact, log entry, PR, or
     explicit "nothing to do" outcome.

6. Optional Cross-Model Smoke

   If the skill is high-risk, foundational, or prompts model-specific behavior,
   recommend a separate benchmark or prompt-eval pass after the static report. Do
   not block the report on optional benchmarking unless the user asked for it.

## Output Format

Lead with findings like a code review. Use file and line references wherever
possible.

```text
## Skill Review Report: <skill>

Verdict: <READY | READY WITH NITS | NEEDS WORK | BLOCKED>
Overall: <N>/10
Validation: skillpack-check <PASS/FAIL/NOT RUN>, lifecycle tests <PASS/FAIL/NOT RUN>, targeted tests <PASS/FAIL/NOT RUN>, scripts/verify <PASS/FAIL/NOT RUN>

### Findings
1. [P1] <title> -- <file:line>
   Why it matters:
   Evidence:
   Fix:

### Scorecard
| Dimension | Score | Evidence |
|-----------|-------|----------|
| Routing and discoverability | N/10 | ... |

### What Works
- <strong parts worth preserving>

### Recommended Fix Order
1. <highest leverage fix>
2. <next fix>

### Residual Risk
<what remains uncertain because tests/tools were unavailable>
```

Severity:

- P0: Unsafe or unusable; blocks shipping.
- P1: Likely to cause wrong behavior, data loss, bad routing, or broken execution.
- P2: Quality gap that will confuse agents/users or make maintenance harder.
- P3: Polish, clarity, or nice-to-have.

## Anti-Patterns

- Editing the reviewed skill during a review-only run.
- Treating this as a generic code review instead of an agent-workflow release
  review.
- Giving a score without concrete file or command evidence.
- Letting a full baseline failure hide targeted review findings.
- Using string search as proof of semantic correctness; use it only for discovery
  unless a deterministic validator or fixture backs the claim.
- Ignoring host portability when a skill was copied from another agent runtime.
- Praising the skill before listing blocking or high-priority findings.
