---
name: plan-devex-review
description: Review developer-facing implementation plans before coding by interrogating personas, onboarding, API/CLI/docs ergonomics, error quality, upgrade paths, and measurable time to hello world.
---

# Plan Devex Review

Use this skill when the user asks for a developer experience review, DX plan review, API design review, onboarding review, or "will developers like this?" review for a plan involving APIs, CLIs, SDKs, libraries, platforms, docs, Codex skills, MCP servers, or other agent tools.

This is a planning skill. Do not implement code. Do not silently rewrite the plan unless the user explicitly asks for document edits. Your job is to surface DX gaps, force the few decisions that matter, and leave an implementation-ready DX checklist.

## Contract

A complete review provides:

- product type and applicability decision
- target developer persona
- first-person empathy narrative
- competitive benchmark or current best available reference benchmark
- selected TTHW target tier
- magical moment specification
- journey map with friction decisions
- eight-pass DX scorecard using [review-sections.md](./references/review-sections.md)
- implementation checklist and action tasks derived from findings
- unresolved decisions, if any

If the plan has no developer-facing surface, exit gracefully and recommend a more relevant skill such as `plan-eng-review` or `plan-design-review`.

## Core Posture

- The output is a better plan, not a pretty scorecard.
- Scores are calibration; decisions and implementation obligations matter more.
- Ground every finding in a persona, file, plan line, docs path, competitor benchmark, or TTHW trace.
- Use current web research for competitor onboarding, pricing, docs, and public TTHW claims when they influence the recommendation. Cite sources.
- Ask the user only for genuine trade-offs. For obvious fixes, recommend directly.
- One issue equals one decision. Do not batch multiple developer pains into one question.

## Workflow

### 1. Pre-Review System Audit

Read the direct plan or requirement source first. Then inspect only the context needed to understand developer-facing surfaces:

- `AGENTS.md` and relevant project rules
- selected `plan.md`, `secondary_plan.md`, `spec.md`, `contracts.md`, or requirement docs
- `README.md`, docs, examples, package manifests, CLI entrypoints, and public API definitions
- changelog, migration docs, contributing docs, issue templates, and sample apps when relevant

Map:

- product type: API/service, CLI, SDK/library, platform, documentation, Codex skill, MCP server, or agent tool
- developer-facing surfaces changed by the plan
- existing docs, examples, error handling, and DX patterns the plan should reuse
- current install and hello-world path

### 2. Applicability Gate

Infer product type from the plan:

- endpoints, REST, GraphQL, gRPC, webhooks: API/service
- commands, flags, terminal, config files: CLI
- package install, imports, language bindings: SDK/library
- deploy, hosting, provisioning, infrastructure: platform
- guides, tutorials, references, examples: documentation
- `SKILL.md`, MCP, agent workflows, prompt contracts: Codex skill or agent tool

If no developer-facing surface exists, stop with a short explanation. If a surface exists, state the classification and proceed.

### 3. Step 0 Investigation

Do this before scoring.

#### 0A. Developer Persona

Infer the likely target developer from the plan and docs. Offer 2-3 concrete persona options only when the answer changes the review.

Example archetypes:

- YC founder building an MVP
- platform engineer evaluating for a company
- frontend developer adding a feature
- backend developer integrating an API
- open-source contributor
- student or first-time learner
- DevOps engineer automating infrastructure

Produce a persona card:

```text
TARGET DEVELOPER PERSONA
Who:
Context:
Tolerance:
Expects:
```

#### 0B. Empathy Narrative

Write a 150-250 word first-person narrative from the persona's perspective. Trace the actual getting-started path from available docs and the plan. Include where they feel confident, confused, or likely to abandon.

If the narrative depends on an uncertain assumption, ask the user to correct it before using it as evidence.

#### 0C. Competitive Benchmark

Compare against current public examples when the choice affects scope or target tier. Search the web if needed, and cite sources. If live search is unavailable, use the reference benchmarks in [dx-hall-of-fame.md](./references/dx-hall-of-fame.md) and mark them as reference, not current market proof.

Produce:

```text
COMPETITIVE DX BENCHMARK
Tool              TTHW       Notable DX Choice       Source
...
This plan         <estimate> <current path>           <plan/docs>
```

Ask or recommend the target tier:

- Champion: under 2 minutes
- Competitive: 2-5 minutes
- Needs Work: 5-10 minutes
- Red Flag: over 10 minutes

#### 0D. Magical Moment

Identify the moment where the developer first feels "this works and is worth it."

Choose or ask between:

- interactive playground or sandbox
- copy-paste demo command
- short video/GIF walkthrough
- guided tutorial with the developer's own data
- sample app or template repo

Record the selected delivery vehicle and implementation requirements.

#### 0E. Review Mode

Pick one mode explicitly:

- `DX EXPANSION`: new or strategically important developer product; propose ambitious opt-in improvements.
- `DX POLISH`: scope is right; make each touchpoint clear and adoption-safe. Default for most reviews.
- `DX TRIAGE`: urgent or narrow work; flag only adoption blockers and ship-critical gaps.

Do not drift modes mid-review without saying why.

#### 0F. Developer Journey Trace

Trace the actual or planned journey:

1. Discover
2. Install
3. Hello World
4. Real Usage
5. Debug
6. Upgrade

For each stage, identify concrete friction and resolve it as fixed, deferred, accepted, or blocked.

In `DX TRIAGE`, trace Install and Hello World first and continue only if critical risk remains. In `DX POLISH` and `DX EXPANSION`, trace all stages.

#### 0G. First-Time Developer Roleplay

Produce a timestamped confusion report:

```text
FIRST-TIME DEVELOPER REPORT
Persona:
Attempting:

T+0:00
T+0:30
T+1:00
T+2:00
T+3:00
Final state:
```

Ground this in actual plan/docs evidence. Do not invent a fictional onboarding path when files contradict it.

### 4. Run The Eight DX Passes

Read [review-sections.md](./references/review-sections.md) before running the passes. Use [dx-hall-of-fame.md](./references/dx-hall-of-fame.md) pass-by-pass for calibration. Do not load unrelated references.

Every pass follows this pattern:

1. recall relevant Step 0 evidence
2. score 0-10
3. explain what a 10 looks like for this product and persona
4. identify the gap
5. recommend a plan change or ask one trade-off question
6. re-rate the plan assuming accepted fixes

Mode behavior:

- `DX EXPANSION`: after reaching a solid baseline, propose opt-in best-in-class moves.
- `DX POLISH`: close every material gap and tie each to a plan obligation.
- `DX TRIAGE`: only block on gaps below 5/10 or TTHW above 10 minutes.

### 5. Synthesize Tasks

Convert accepted findings into flat implementation tasks. Each task must derive from a specific finding.

Use:

```markdown
## Implementation Tasks

- [ ] **T1 (P1)** - <component> - <imperative title>
  - Surfaced by: <pass or Step 0 finding>
  - Files: <likely files or docs>
  - Verify: <test, browser check, CLI smoke, or manual audit>
```

Priorities:

- `P1`: blocks developer adoption or ship-readiness
- `P2`: should land in the same branch
- `P3`: useful follow-up DX debt

### 6. Close The Review

Return:

1. **Plan Under Review**
2. **Persona And TTHW Target**
3. **Top DX Findings**
4. **DX Scorecard**
5. **Magical Moment**
6. **Implementation Checklist**
7. **Implementation Tasks**
8. **Unresolved Decisions**
9. **Recommended Next Step**

If the plan is ready, say `GO`. If changes are needed but bounded, say `GO WITH CHANGES`. If adoption-critical decisions or plan gaps remain, say `STOP`.

## Output Format

Scorecard template:

```text
DX PLAN REVIEW - SCORECARD
Dimension              Score   Prior/Target   Trend/Gap
Getting Started        __/10   <target>       <gap>
API/CLI/SDK            __/10   <target>       <gap>
Error Messages         __/10   <target>       <gap>
Documentation          __/10   <target>       <gap>
Upgrade Path           __/10   <target>       <gap>
Dev Environment        __/10   <target>       <gap>
Community              __/10   <target>       <gap>
DX Measurement         __/10   <target>       <gap>
TTHW                   __ min  <tier>         <gap>
Competitive Rank       <Champion|Competitive|Needs Work|Red Flag>
Magical Moment         <designed|missing> via <vehicle>
Product Type           <type>
Mode                   <DX EXPANSION|DX POLISH|DX TRIAGE>
Overall DX             __/10
```

Implementation checklist:

```text
DX IMPLEMENTATION CHECKLIST
[ ] TTHW is under <target>
[ ] installation path is explicit
[ ] first run produces meaningful output
[ ] magical moment is delivered via <vehicle>
[ ] every major error has problem, cause, fix, and docs link
[ ] API/CLI naming is guessable
[ ] defaults are production-shaped
[ ] docs examples are copy-paste complete
[ ] upgrade path is documented
[ ] CI/non-interactive path is covered when relevant
[ ] feedback and measurement loop exists
```

## Anti-Patterns

- Implementing code during the plan review.
- Treating "developers" as one persona.
- Scoring before persona, benchmark, and journey evidence.
- Asking vague preference questions instead of specific trade-off questions.
- Importing gstack telemetry, home-directory artifacts, Claude-specific preambles, or routing behavior.
- Treating current-market competitor claims as stable without web verification.
- Letting a low score stand without saying what would make it a 10 for this product.
