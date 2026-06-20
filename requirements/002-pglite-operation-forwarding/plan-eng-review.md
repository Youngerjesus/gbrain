# Plan Engineering Review

## Plan Under Review

- Requirement: `requirements/002-pglite-operation-forwarding/requirements.md`
- Research: `requirements/002-pglite-operation-forwarding/research.md`
- Draft plan: `plans/002-pglite-operation-forwarding/plan.md`
- Companion reviewers: scope/reuse, architecture/contract, verification/failure

## Verdict

GO WITH CHANGES

The slice can proceed, but the plan must be strengthened before implementation or evidence-only closeout. Requirement 002 must close against the exact worktree/commit that will be committed, preserve current stdio MCP source-scope/auth semantics when present, and add direct missing verification for no-owner `search`, owner-unreachable proxy behavior, and MCP proxy failure envelopes.

## Accepted Findings

### F1 - Pin the actual target worktree and commit

- Kind: implementation-readiness / evidence integrity
- Accepted from: all companion reviewers
- Required change: AC mapping and test reruns must execute against `/Users/jeongmin/Documents/garrytan-gbrain-001-pglite-owner-broker` or a newer explicit task worktree containing the broker implementation. Evidence must record the exact HEAD, command, and output.
- Rationale: base `master` has unrelated dirty MCP changes and does not contain the broker implementation.

### F2 - Add direct no-owner `search` proof

- Kind: verification gap
- Accepted from: scope/reuse and verification/failure reviewers
- Required change: add one exact PGLite no-owner `gbrain search "x"` smoke assertion to the existing broker test or equivalent. Do not rely only on `cli-search-dispatch`.
- Rationale: AC3 names `query`, `search`, and `think`; query/think direct-open coverage is exact but search coverage is indirect.

### F3 - Preserve current stdio MCP source-scope/auth parity

- Kind: contract gap
- Accepted from: architecture/contract reviewer
- Required change: If the implementation target includes the current base stdio `GBRAIN_FEDERATED_READ` / `auth.allowedSources` contract, brokered MCP requests must preserve it. Because the base worktree already has this active contract, requirement 002 should integrate or account for it before claiming AC4.
- Rationale: brokered MCP parity is not only `remote=true`; it includes source/federated-read scoping.

### F4 - Add MCP proxy failure-envelope and owner-unreachable evidence

- Kind: verification gap
- Accepted from: verification/failure reviewer
- Required change: add direct proxy-level evidence for a failure envelope, preferably invalid `search` params through the second stdio MCP proxy, and direct owner-unreachable behavior at the MCP proxy boundary.
- Rationale: existing tests prove happy-path proxy and direct dispatch helper parity, but not proxy failure shape.

### F5 - Record broker dispatch ownership boundary

- Kind: architecture clarity
- Accepted from: architecture/contract reviewer
- Required change: either move the broker dispatch adapter out of low-level `core`, or explicitly document it as a boundary adapter. The low-level IPC module must remain handler-injected and free of CLI/MCP semantics.
- Rationale: `src/core/pglite-operation-ipc.ts` has clean ownership; the dispatch adapter imports MCP dispatch and must not be mistaken for generic core.

### F6 - Narrow verification trigger wording

- Kind: scope/reuse
- Accepted from: scope/reuse reviewer
- Required change: focused verification is enough for evidence-only planning artifact edits. The broader related suite plus typecheck is mandatory when source, tests, or product docs change.
- Rationale: requirement evidence edits are inevitable and should not force the full suite by themselves.

## Rejected Or Deferred Findings

- Scenario-brake being scope waste: rejected as a skip. The sequence explicitly requires scenario-brake for this requirement; however, scenario-brake should stay narrow and focus on stale target, proxy failure, and source-scope drift.
- HTTP MCP forwarding: deferred/out of scope by requirement.
- Maintenance scheduling/yield behavior: deferred to requirement 003.

## Executable Contract Compatibility Gate

Triggered. The plan touches trust-domain boundary fields for MCP stdio forwarding.

Code-owned contract evidence:

- Direct MCP dispatch accepts `auth?: AuthInfo` in `src/mcp/dispatch.ts`.
- Operations use `ctx.auth?.allowedSources` for federated read scoping.
- Current base `src/mcp/server.ts` adds `GBRAIN_FEDERATED_READ` parsing and passes `auth.allowedSources` to direct stdio dispatch.
- Broker dispatch in requirement 001 commit `d50dc701` does not yet show `auth.allowedSources` propagation.

Implementation readiness condition: AC4 cannot close until brokered MCP dispatch preserves the active stdio source-scope/auth contract or the target worktree explicitly does not contain that contract.

## Top Missing Tests

- Direct no-owner PGLite `gbrain search "x"` smoke coverage.
- Proxy-level invalid params/error envelope through second stdio MCP server.
- Proxy-level owner-unreachable result.
- Federated stdio source-scope parity if `GBRAIN_FEDERATED_READ` is present in target.

## Failure Modes

- A later merge drops `GBRAIN_FEDERATED_READ` auth parity for brokered MCP while direct MCP keeps it.
- `gbrain search` with no owner regresses into broker-only behavior while query/think remain green.
- A second stdio MCP proxy returns generic success/error shape for owner-unreachable or invalid params.
- Evidence is rerun against base `master` without broker files or against stale `d50dc701` after new target changes.

## Scenario-Brake Routing

Used. The requirement has multiple entry paths, failure states, target drift, trust-boundary fields, and evidence reuse. Scenario-brake must run next and stay focused on those risks.

## Companion Reconciliation

- Scope/reuse reviewer: GO WITH CHANGES; accepted target pinning, no-owner search proof, and narrowed full-suite trigger.
- Architecture/contract reviewer: GO WITH CHANGES; accepted target pinning, MCP auth/source parity, and dispatch adapter boundary finding.
- Verification/failure reviewer: GO WITH CHANGES; accepted no-owner search, owner-unreachable proxy, proxy failure-envelope, and evidence pinning findings.

## Required Plan Changes Before Secondary Plan

- Make no-owner `search` direct proof mandatory.
- Require target worktree/commit pinning before any tests count.
- Require brokered MCP parity for `GBRAIN_FEDERATED_READ` / `auth.allowedSources` when present in the target.
- Require proxy failure-envelope and owner-unreachable tests.
- Document or relocate the broker dispatch adapter boundary.
- Keep full related suite mandatory only after source/test/product-doc changes, not after requirement evidence-only edits.
