---
name: browser-testing
description: Guidelines and helper tools for Full-Stack End-to-End (E2E) testing and browser verification. Use this skill to verify features in a real browser environment after development, or to gather read-only browser evidence during verification. Includes tools to safely manage the dev server in the background.
---

# Browser Testing & Visual QA Workflow

This skill provides the methodology and embedded tools for testing completed features (Frontend + Backend) in a real browser. You are an autonomous worker agent; you must establish the context by reading the feature specifications, and strictly follow the execution constraints defined in the contract.

When this skill is used from `impl_verify` or another verifier-driven phase, treat it as a read-only browser evidence workflow. In that mode you must not modify product code or test code, and you must leave behind verifier-consumable artifacts.

## Core Principles

1. **Context & Contract Driven**:
   - ALWAYS read the relevant `specs/.../spec.md` to understand the feature's core "Happy Path" and the user persona you are testing for.
   - ALWAYS read the relevant `specs/.../contracts.md`. If the contract asks for visual verification, use MCP tools. If it mandates regression scripts, write Playwright code.
2. **The Browser is the Source of Truth**: Unit tests are not enough. If it doesn't render correctly or the user flow breaks in a real browser, the feature is broken.
3. **Safe Environment Management**: Treat `main/scripts/run_dev_env.sh` as the long-running environment orchestrator. Do not run it directly in the foreground during browser-testing flows because it blocks further tool use. Start the environment via the provided background wrappers in `.codex/skills/browser-testing/scripts/` and inspect logs before attempting any direct diagnostics.
4. **Verification Mode Matters**: In implementation phases you may create or update Playwright assets if the contract explicitly requires it. In verifier phases you are evidence-only and must not mutate product or test code.

## Step 1: Start the Environment

This skill provides helper scripts in the `.codex/skills/browser-testing/scripts/` directory to manage `main/scripts/run_dev_env.sh` safely.

1. **Start the server**: Run the start script. It launches `run_dev_env.sh` in the background, writes logs to `dev_env.log`, and stores the PID for cleanup.
   ```bash
   ./.codex/skills/browser-testing/scripts/start_env.sh
   ```
2. **Wait for readiness**: Use the readiness checker to poll the frontend until it responds.
   ```bash
   ./.codex/skills/browser-testing/scripts/check_logs.sh http://localhost:3000
   ```
3. **Diagnose startup failures safely**: If readiness times out, inspect `main/dev_env.log` first. Do not retry by running `main/scripts/run_dev_env.sh` directly in the foreground. If direct execution is absolutely required for diagnosis, run it in a separate PTY or other non-blocking session so the main testing flow remains usable.

## Step 2: Choose the Testing Approach

Based on the `contracts.md` requirements and the context from `spec.md`, use one or a combination of the following approaches:

### Approach A: Autonomous Agent Testing (Chrome DevTools MCP)
**When to use:** For visual QA, exploratory testing, rapid verification, or as a precursor to writing automated scripts.
**How:**
- Use your built-in MCP tools (e.g., `mcp_chrome-devtools_navigate_page`) to navigate to `http://localhost:3000`.
- **Apply the Reconnaissance-Then-Action Pattern**:
  1. **Wait**: Use `mcp_chrome-devtools_wait_for` to ensure the network is idle and the dynamic DOM has fully rendered.
  2. **Inspect**: Use `mcp_chrome-devtools_take_snapshot` to capture the current state of the accessibility tree and identify the exact `uid` of elements you need to interact with.
  3. **Act**: Only after identifying the target, use tools like `mcp_chrome-devtools_click` or `mcp_chrome-devtools_fill` using the discovered `uid`.
- Embody the user persona defined in `spec.md`. Follow the core scenario (Happy Path).
- Visually confirm the layout, states, and data fetching work end-to-end.
- Report the outcome in your final task summary.

### Approach B: Scripted E2E Tests (Playwright Code)
**When to use:** When the contract explicitly demands E2E test scripts for CI/CD, regression prevention, or permanent test assets.
**How:**
- Create or update `.spec.ts` files in the `tests/e2e/` (or equivalent) directory.
- *Note on Server Management*: If the project's Playwright config (`playwright.config.ts`) uses a `webServer` block to automatically start its own server, ensure it doesn't conflict with Step 1 (e.g., use a different port, or skip Step 1 if Playwright handles it entirely).
- Use semantic locators (`getByRole`, `getByLabel`).
- Ensure the tests interact with the actual running full-stack environment.
- Run the tests to verify they pass:
  ```bash
  npx playwright test
  ```

## Step 3: Cleanup

ALWAYS clean up the environment when testing is complete so you do not leave zombie processes or blocked ports.

```bash
./.codex/skills/browser-testing/scripts/stop_env.sh
```

## Evidence Contract

When browser verification is part of a scheduler or verifier flow, write these outputs inside the repository:

- `contexts/browser-testing/<run-name>-<YYYYMMDD>/report.md`
- `contexts/browser-testing/<run-name>-<YYYYMMDD>/baseline.json`
- `contexts/browser-testing/<run-name>-<YYYYMMDD>/screenshots/`
- `specs/<feature>/qa_verdict.md` when the run maps cleanly to one active spec package

`qa_verdict.md` must contain:

- `pass`, `fail`, or `blocked`
- tested flows
- top findings
- coverage gaps
- the canonical artifact directory

If the run is broad or spans multiple unrelated specs, keep the canonical output under `contexts/browser-testing/...` and skip the spec-local verdict.

---
**Remember**: Understand the *Why* through `spec.md`, follow the *Rules* of `contracts.md`, and use the provided *Tools* to execute safely.
