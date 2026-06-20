# Technical Research: PGLite Broker Guard Implementation

Created: 2026-06-21
Status: Complete
Requirement source: requirements/007-pglite-broker-guard-implementation/requirements.md

## Research Decisions

### RD-001: Treat the requirement 006 inventory as a validation contract, not a runtime dependency

- Question: Should product runtime read `pglite-access-inventory.yml` directly to decide broker/guard behavior?
- Decision: No. Runtime should use repo-native TypeScript policy/dispatch tables or helpers, while tests/validators compare those runtime policies against the requirement 006 inventory.
- Rationale: Requirement artifacts are planning/evidence sources and should not become product runtime dependencies. A code-native policy keeps product startup independent of YAML parsing and lets TypeScript enforce operation names, caller types, and typed errors. The inventory remains authoritative by validator/test parity.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Runtime reads YAML inventory | Exact artifact parity | Adds YAML/runtime coupling, deploy risk, and broadens config surface | Rejected |
  | Hand-maintained runtime policy with no validator parity | Simple runtime | Easy to drift from 468-row inventory | Rejected |
  | Runtime policy plus inventory parity tests | Stable runtime and drift detection | Requires test/helper work | Accepted |
- Risk: Parity tests must fail closed when source fingerprints, row counts, or class mappings drift.
- Evidence:
  - `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml` records 468 rows and source fingerprints.
  - `scripts/validate-pglite-access-inventory.ts` already proves source-derived inventory parity.
  - `requirements/007-pglite-broker-guard-implementation/requirements.md` AC1 requires consuming the accepted inventory without making it a runtime dependency.

### RD-002: Generalize owner IPC beyond `query`, `search`, and `think`

- Question: Is the existing operation IPC substrate sufficient for all read/mutation paths?
- Decision: Keep the local Unix-socket IPC substrate and protocol pattern, but extend its operation identity and validation beyond the current `OperationIpcOperation = 'query' | 'search' | 'think'` narrow union.
- Rationale: `startPgliteOperationIpcServer` already serializes requests through a single owner queue, records `served`, `owner_unreachable`, `broker_timeout`, `completion_unknown`, `lock_safety_blocked`, and related statuses, and is local-socket-only. The narrow enum and proxy tool list are the limiting factors for all-access behavior.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Add ad hoc special cases for `list_pages` only | Fast for observed bug | Repeats prior under-scoping and violates 468-row contract | Rejected |
  | Replace IPC with a new broker | Clean-slate design | Higher risk; could introduce network/security changes | Rejected |
  | Generalize existing IPC operation identity and policy | Reuses tested local queue and statuses | Requires careful type/policy changes | Accepted |
- Risk: Expanding operation names without a policy gate could accidentally expose local-only operations remotely; policy validation must precede dispatch.
- Evidence:
  - `src/core/pglite-operation-ipc.ts` defines `VALID_OPERATIONS` as `query`, `search`, `think` and serializes queued requests.
  - `src/cli.ts` defines `BROKERED_OPERATIONS` as the same narrow set.
  - `src/mcp/server.ts` proxy mode builds tool definitions only for `query`, `search`, `think`.

### RD-003: Use live-lock preflight before any PGLite direct open

- Question: Where should raw lock/connect timeout prevention happen?
- Decision: Every PGLite-touching entry path that can run while a local owner is live must check `classifyPgliteLock` before creating/connecting a second PGLite engine. Healthy live locks route/guard; corrupt or unknown locks fail fast; dead/stale locks may recover into existing direct-open behavior.
- Rationale: Raw timeouts happen after a second process attempts direct PGLite access. Existing `maybeRunBrokeredOperation` and `maybeDeferPgliteMaintenanceCommand` prove the safer pattern: inspect lock state first and avoid direct open when the lock is live, corrupt, or unknown.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Catch `PGLiteEngine.connect` lock errors globally | Minimal changes | Still attempts direct open and may preserve raw timeout surface | Rejected |
  | Preflight only CLI top-level commands | Covers many paths | Misses MCP and nested command-module direct opens | Rejected |
  | Central preflight helper used by CLI/MCP/command open sites | Consistent behavior before direct open | Requires broader integration | Accepted |
- Risk: Preflight must not steal/delete live locks and must preserve no-owner/dead-lock recovery behavior.
- Evidence:
  - `src/core/pglite-lock.ts` exposes `classifyPgliteLock` without acquiring, waiting, stealing, or cleaning.
  - `src/cli.ts` uses `classifyPgliteLock` in brokered operation and maintenance deferral paths.
  - `test/cli-pglite-operation-broker.test.ts` asserts corrupt lock fails fast and dead/stale lock recovers to direct-open behavior.

### RD-004: Dispatch operation rows through existing `dispatchToolCall` / operation handlers with caller context preserved

- Question: How should `gbrain call` and MCP operation rows execute through the owner without duplicating handlers?
- Decision: Owner-side dispatch should continue to use `dispatchToolCall` / `dispatchBrokeredOperation` style execution so existing param validation, `OperationContext.remote`, source resolution, auth scopes, localOnly checks, and operation errors are preserved.
- Rationale: `dispatchToolCall` is the shared MCP operation boundary; `runCall` already delegates to `handleToolCall` with local CLI `remote=false`; `dispatchBrokeredOperation` already wraps CLI and stdio MCP contexts for the owner. Extending this path avoids handler duplication and preserves established trust-boundary semantics.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Directly call engine methods per operation | Fine-grained control | Duplicates validation/auth/source logic | Rejected |
  | Forward raw SQL or engine method names | Flexible | Violates security/product boundary | Rejected |
  | Extend dispatchToolCall-based owner dispatch | Reuses existing contracts | Needs richer caller/policy metadata | Accepted |
- Risk: CLI command-module paths that are not `operations.ts` operations still need command-specific adapters or typed guards.
- Evidence:
  - `src/mcp/dispatch.ts` centralizes param validation, `OperationContext`, `OperationError` formatting, and MCP result shape.
  - `src/commands/call.ts` uses `handleToolCall(engine, tool, params, { sourceId })`.
  - `src/mcp/pglite-operation-dispatch.ts` already dispatches brokered CLI and stdio MCP requests through operation handlers.

### RD-005: Serialized mutation must be owner-owned, not retry-based

- Question: How should `serialized_owner_mutation` rows avoid concurrent direct-open failures?
- Decision: Mutations accepted as `serialized_owner_mutation` should execute inside the owner process through the same owner queue/dispatch boundary, not by waiting/retrying in the second process for the PGLite lock.
- Rationale: PGLite is single-writer/single-connection in this setup. The owner process already holds the connection and queue. Retrying from another process still competes with the owner lock and can produce raw timeout or unknown completion. Owner-owned serialization gives one execution locus and clearer completion semantics.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Second process waits for PGLite lock | Simple mental model | Can hang, timeout, or race with owner; violates live-owner product boundary | Rejected |
  | Guard all mutations while owner is live | Safer than direct open | Downgrades `serialized_owner_mutation` rows without approval | Rejected |
  | Owner queue executes allowed mutations | Matches accepted class and single-owner invariant | Requires policy and tests | Accepted |
- Risk: Long-running mutations can block interactive reads unless priority/class and timeout behavior remain explicit.
- Evidence:
  - `startPgliteOperationIpcServer` already queues requests with priority and class.
  - Requirement 007 AC3 forbids silently downgrading `serialized_owner_mutation` rows to guard-only behavior.
  - Requirement 006 inventory class count includes 236 `serialized_owner_mutation` rows.

### RD-006: Typed guards should reuse and extend existing broker error vocabulary

- Question: What error strategy should typed guard fail-fast paths use?
- Decision: Reuse existing product-boundary statuses where they already fit (`owner_unreachable`, `broker_timeout`, `completion_unknown`, `lock_safety_blocked`, `maintenance_deferred`, `owner_starting`) and add only narrowly named statuses for newly guarded classes when technical design proves a gap.
- Rationale: Existing tests already assert these statuses and exit-code behavior. Reusing them reduces compatibility churn and keeps operators on a familiar recovery path. New statuses should be typed and bounded, never raw PGLite messages.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | One generic `pglite_busy` error | Simple | Loses recovery signal and completion semantics | Rejected |
  | Many row-specific errors | Precise | Too much public surface drift | Rejected |
  | Reuse vocabulary, add only gaps | Compatible and actionable | Requires design discipline | Accepted |
- Risk: Error shape must stay parseable across CLI, stdio MCP, and HTTP MCP.
- Evidence:
  - `src/cli.ts` maps broker failures through `emitBrokerFailure` and sets timeout/unknown exit code 124.
  - `test/cli-pglite-operation-broker.test.ts` asserts `owner_unreachable`, `completion_unknown`, `owner_starting`, `maintenance_deferred`, and `lock_safety_blocked`.
  - Requirement 007 AC4 and AC7 require stable typed errors with exit-code/error-shape evidence.

### RD-007: Remote trust boundaries must be enforced before and inside owner dispatch

- Question: Does forwarding a remote MCP request to the owner risk bypassing `OperationContext.remote` or localOnly checks?
- Decision: Policy checks must happen before forwarding when possible and again owner-side through `dispatchToolCall` with `remote=true`, auth scopes, source scopes, and localOnly semantics preserved.
- Rationale: The second process and owner process are separate trust boundaries. Pre-forward filtering avoids unnecessary owner traffic and reduces attack surface, while owner-side `remote=true` is the fail-closed semantic authority if a caller bypasses the proxy or if policy metadata drifts.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Trust the proxy only | Faster | Owner-side bypass risk if proxy drifts | Rejected |
  | Trust owner dispatch only | Single authority | Unknown tools/localOnly may be forwarded unnecessarily | Rejected |
  | Enforce at both boundaries | Defense in depth | Some duplicated policy metadata | Accepted |
- Risk: Policy duplication must be covered by tests so proxy and owner do not drift.
- Evidence:
  - `OperationContext.remote` documentation says security-sensitive operations tighten confinement when remote=true.
  - `dispatchToolCall` builds context with `remote` and auth/source options.
  - `file_upload` is `localOnly` and validates upload path differently for remote versus local callers.

### RD-008: Requirement 007 evidence should be class-complete; requirement 008 should be all-row repeated matrix

- Question: How much verification belongs to implementation slice 007 versus final verification slice 008?
- Decision: Requirement 007 must prove implementation coverage across all behavior classes and critical trust/owner-state variants with targeted tests and manifest parity. Requirement 008 remains the full N=3 repeated named command matrix proof for all in-scope paths.
- Rationale: This preserves the sequence split: implementation first, exhaustive verification next. It also prevents 007 from claiming all-row matrix completion from representative tests.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Full all-row matrix in 007 | Strong proof | Collapses 007 and 008; slows implementation feedback | Rejected |
  | Only unit tests in 007 | Fast | Too weak for runtime concurrency behavior | Rejected |
  | Class-complete targeted evidence in 007, full matrix in 008 | Balanced sequence fidelity | Requires precise closeout language | Accepted |
- Risk: Closeout must not overclaim; coverage ledger closure should distinguish targeted implementation proof from final matrix proof.
- Evidence:
  - Sequence item 3 reserves requirement 008 for the named command matrix with zero raw lock/connect timeout.
  - Requirement 007 AC9 and AC10 explicitly preserve that boundary.
  - Requirement 006 gauntlet provides the raw-timeout classifier and manifest validation foundation.

## Requirement Impact

- None.

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |
| Exact runtime policy table/module name | non_blocking | Research chooses code-native policy plus inventory parity; technical-design should place it in a cohesive module. | technical-design |
| Exact typed error code additions | non_blocking | Existing vocabulary covers many states; technical-design should name any required new statuses after mapping row classes. | technical-design |
| Exact representative row set for requirement 007 tests | non_blocking | Requirement 007 needs class-complete targeted evidence, while requirement 008 owns final all-row matrix. Plan-eng-review should lock the representative set. | technical-design / plan-eng-review |
| Whether command-module-only paths become operation adapters or guard-only command wrappers | non_blocking | Requirement preserves class behavior; technical-design must choose the lowest-risk integration per command family. | technical-design |

## Gate Self-Review

- All technical unknowns from the requirement were addressed or classified.
- Every decision has rationale and alternatives.
- Requirement Impact is absent.
- Every unresolved item is classified as non_blocking with a downstream owner.
- Evidence paths/sources are recorded in evidence.md.
