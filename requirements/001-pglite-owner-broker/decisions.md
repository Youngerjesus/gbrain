# Requirement Decisions

## Decisions

### 2026-06-20 13:45 KST - Scenario-brake additions are implementation-blocking guardrails

- Decision: Implementation must cover no-owner cold-start race, phase-aware ambiguous completion, mutating `think` no-auto-retry, unknown/corrupt lock fallback, partial broker response, socket permission/not-yet-bound, race-safe stale cleanup, long `think` boundedness, and second MCP proxy zero-direct-open evidence.
- Rationale: Scenario-brake found these are distinct paths rather than extra test decoration; missing them would let the implementation preserve a happy-path broker while leaving lock timeout or side-effect risks.
- Alternatives considered: Treat scenario findings as follow-up tests; rely only on live-owner five-caller proof.
- Impact: Secondary plan and implementation must preserve these scenarios as acceptance evidence for this slice.
- Source artifact: scenario-brake.md
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none before secondary-plan.

### 2026-06-20 13:25 KST - Plan-eng review tightened implementation contract

- Decision: The implementation plan must include MCP stdio proxying, a non-acquiring lock classifier, explicit CLI-only `think` pre-connect routing, caller source-resolution inputs, injected broker handler boundaries, positive broker-routing evidence, and privacy-safe diagnostic tests.
- Rationale: Plan-eng companion reviewers found that a generic CLI forwarding seam and absence-only timeout tests would under-prove the accepted requirements.
- Alternatives considered: Treat second MCP servers like CLI callers; rely on `acquireLock()` failure for live-owner detection; keep `mcp-http` in first-slice protocol; defer all AC4 priority proof.
- Impact: First slice is now narrower on HTTP and real maintenance commands, but stricter on MCP stdio, lock safety, source/trust preservation, and proof obligations.
- Source artifact: plan-eng-review.md
- Requirement Impact: none
- Blocking/non-blocking unresolved items: scenario-brake remains required before accepted secondary plan.

### 2026-06-20 13:05 KST - UX/DX status matrix and docs are in-scope

- Decision: The implementation must include a deterministic, privacy-safe broker status/error matrix and operator/developer docs or equivalent evidence in the same requirement slice.
- Rationale: Plan UX and DevEx reviews found that concurrency without lock errors is not enough; users and contributors need to distinguish queued, served, owner-unreachable, stale-socket-recovered, and lock-safety-blocked outcomes.
- Alternatives considered: Leave diagnostics as incidental stderr strings; defer all docs to production readiness.
- Impact: Draft plan now includes status-matrix, timeout, docs, and focused verification obligations before implementation.
- Source artifact: plan-ux-review.md, plan-devex-review.md, plans/001-pglite-owner-broker/plan.md
- Requirement Impact: none
- Blocking/non-blocking unresolved items: exact wording remains implementation-owned but must be tested.

### 2026-06-20 12:45 KST - Separate architecture artifact for owner/broker boundary

- Decision: Record a requirement-local `architecture.md` in addition to `technical-design.md`.
- Rationale: The requirement introduces a runtime boundary between PGLite owner, local broker clients, CLI, and MCP trust/source handoffs.
- Alternatives considered: Keep all design in `technical-design.md`; update durable architecture docs immediately.
- Impact: Implementation must preserve the dependency direction and cross-layer invariants recorded in the architecture artifact; durable docs can be synced after implementation evidence exists.
- Source artifact: technical-design.md, architecture.md
- Requirement Impact: none
- Blocking/non-blocking unresolved items: durable docs sync remains a later closeout/context-sync consideration, not a design blocker.

### 2026-06-20 12:45 KST - Pre-connect broker routing seam

- Decision: Broker-eligible CLI/MCP callers should probe/forward before `connectEngine()` rather than after a PGLite lock failure.
- Rationale: Waiting for lock failure preserves the current user-visible timeout and cannot satisfy the no-lock-timeout acceptance target.
- Alternatives considered: Post-lock-error fallback; mandatory daemon startup; direct PGLite multi-open.
- Impact: CLI command classification and MCP owner startup must be implemented before product source verification can pass.
- Source artifact: technical-design.md
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none.

### 2026-06-20 12:35 KST - Local operation IPC, not direct PGLite concurrency

- Decision: Add a sibling local-only operation broker IPC for PGLite owner forwarding instead of changing PGLite locking or widening the existing retrieval-reflex IPC.
- Rationale: The existing file lock is the safety primitive, and `resolve-ipc.ts` proves the local Unix-socket typed-request pattern without turning it into generic SQL.
- Alternatives considered: Weaken the PGLite file lock; wait for lock timeout then fallback; reuse retrieval-reflex IPC for general operations.
- Impact: Implementation must discover and forward eligible requests before `connectEngine()` on competing callers, while owner-side dispatch uses the already-open engine.
- Source artifact: research.md RD-001, RD-002
- Requirement Impact: none
- Blocking/non-blocking unresolved items: exact schema belongs to technical-design.

### 2026-06-20 12:35 KST - Preserve dispatch contracts through existing operation paths

- Decision: Owner-side broker execution should reuse `dispatchToolCall()` for MCP-shaped calls and operation handlers/CLI formatting for CLI-shaped calls, with explicit caller context in the broker request.
- Rationale: `dispatchToolCall()` already owns MCP validation, `remote=true`, takes-holder allow-list, source scope, and auth behavior. CLI callers need `remote=false` and existing output/exit behavior.
- Alternatives considered: Broker-specific SQL/search logic; treating every caller as MCP remote; separate duplicated handlers.
- Impact: Broker request schema must carry caller kind, operation name, params, source/trust fields, and output mode; tests must assert remote/source semantics survive forwarding.
- Source artifact: research.md RD-003
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none for design.

### 2026-06-20 12:11 KST - User-observable concurrency via owner broker

- Decision: The requirement targets PGLite-only gbrain behavior and defines concurrency as multiple callers being queued or served without lock errors, not simultaneous direct PGLite access from multiple processes.
- Rationale: PGLite is documented and implemented as single-process; direct multi-process access would fight the existing safety design.
- Alternatives considered: Weaken PGLite locking; require Postgres for concurrent use; require manual daemon startup.
- Impact: All later implementation must preserve single-owner PGLite safety while hiding normal-use lock failures from `query`, `search`, and `think`.
- Source artifact: requirements.md
- Requirement Impact: approved by user in current chat
- Blocking/non-blocking unresolved items: Broker architecture is blocking for technical-design, not for requirements acceptance.

### 2026-06-20 12:11 KST - Interactive priority over maintenance

- Decision: `query`, `search`, and `think` must take priority over `sync`, `embed`, and `extract` when contending for the owner.
- Rationale: The user's pain is interactive MCP/CLI use being blocked by lock contention; maintenance can queue or yield.
- Alternatives considered: FIFO across all operations; maintenance-first to maximize background throughput.
- Impact: Scheduler design must include priority or yielding behavior and prove it with tests.
- Source artifact: requirements.md
- Requirement Impact: approved by user in current chat
- Blocking/non-blocking unresolved items: Exact latency budget remains for technical-design.
