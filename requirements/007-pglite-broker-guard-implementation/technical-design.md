# Technical Design: PGLite Broker Guard Implementation

Created: 2026-06-21
Status: Complete
Requirement source: requirements/007-pglite-broker-guard-implementation/requirements.md
Research source: requirements/007-pglite-broker-guard-implementation/research.md
Architecture artifact: requirements/007-pglite-broker-guard-implementation/architecture.md

## Requirement Coverage

| Requirement / Acceptance Criterion | Design mapping |
| --- | --- |
| AC1. Consume accepted requirement 006 inventory | Add a code-native PGLite owner policy module plus test/validator parity against `pglite-access-inventory.yml`. Runtime does not read YAML; tests fail on row/class/source drift. |
| AC2. Broker `broker_success_read` rows | Generalize local owner IPC target identity from `query/search/think` to operation and command targets. Use owner-side `dispatchToolCall` for operation rows and command adapters for CLI command rows. |
| AC3. Serialize `serialized_owner_mutation` rows | Route allowed mutation rows to owner-owned queue execution. Disallow second-process lock waiting/retry as a live-owner strategy. Command adapters return captured stdout/stderr/exit verdict to the caller process. |
| AC4. Typed guard fail-fast rows | Add a pre-connect owner-state/policy guard that emits stable typed statuses before any direct PGLite open. Reuse existing statuses first and add new statuses only through typed union/tests. |
| AC5. Preserve trust boundaries | Enforce remote/local policy before forwarding and again owner-side via `dispatchToolCall(remote=true)` or command-adapter restrictions. Local-only/file-sensitive rows are rejected for remote MCP. |
| AC6. Owner-state variants | Centralize owner-state classification around `classifyPgliteLock`, operation startup election, socket probing, IPC timeout, and corrupt/unknown lock handling. |
| AC7. Preserve public command syntax | Second-process CLI keeps parsing existing argv. Live-owner forwarding writes the owner response stdout/stderr back to the same streams and sets the same exit verdict contract. |
| AC8. Replace expected-red rows | Update the requirement 006 gauntlet or add a requirement 007 successor gauntlet so `call:list_pages` and other expected-red representatives no longer emit raw PGLite lock/connect timeout. |
| AC9. Class-complete regression coverage | Add unit tests for policy parity, IPC validation, result/output capture, and typed guards; integration tests for read, mutation, remote rejection, owner-state, and no-owner baseline. |
| AC10. Handoff to requirement 008 | Evidence records implemented class coverage, residual verification-only risks, updated gauntlet paths, and exact commands to run for final repeated matrix. |

## Module Design

- Module boundaries:
  - `src/core/pglite-owner-policy.ts`
    - Owns the code-native policy projection of the requirement 006 behavior classes.
    - Exports typed behavior classes, caller kinds, target kinds, side-effect categories, and `resolvePgliteOwnerPolicy(input)`.
    - Does not import requirement YAML.
  - `src/core/pglite-owner-routing.ts`
    - Owns live-owner preflight decisions around `classifyPgliteLock`, startup election, socket availability, no-owner direct-open, and fail-fast statuses.
    - Exports `decidePgliteOwnerRoute(config, policy, ownerStateOpts)`.
  - `src/core/pglite-operation-ipc.ts`
    - Keeps local Unix-socket transport, queueing, timeouts, startup lock, and request validation.
    - Extends request target from the current narrow `operation: 'query' | 'search' | 'think'` to a typed target:
      - `{ kind: 'operation'; name: string }`
      - `{ kind: 'cli_command'; command: string; args: string[]; profile?: string }`
    - Uses an additive v1-compatible extension by default: legacy `operation: query|search|think` requests remain valid, and generalized requests add a typed `target` shape. Protocol v2 is allowed only if additive compatibility is proven impossible and recorded before implementation continues.
  - `src/mcp/pglite-operation-dispatch.ts`
    - Renamed or expanded to owner dispatch for both operation targets and CLI command targets.
    - Operation target dispatches through existing `dispatchToolCall` / `buildOperationContext` path.
    - CLI command target dispatches through a curated surface-id keyed command adapter registry. Operation-backed rows must not use command adapters.
  - `src/cli.ts`
    - Replaces `BROKERED_OPERATIONS` / `PGLITE_MAINTENANCE_COMMANDS` special-case sets with policy-backed preflight for every PGLite-touching CLI entry that reaches engine creation.
    - Keeps current argument parsing and output formatting where command code already owns it.
  - `src/mcp/server.ts`
    - Expands second-serve proxy tool list from `query/search/think` to remote-allowed operation rows from policy.
    - Keeps normal owner serve behavior as the owner-side execution authority.
  - Test helpers:
    - Extract or reuse temp-home, live-lock, IPC server, CLI runner, and raw-timeout classifier helpers from existing PGLite broker and requirement 006 tests.

- Public interfaces:
  - `PgliteOwnerBehaviorClass = 'broker_success_read' | 'serialized_owner_mutation' | 'typed_guard_fail_fast'`.
  - `PgliteOwnerTarget = { kind: 'operation'; name: string } | { kind: 'cli_command'; surfaceId: string; command: string; args: string[]; profile?: string }`.
  - `PgliteOwnerPolicy` includes:
    - `surfaceId`
    - `target`
    - `behaviorClass`
    - `allowedCallers`
    - `remoteAllowed`
    - `localOnly`
    - `filesystemSensitive`
    - `requiresOwnerSerialization`
    - `guardStatusWhenLiveOwner`
    - `noOwnerMode`
  - `PgliteOwnerRouteDecision` includes:
    - `kind: 'direct_open_allowed' | 'forward_to_owner' | 'typed_guard'`
    - `status`
    - `message`
    - `exitCode`
    - `socketPath?`
    - `target?`
  - IPC response for CLI command targets includes:
    - `stdout`
    - `stderr`
    - `exitCode`
    - `result?`
    - `typedError?`

- Dependency direction:
  - Product runtime modules may import `pglite-owner-policy`, `pglite-owner-routing`, `pglite-operation-ipc`, and owner dispatch.
  - Product runtime must not import `requirements/**`, coverage ledgers, or test validators.
  - Tests/scripts may import both runtime policy and requirement 006 inventory to assert parity.
  - Lower-level lock/IPC modules must not import CLI command modules directly; command adapter registration lives above IPC.

- Data flow:
  - CLI/MCP entry parses command/tool request as it does today.
  - Before engine creation in a second process, routing code resolves policy and owner state.
  - `direct_open_allowed`: existing no-owner/dead-lock path continues.
  - `forward_to_owner`: caller sends typed IPC request to owner socket.
  - Owner validates target, policy, caller, remote context, and params, then executes operation/command through owner-owned engine.
  - Owner returns result or captured command output; caller writes stdout/stderr and sets exit code.
  - `typed_guard`: caller returns stable error without opening PGLite.
  - HTTP MCP live-owner path follows the same policy/routing/owner dispatch contract as stdio, while preserving OAuth auth, source scope, request logging, JSON envelopes, and `remote=true`.

## Interactions

- Main flow:
  - Validate inventory parity in tests.
  - Add/extend owner policy for all accepted rows.
  - Generalize IPC request validation and proxy tool listing.
  - Add owner dispatch for operation targets first because it reuses `dispatchToolCall`.
  - Add CLI command adapters only for true command-module/open-site rows that requirement 006 classified as brokerable or serialized, keyed by inventory surface id.
  - Add typed guards for rows classified `typed_guard_fail_fast`, corrupt/unknown locks, owner-starting, missing/stale socket, and remote local-only attempts.
  - Update gauntlet expected outcomes and class-complete tests.
- Alternate flows:
  - No owner or dead/stale recoverable lock: existing direct-open path remains valid.
  - Live owner without socket: return `owner_unreachable` or a more specific typed status before direct open.
  - Corrupt or unknown lock: return `lock_safety_blocked` before direct open.
  - Owner accepts but times out: return `completion_unknown` and exit 124 for CLI.
  - Remote MCP local-only operation: reject before forwarding and owner-side with JSON error envelope, including bypass-style owner dispatch tests.
  - Duplicate owner startup: a second `gbrain serve` under a live owner returns typed already-running/startup behavior without direct PGLite open or lock deletion.
  - Wrong owner identity: stale socket/lock state for another `GBRAIN_HOME`, profile, brain, or source cannot receive forwarded requests.
  - IPC version skew: generalized target callers talking to a legacy v1 owner receive typed unsupported/owner error rather than raw timeout, direct-open fallback, or authority expansion.
  - Command adapter unavailable for a row classified serialized/read: this is a blocker unless inventory impact is recorded and approved.
- Handoffs:
  - Requirement 008 consumes updated tests/manifest/evidence and runs the full repeated named matrix.
  - `implementation-brake` consumes the policy parity evidence and verifies no representative-only overclaim.

## State And Invariants

- States:
  - `policy_resolved`: entry path maps to exactly one owner behavior class.
  - `owner_absent`: no live PGLite lock; direct-open baseline may continue.
  - `owner_live_broker_ready`: live lock and reachable owner socket; forward allowed targets.
  - `owner_live_broker_missing`: live lock but socket absent/unreachable; typed failure.
  - `owner_starting`: startup election held; typed failure or retry loop according to class.
  - `lock_safety_blocked`: corrupt or unknown lock; no direct open.
  - `owner_dispatched`: owner accepted request; completion semantics belong to IPC response.
  - `completion_unknown`: owner accepted but caller timed out before completion.
  - `wrong_owner_identity`: lock/socket identity does not match the active home/profile/brain/source.
  - `unsupported_owner_protocol`: owner cannot accept the generalized target shape.
- Invariants:
  - No live-owner second process opens PGLite directly for an in-scope row.
  - Every policy row maps to one accepted behavior class and one inventory row or approved successor-manifest row.
  - Remote `localOnly` and filesystem-sensitive operations remain fail-closed.
  - Owner-side dispatch revalidates params and remote context even if the proxy already checked.
  - CLI command adapters must not call `process.exit`; they return exit verdict/output to the caller.
  - Raw PGLite lock/connect timeout text is never the asserted product-boundary result.
  - No runtime import from requirement YAML.
- Consistency rules:
  - Runtime policy parity tests compare against the 468-row requirement 006 inventory or a recorded approved update. If implementation edits fingerprinted source files, tests must refresh inventory fingerprints without class/row drift or create a requirement 007 successor manifest with recorded requirement impact.
  - New typed statuses must be included in tests for CLI stderr, exit code, and MCP JSON envelope.
  - Command adapters must preserve existing command syntax and output shape.
  - Safe non-execution from requirement 006 is not evidence of implementation; requirement 007 must replace expected-red behavior or record approved impact.

## Error Handling And Edge Cases

- Errors:
  - `owner_unreachable`: live owner lock requires owner routing but socket is not reachable.
  - `broker_timeout`: broker did not accept before deadline.
  - `completion_unknown`: owner accepted but caller timed out before response.
  - `lock_safety_blocked`: corrupt/unknown lock inspection refuses direct open.
  - `owner_starting`: startup election is held and direct open is unsafe.
  - `maintenance_deferred`: allowed only for rows still classified `typed_guard_fail_fast`; not a substitute for serialized mutation rows.
  - `wrong_owner_identity`: active caller context does not match the discovered owner lock/socket identity.
  - `unsupported_owner_protocol`: the owner is reachable but cannot accept the requested generalized target.
  - New statuses, if any, must be added to IPC status union, CLI rendering, MCP envelope tests, and evidence.
- Edge cases:
  - `gbrain call list_pages {}` under live owner, with assertions that owner IPC received the typed target and no second-process direct open occurred.
  - `gbrain call put_page ...` or another mutation under live owner.
  - Remote stdio/HTTP MCP attempts `file_upload`, including owner-side bypass rejection.
  - Local filesystem-sensitive owner dispatch receives relative path, symlink/out-of-scope path, and deleted-before-dispatch file payloads; owner-side canonicalization/confinement produces stable typed outcomes.
  - `doctor --fast`, `doctor --locks`, `doctor --remediation-plan`, and `doctor --remediate`.
  - `sync`, `embed`, `extract`, `apply-migrations`, and `upgrade`.
  - Live lock with missing socket, corrupt lock file, dead process lock, stale heartbeat, and startup lock.
  - Duplicate `gbrain serve` while another owner holds the lock.
  - Owner crash or restart after accepting a request, especially for serialized mutations.
  - Owner command adapter writes both stdout and stderr and returns exitCode without `process.exit`.
  - Owner command adapter wants to set nonzero exit.
  - Owner command adapter emits success-like stdout before nonzero exit, typed failure, stall, or disconnect.
- Recovery:
  - Caller never deletes live locks.
  - Dead/stale recoverable lock behavior stays with existing lock reaper path.
  - Completion-unknown tells the operator completion is unknown rather than retrying automatically; a later manual retry is a new serialized request and not a hidden resume.
  - Tests isolate with temporary `GBRAIN_HOME`, PGLite data dirs, and no inherited `DATABASE_URL`.
- Observability:
  - IPC responses include status, requestId, target or surface id, ownerPid, queuedMs, servedMs, and accepted/queued/served timing when applicable for operator-actionable outcomes.
  - CLI command target responses include stdout/stderr/exitCode.
  - Tests capture raw stdout/stderr and structured MCP content.
  - Evidence records raw-timeout classifier result for expected-red replacement.

## Testability

- Unit:
  - Policy resolver maps representative inventory rows to correct behavior class/caller constraints.
  - Inventory parity test rejects missing runtime policy rows, class drift, and remote/localOnly drift.
  - IPC validation accepts v1 `query/search/think` compatibility and new target shape; rejects unknown target kinds.
  - Routing helper maps owner states to direct/forward/typed-guard decisions.
  - Command output capture returns stdout/stderr/exitCode without calling `process.exit`.
  - Typed error renderer produces CLI and MCP-compatible envelopes.
- Integration:
  - Live-owner `gbrain call list_pages {}` forwards to owner, owner receives the row-id/surface-id target, and caller exits without raw timeout.
  - Live-owner representative read operation from stdio MCP and HTTP MCP forwards through owner.
  - Live-owner representative mutation serializes through owner and preserves local/remote policy.
  - Remote local-only/file upload operation fails closed before forwarding and in an owner-side bypass test.
  - Missing socket, unreachable socket, no lock, dead/stale recoverable lock, corrupt/unknown lock, startup election, duplicate owner startup, broker timeout, completion_unknown, owner crash/restart-after-accept, wrong-owner identity, and unsupported owner protocol states produce stable typed outcomes or safe direct-open only where eligible.
  - Filesystem-sensitive local owner dispatch proves owner-side canonicalization/confinement across path and queue-delay drift.
  - Partial command/IPC response proves exit/status/typed failure wins over captured stdout.
  - No-owner direct-open behavior for representative commands remains green.
  - Existing `test/cli-pglite-operation-broker.test.ts` remains green.
- E2E/manual if relevant:
  - Requirement 007 successor gauntlet runs in serial PGLite test tier against temp homes.
  - Requirement 008 later runs the full repeated matrix.
- Mockable boundaries:
  - `classifyPgliteLock` state can be fixture-driven through temp lock files.
  - `forwardOperationViaIpc` can be tested with a fake server.
  - Owner command adapters can be tested with fake engines and captured console streams.

## Requirement Impact

- None.

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |
| Exact command adapter list for first implementation patch | non_blocking | All rows remain in scope; adapters must now be surface-id keyed and limited to true command-module/open-site rows. Plan can order adapters by class/risk without reducing final requirement coverage. | secondary-plan / implementation |
| Exact new typed status names | non_blocking | Existing statuses should be reused first; implementation may add narrowly scoped statuses with tests. | implementation / plan-eng-review |
| HTTP MCP implementation staging | non_blocking | Requirement includes HTTP MCP in closeout scope; plan may stage tests/patches but not defer HTTP MCP past requirement 007 closeout. | secondary-plan / implementation |

## Self-Review

- Requirement coverage: All ten acceptance criteria map to modules, interfaces, interactions, and tests.
- Separation of concerns: Runtime policy is code-native; requirement YAML remains test/evidence input only.
- Testability: Unit, integration, and gauntlet layers are identified with mockable boundaries.
- Security / safety: Remote/localOnly/filesystem restrictions are enforced before forwarding and owner-side.
- Requirement integrity: No behavior class is weakened; final all-row matrix remains reserved for requirement 008.
