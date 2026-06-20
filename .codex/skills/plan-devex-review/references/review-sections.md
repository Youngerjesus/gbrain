# Plan DX Review Sections

Run all eight passes after Step 0 investigation. If a pass has no findings, say so and explain why. The plan file is not proof by itself; every pass must connect to the target persona, TTHW target, journey trace, or competitor benchmark.

## Pass 1: Getting Started Experience

Rate 0-10: Can the developer go from zero to hello world within the target tier?

Evidence to recall:

- persona tolerance from Step 0A
- empathy narrative pain from Step 0B
- competitor target from Step 0C
- magical moment vehicle from Step 0D
- Install and Hello World friction from Step 0F

Evaluate:

- install path count and prerequisites
- first run output
- sandbox or try-before-install path
- free tier or no-account path
- copy-paste completeness
- auth/credential bootstrap
- TTHW estimate

Plan obligation for 10/10: exact golden path, expected output, time budget per step, and the first magical moment.

## Pass 2: API/CLI/SDK Design

Rate 0-10: Does the interface match the target developer's mental model?

Evaluate:

- naming and command grammar
- defaults and progressive disclosure
- consistency across surfaces
- completion of common workflows
- discoverability from help text or examples
- reliability semantics: retries, idempotency, rate limits, offline behavior
- persona fit

Plan obligation for 10/10: one simple example that is production-shaped, plus a clear path to advanced use without changing concepts.

## Pass 3: Error Messages And Debugging

Rate 0-10: Does the plan specify what developers see when things fail?

Trace at least three planned or likely error paths:

- missing credentials or permissions
- invalid input or bad command flags
- missing prerequisites
- network/API/service failure
- version mismatch or migration failure

Evaluate whether each error includes:

- what happened
- why it happened
- how to fix it
- actual value or location involved
- docs link or next command

Plan obligation for 10/10: explicit error UX examples and a debug/verbose path when helpful.

## Pass 4: Documentation And Learning

Rate 0-10: Does the plan teach by doing and make help findable?

Evaluate:

- quickstart placement and completeness
- tutorials vs reference coverage
- examples with real context
- versioned docs
- language/framework variants
- search and navigation expectations
- playground or sample app path

Plan obligation for 10/10: docs ship with the feature and include runnable examples for the persona's main use case.

## Pass 5: Upgrade And Migration Path

Rate 0-10: Can existing developers adopt or upgrade without fear?

Evaluate:

- backwards compatibility
- migration guide
- deprecation warnings
- changelog expectations
- codemods or automation where warranted
- versioning policy
- rollback or coexistence path

Plan obligation for 10/10: every breaking or behavior-changing path has a migration story and verification.

## Pass 6: Developer Environment And Tooling

Rate 0-10: Does the plan fit real development workflows?

Evaluate:

- local setup reproducibility
- CI/non-interactive mode
- language types and editor support
- fixtures, mocks, dry-run, or test helpers
- platform compatibility
- feedback loop speed
- observability for local debugging

Plan obligation for 10/10: the persona can evaluate, integrate, test, and automate the tool without hidden environment knowledge.

## Pass 7: Community And Ecosystem

Rate 0-10: Does the plan make adoption feel credible beyond the first demo?

Evaluate:

- open-source or license clarity
- support and community paths
- issue templates and contribution flow
- examples and integrations
- extension model if relevant
- pricing, quota, or operational transparency

Plan obligation for 10/10: a developer can understand where to get help, how the ecosystem grows, and what adoption costs.

## Pass 8: DX Measurement And Feedback Loops

Rate 0-10: Can the team tell whether DX improved after shipping?

Evaluate:

- TTHW measurement plan
- onboarding drop-off signals
- docs search or feedback signals
- common error telemetry or logs without sensitive data
- release DX checklist
- live `devex-review` boomerang target

Plan obligation for 10/10: measurable DX acceptance criteria and a post-ship audit path.

## Conditional Checklist: Codex Skill Or Agent Tool

Use this checklist when reviewing Codex skills, MCP servers, agent workflows, prompt contracts, or AI developer tools. This is not a ninth scored pass unless the product is primarily an agent tool.

Check:

- trigger conditions are narrow and non-overlapping
- required references are one hop from `SKILL.md`
- host-specific preambles and telemetry are absent
- interactive decisions work through normal chat and do not require unavailable tools
- state storage is repo-local or explicitly justified
- failure recovery and verification are explicit
- prompt/schema/parser/validator contracts stay synchronized
- live or deterministic smoke evidence is named for AI boundary changes

If any item affects implementation readiness, convert it into a task.
