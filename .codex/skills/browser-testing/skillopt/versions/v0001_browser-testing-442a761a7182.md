---
name: browser-testing
description: Verify web features in a real browser after implementation, gather browser evidence for read-only verifier flows, and safely coordinate local dev servers and Playwright when browser behavior matters.
---

# Browser Testing

Use this skill when a task needs real browser evidence: post-implementation
verification, read-only verifier runs, smoke testing a local web app, debugging a
rendered flow, or deciding whether permanent Playwright coverage is needed.

Do not use this as a substitute for `design-review`, `ux-review`,
`visual-qa-hardening`, `browse`, or `benchmark` when the user explicitly asks
for those higher-level reviews. This skill can provide the browser evidence
they depend on.

## Contract

A browser-testing run is complete only when:

- The active product contract is identified before opening the browser. Prefer
  task-provided requirements, accepted plans, specs, contracts, README commands,
  or existing Playwright config in that order.
- The server is started through a non-blocking project-native mechanism. If this
  repo shape exposes `main/scripts/start_dev_env.sh`, use the helper scripts in
  `.codex/skills/browser-testing/scripts/`; otherwise use the app's documented
  dev server or Playwright `webServer` configuration.
- Browser actions are based on observed page state, not guessed selectors. Use
  accessibility snapshots, role/name locators, visible text, screenshots, or DOM
  inspection before interacting.
- Evidence matches the requested boundary: screenshots and a concise report for
  read-only verification; committed Playwright tests only when the contract asks
  for durable regression coverage.
- UI-bearing post-implementation requirements route to `visual-qa-hardening`
  after same-run browser screenshots exist and before `implementation-brake`
  when visual readiness is the gate.
- Cleanup happens before handoff unless an active dev server is intentionally
  left running for the user and clearly reported.

## Routing Decisions

- Use `browser-testing` as the primary skill for browser smoke checks,
  post-implementation browser verification, verifier evidence collection,
  dev-server readiness, selector strategy, and Playwright regression execution.
- Use `design-review` as primary when the user asks for a visual design audit,
  design polish, or design-system consistency review. `browser-testing` may
  still gather screenshots or page state for that review.
- Use `visual-qa-hardening` as primary when a UI-bearing requirement is already
  implemented, browser screenshot verification exists or must be gathered, and
  the next decision is visual readiness before `implementation-brake`.
  `browser-testing` supplies same-run desktop, mobile, stress-state, flow, and
  screenshot evidence; `visual-qa-hardening` owns the visual verdict.
- Use `ux-review` as primary when the question is task success, first value,
  recovery, trust, or user outcome quality rather than basic browser execution.
- Use `benchmark` as primary for Web Vitals, Lighthouse-style performance,
  load-time, or bundle-size regression analysis.

## Workflow

1. Identify the contract and mode.
   - Implementation mode may edit tests or product code only within the active
     task contract.
   - Verifier mode is read-only for product and test code. Leave artifacts the
     next phase can consume.
   - If a project has `DESIGN.md` and the check is visual or UI-bearing, read it
     before judging layout or polish.
   - If the accepted contract is a UI-bearing post-implementation visual gate,
     gather browser evidence here and hand the final visual verdict to
     `visual-qa-hardening`.
2. Prepare the environment.
   - Inspect the project's dev-server and E2E commands before starting anything.
   - Prefer Playwright's configured `webServer` when running Playwright tests.
   - For this worktree layout, run:
     ```bash
     ./.codex/skills/browser-testing/scripts/start_env.sh
     ./.codex/skills/browser-testing/scripts/check_logs.sh http://localhost:3000
     ```
   - If readiness fails, inspect the log printed by `check_logs.sh` or
     `main/dev_env.log` before retrying. Keep long-running commands in a
     background session or repo wrapper so the agent remains usable.
3. Choose the browser path.
   - Use browser-control tools for exploratory verification, screenshots,
     state inspection, and read-only evidence. If browser tools are not already
     exposed, discover the available browser or Chrome tool first.
   - Use Playwright for durable regression coverage, CI-facing E2E tests, or
     flows that must be replayed deterministically.
   - Use both when a flow needs quick manual evidence and then permanent
     coverage.
4. Exercise the user flow.
   - Start from a clean, stated URL and viewport.
   - Wait for the page or network condition the app actually depends on.
   - Inspect the current accessibility tree, DOM, or screenshot before acting.
   - Interact through role/name locators, labels, stable test ids, or observed
     element handles. Avoid brittle coordinate-only interaction unless the UI is
     canvas-based or no semantic target exists.
   - Verify loading, success, failure, empty, and permission states when the
     contract covers them.
5. Record evidence.
   - For verifier or scheduler flows, write:
     - `contexts/browser-testing/<run-name>-<YYYYMMDD>/report.md`
     - `contexts/browser-testing/<run-name>-<YYYYMMDD>/baseline.json`
     - `contexts/browser-testing/<run-name>-<YYYYMMDD>/screenshots/`
   - If the run maps to one active spec package, also write
     `specs/<feature>/qa_verdict.md` with `pass`, `fail`, or `blocked`, tested
     flows, top findings, coverage gaps, and the canonical artifact directory.
   - If the run spans unrelated features, keep the canonical output under
     `contexts/browser-testing/...` and skip the spec-local verdict.
6. Clean up.
   - Stop helper-managed environments with:
     ```bash
     ./.codex/skills/browser-testing/scripts/stop_env.sh
     ```
   - Report any server intentionally left running, including its URL and why it
     remains useful.

## Output Format

In the final response or verifier report, include:

- `mode`: implementation, verifier, exploratory, or regression.
- `contract`: the spec, requirement, plan, README command, or test config used.
- `environment`: command or helper used to start the app, URL, browser, and
  viewport when relevant.
- `flows tested`: the concrete user paths and states exercised.
- `evidence`: screenshots, Playwright traces, artifact directories, or test
  commands with pass/fail outcomes.
- `verdict`: pass, fail, or blocked, with the first blocking reason or highest
  impact finding.
- `downstream gate`: `visual-qa-hardening`, `design-review`, `ux-review`,
  `benchmark`, or `not required`, with the routing reason.
- `cleanup`: stopped, left running for the user, or not started.

## Playwright Guidelines

- Add or update Playwright tests only when durable E2E coverage is part of the
  accepted contract or is the narrowest honest regression proof for the bug.
- Keep tests user-centered with `getByRole`, `getByLabel`, visible text, or
  stable app-owned test ids.
- Let Playwright own server startup when `playwright.config.*` already defines a
  `webServer`; avoid starting a second conflicting server.
- Capture traces, screenshots, or videos only when they help diagnose or prove a
  browser-observed behavior.
- Run the narrowest relevant Playwright command first, then the repo baseline
  verification required by the task.

## Anti-Patterns

- Treating unit-test success as browser verification for UI behavior.
- Guessing selectors or clicking coordinates without first inspecting rendered
  state.
- Running long-lived dev servers in the foreground so no further tool use is
  possible.
- Mutating product or test code during a read-only verifier run.
- Creating permanent E2E tests for every exploratory finding when a screenshot,
  report, or narrower deterministic test is the correct evidence.
- Leaving servers, browser contexts, or occupied ports behind without reporting
  them.
- Claiming visual, UX, performance, or accessibility approval when the task only
  gathered basic browser evidence.
- Returning the final visual readiness verdict for a UI-bearing requirement
  that should pass through `visual-qa-hardening`.
