---
name: devex-review
description: Run a live developer experience audit for APIs, CLIs, SDKs, libraries, platforms, docs, or agent tools by dogfooding onboarding, measuring time to hello world, and producing evidence-backed DX findings.
---

# Devex Review

Use this skill when the user asks to test developer experience, run a DX audit, dogfood onboarding, measure time to hello world, inspect CLI/API/docs ergonomics, or compare shipped developer-facing behavior against an earlier plan.

This is a live audit skill. It is not a plan review. Read about the experience only when a surface cannot be executed or rendered; otherwise, try it like a first-time developer.

## Contract

A complete review provides:

- the developer-facing surface under test and target persona assumptions
- measured or explicitly inferred time to hello world (TTHW)
- evidence for every score: browser screenshots, terminal output, file references, or a clearly marked unavailable check
- scores for the eight DX dimensions in [review-sections.md](./references/review-sections.md)
- a boomerang comparison against any available `plan-devex-review` expectations
- prioritized fixes tied to concrete developer pain, not generic polish

Do not make product code changes unless the user explicitly asks you to fix the findings after the audit.

## Core Posture

- Measure, do not guess.
- Screenshots and terminal output beat prose.
- The first five minutes matter most.
- Every error should tell a developer what happened, why, how to fix it, and where to learn more.
- Mark the evidence method for each dimension: `TESTED`, `PARTIAL`, `INFERRED`, or `BLOCKED`.
- Use current web research when competitor claims, docs URLs, pricing, or public onboarding behavior may have changed; cite sources in the final audit.

## Workflow

### 1. Discover The Target

Read the direct task context first, then inspect:

- `AGENTS.md` and relevant project instructions
- `README.md`, docs, examples, and package manifests
- CLI entrypoints or help text if a CLI exists
- changelog, migration docs, contributing docs, and issue templates when present
- any plan or requirement artifact the user points to

Identify:

- product type: API/service, CLI, SDK/library, platform, documentation, Codex skill, MCP server, or other agent tool
- primary developer persona, inferred from docs or user context
- canonical getting-started path
- available local commands and web URLs

If no URL or runnable entrypoint can be discovered, ask the user for the missing target before continuing.

### 2. Establish Evidence Paths

Use the strongest available evidence:

- Browser evidence for docs, dashboards, playgrounds, forms, 404 pages, and web onboarding.
- Terminal evidence for CLI install, `--help`, first run, invalid args, and local setup.
- File evidence for migration policy, examples, types, CI support, feedback loops, and community docs.

If the audit needs browser automation, use the repo's browser-testing or browse workflow. If the page requires secrets, paid accounts, private auth, email verification, or an unavailable external service, mark that slice `BLOCKED` or `INFERRED` and say exactly why.

### 3. Measure Getting Started

Act as a new developer following the documented golden path.

Record:

```text
GETTING STARTED AUDIT
Step 1: <developer action>    Time: <estimate/measure>    Friction: <low|med|high>    Evidence: <screenshot/command/file>
Step 2: ...
TOTAL: <steps>, <minutes>, <final state>
```

Rate against the TTHW benchmark in [dx-hall-of-fame.md](./references/dx-hall-of-fame.md).

### 4. Run The Eight DX Passes

Read and apply [review-sections.md](./references/review-sections.md). For each pass, load only the matching pass from [dx-hall-of-fame.md](./references/dx-hall-of-fame.md) when calibration would help.

The eight passes are:

1. Getting Started Experience
2. API/CLI/SDK Design
3. Error Messages And Debugging
4. Documentation And Learning
5. Upgrade And Migration Path
6. Developer Environment And Tooling
7. Community And Ecosystem
8. DX Measurement And Feedback Loops

Every pass must produce a score or an explicit `BLOCKED` reason. Do not skip a pass because the plan or product seems "not about docs" or "only a CLI"; adoption breaks at the gaps between surfaces.

### 5. Boomerang Against Plan Expectations

If the user provides a prior `plan-devex-review` report, requirement evidence, plan scorecard, or acceptance target, compare planned vs. live reality.

Flag:

- live score more than 2 points below plan score
- measured TTHW slower than the target tier
- magical moment missing from the shipped path
- inferred dimensions that were promised as testable

If no prior plan evidence exists, state `No boomerang baseline found`.

### 6. Produce The Audit

Lead with findings, then scorecard.

Use this structure:

1. **Target And Persona**
2. **Top Findings**
3. **TTHW Trace**
4. **DX Scorecard**
5. **Boomerang Comparison**
6. **Evidence Inventory**
7. **Recommended Fixes**
8. **Verification Gaps**

## Output Format

Scorecard template:

```text
DX LIVE AUDIT - SCORECARD
Dimension              Score   Evidence                 Method
Getting Started        __/10   <screenshots/output>      TESTED
API/CLI/SDK            __/10   <screenshots/output>      PARTIAL
Error Messages         __/10   <screenshots/output>      PARTIAL
Documentation          __/10   <screenshots/files>       TESTED
Upgrade Path           __/10   <files>                   INFERRED
Dev Environment        __/10   <files/output>            INFERRED
Community              __/10   <screenshots/files>       PARTIAL
DX Measurement         __/10   <files/pages>             INFERRED
TTHW measured          __ min  <step count>              TESTED
Overall DX             __/10
```

For each issue, include:

- severity: `P1 adoption blocker`, `P2 meaningful friction`, or `P3 polish`
- evidence
- developer impact
- recommended fix
- verification method after the fix

## Anti-Patterns

- Auditing from docs alone when the product can be tried.
- Treating string searches as authoritative proof of semantic behavior.
- Scoring without evidence.
- Hiding untested dimensions inside an overall score.
- Importing gstack telemetry, home-directory review logs, Claude-specific preambles, or routing behavior.
- Requiring secrets or paid external services for baseline completion.
