---
name: skillify
description: Turn a raw repeatable capability into a proper Codex skill with a clear trigger, lean instructions, deterministic helpers where useful, verification coverage, and lifecycle evidence.
---

# Skillify

Use this skill when the user asks to "skillify" a feature, make a workflow proper, add tests/evals for a skill, or decide whether a repeated behavior should become a Codex skill.

This is the Codex port of gbrain's meta skill. It keeps the original lifecycle idea while replacing gbrain resolver, Bun, and cross-modal commands with repo-native Codex files and `scripts/verify`.

## Contract

A capability is properly skilled when:

- It is reusable and has a realistic user trigger.
- `.codex/skills/<name>/SKILL.md` defines the contract, workflow, output format, and anti-patterns.
- Deterministic behavior lives in scripts or tests instead of vague instructions.
- Quality checks exist for the behavior that can regress.
- The skill is reachable in the current Codex environment and does not overlap an existing skill.

## Workflow

1. Decide whether this should be a skill. Require reuse, a clear trigger, and enough process or logic to justify a durable package.
2. Audit the current artifact: skill doc, helper scripts, references, tests, and verification commands.
3. Create or update `SKILL.md` with Codex-native frontmatter and one-hop references.
4. Add scripts, templates, or assets only when they make the skill more reliable than prose.
5. Run a quality pass before tests lock behavior in. Use deterministic checks where possible; use LLM review only with an explicit rubric and evidence refs.
6. Add focused tests or verification scripts for the skill's durable contract.
7. Run targeted verification, then `scripts/verify`.
8. Report remaining gaps as known gaps, not as successful skillification.

## Output Format

Produce a short lifecycle report with:

- Skill path.
- Capability decision: `skill`, `extend_existing`, or `not_a_skill`.
- Files created or changed.
- Verification commands and outcomes.
- Known gaps or waived checks.

## Anti-Patterns

- Skillifying a one-time note, prompt, or tiny helper.
- Writing tests that only assert wording instead of behavior.
- Importing host-specific command names, paths, or private conventions.
- Adding broad always-on routing language that overlaps existing skills.
- Claiming the skill is proper when verification is missing or stale.
