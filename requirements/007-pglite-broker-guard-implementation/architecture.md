# Architecture Design: PGLite Broker Guard Implementation

Requirement source: requirements/007-pglite-broker-guard-implementation/requirements.md
Technical design source: requirements/007-pglite-broker-guard-implementation/technical-design.md

## Architecture Boundary

Requirement 007 changes the local PGLite owner boundary from a narrow interactive broker into the single product boundary for all PGLite-touching live-owner access.

The owner process remains local and single-machine. The design does not introduce a network broker, raw SQL forwarding, public command syntax changes, or remote authority expansion.

## Components And Ownership

- `pglite-lock`: owns lock inspection and stale/dead/corrupt/live classification. It must not know about commands or MCP.
- `pglite-operation-ipc`: owns local socket transport, protocol validation, queueing, priorities, timeouts, and owner response framing. It must not import CLI command modules.
- `pglite-owner-policy`: owns code-native row behavior class policy and caller/trust constraints. It is the runtime policy projection of the requirement 006 inventory.
- `pglite-owner-routing`: owns second-process route decisions before engine creation.
- Owner dispatch module: owns operation and command target execution inside the owner process.
- CLI layer: owns argv parsing, public command syntax, stream output, and exit verdict propagation.
- MCP layer: owns tool listing, JSON-RPC envelopes, auth/source scope threading, and remote caller semantics.
- Requirement/test validators: own inventory parity and coverage-ledger evidence; they may read requirement YAML and product policy.

## Dependency Direction

- CLI and MCP may depend on owner routing and IPC.
- Owner dispatch may depend on operation dispatch and curated command adapters.
- IPC may depend on transport primitives and request/response types only.
- Lock inspection remains below routing and never imports policy or command code.
- Runtime code must not import `requirements/**`.
- Test/validator code may import runtime policy and read `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml`.

## Runtime / Agent / Schema / Evidence Handoffs

- Runtime handoff:
  - Second process: parse request, resolve policy, inspect owner state, forward or guard before PGLite open.
  - Owner process: validate request, recheck policy and remote context, execute through engine already owned by the process, return typed response.
  - HTTP MCP: must use the same live-owner policy/routing/owner-dispatch contract or an accepted typed guard, preserving OAuth auth, source scope, request logging, JSON envelopes, and `remote=true`.
- Agent/MCP handoff:
  - Remote MCP calls retain `remote=true`, auth, source scope, takes holder allow-list, and localOnly rejection.
  - Local CLI `gbrain call` retains `remote=false` and source resolution semantics.
- Evidence handoff:
  - Requirement 007 implementation records policy parity, class-complete tests, typed error evidence, and updated gauntlet results.
  - Requirement 008 consumes that evidence to run the final repeated all-access matrix.

## Cross-Layer Invariants

- Live-owner PGLite direct open from a second process is forbidden for in-scope rows.
- Owner-owned serialization is the only accepted live-owner mutation execution path unless a row is typed-guard by accepted inventory.
- Command adapters are surface-id keyed and curated; no generic arbitrary argv execution crosses IPC.
- Additive v1-compatible IPC extension is the default; v2 requires recorded evidence that v1 compatibility cannot safely express the target.
- Remote authority can only stay the same or get stricter.
- Output/error compatibility is owned by the caller surface, not by low-level IPC.
- Completion-unknown is never silently retried by the caller.
- Raw PGLite lock/connect timeout text is diagnostic evidence only in tests; it is not an accepted product-boundary result.
- Requirement YAML is source-of-truth for planning/evidence but not runtime configuration.

## Risks And Rollback

- Risk: Expanding IPC target names could expose local-only operations remotely.
  - Mitigation: policy checks before forwarding and owner-side `remote=true` dispatch; parity tests against localOnly inventory.
- Risk: Command adapters that capture stdout/stderr could hide exit verdict drift.
  - Mitigation: adapter tests assert stdout, stderr, and exit code; avoid `process.exit` inside owner execution.
- Risk: HTTP MCP drifts from stdio MCP or loses auth/source/logging semantics.
  - Mitigation: HTTP-specific tests assert OAuth/auth scope, remote=true, request logging shape, and JSON envelope preservation.
- Risk: Long serialized mutations block interactive reads.
  - Mitigation: preserve request class/priority and timeout semantics; record completion_unknown explicitly.
- Risk: Runtime policy drifts from inventory.
  - Mitigation: test validator compares policy rows to the accepted 468-row inventory.
- Rollback: The implementation should be staged so the existing `query/search/think` broker path remains compatible. If broader policy fails, revert the new policy/adapter paths while preserving the existing narrow broker tests.
