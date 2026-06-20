# Live DX Review Sections

Use these eight passes after target discovery. Each pass must state evidence, score, and gaps. For dimensions that cannot be directly exercised, mark the method as `INFERRED` or `BLOCKED` instead of guessing.

## Pass 1: Getting Started Experience

Rate 0-10: Can the target developer go from zero to hello world in the chosen time budget?

Evaluate:

- one-command or one-click install
- complete prerequisites
- first run produces meaningful visible output
- no credit card, sales call, company email, or hidden setup before value
- copy-paste examples work as written
- authentication bootstrap is clear
- a magical moment appears early

Fix direction: write the ideal golden path with exact commands, expected output, and per-step time budget. Target three steps or fewer when possible.

## Pass 2: API/CLI/SDK Design

Rate 0-10: Is the interface guessable, consistent, and complete for the target persona?

Evaluate:

- names and command grammar are predictable
- defaults are useful and production-shaped
- simplest call is valuable, not a toy
- advanced behavior uses progressive disclosure
- output adapts to terminal vs pipe or machine-readable contexts when relevant
- retry, idempotency, rate limits, and offline behavior are clear
- developers do not need raw HTTP or private internals for common tasks

Fix direction: prefer one memorable golden command or API example, then expose power through consistent options.

## Pass 3: Error Messages And Debugging

Rate 0-10: When something fails, does the developer know what happened, why, and how to fix it?

Trace at least three realistic error paths when possible:

- missing auth or credentials
- invalid input, flags, or parameters
- missing prerequisites or unavailable service
- 404, unauthenticated, or invalid web form state

Evaluate against the formula: problem, cause, fix, docs link, and actual values that caused it.

Fix direction: move actionable information to the top, include exact next commands or edits, and expose a debug or verbose mode where useful.

## Pass 4: Documentation And Learning

Rate 0-10: Can the developer find what they need and learn by doing?

Evaluate:

- quickstart is prominent and copy-paste complete
- tutorials and references both exist
- examples show real use cases, not only hello world
- search and navigation work
- language/version switching is coherent
- docs match shipped version
- playgrounds, sandboxes, or try-it paths exist when appropriate

Fix direction: docs are product surface. A feature is not done until the learning path is done.

## Pass 5: Upgrade And Migration Path

Rate 0-10: Can developers upgrade without fear?

Evaluate:

- changelog is user-facing
- breaking changes are explicit
- deprecation warnings are actionable
- migration guides cover each breaking path
- codemods or automated migration tools exist where scale warrants them
- compatibility policy is clear

Fix direction: make upgrades boring and reversible where possible.

## Pass 6: Developer Environment And Tooling

Rate 0-10: Does this fit real developer workflows?

Evaluate:

- local setup is reproducible
- CI/non-interactive use is documented
- TypeScript or language-native types are included when relevant
- testing, mocks, fixtures, dry-run, or sample apps exist
- Mac, Linux, Windows, containers, ARM/x86, and proxy constraints are addressed when relevant
- feedback loop is fast enough for normal iteration

Fix direction: reduce wait time, surprise prerequisites, and environment-specific failure.

## Pass 7: Community And Ecosystem

Rate 0-10: Is help findable and is the ecosystem credible?

Evaluate:

- license and repo visibility
- issue templates and contributing guide
- discussion channels or support paths
- examples and integrations
- extension/plugin model if relevant
- pricing and quota transparency
- response quality on public issues when inspectable

Fix direction: developers need confidence that they will not be stranded after adoption.

## Pass 8: DX Measurement And Feedback Loops

Rate 0-10: Can the product team see and improve developer friction over time?

Evaluate:

- TTHW can be measured
- onboarding drop-offs are visible
- docs search failures or common error paths can be learned from
- bug reports and feedback channels are easy
- periodic DX audits or release checks are planned
- plan targets can boomerang into live verification

Fix direction: make developer pain observable without collecting unnecessary sensitive data.
