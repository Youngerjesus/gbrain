# Requirement Decisions

## Decisions

### 2026-06-21 00:25 KST - Requirement 006 inventory is authoritative for 007

- Decision: Requirement 007 must consume `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml` as the row-level implementation contract.
- Rationale: The sequence intentionally split inventory/reproduction from implementation. Re-discovering or narrowing scope in 007 would reopen requirement 006 and risk representative-only fixes.
- Applies to: requirement, research, technical-design, planning, implementation, implementation-brake
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Requirement 008 owns final full repeated matrix proof

- Decision: Requirement 007 must implement all accepted behavior classes and produce class-complete targeted evidence, while requirement 008 remains responsible for proving the full repeated named matrix has zero raw lock/connect timeout.
- Rationale: This keeps implementation and final verification as separate slices without allowing 007 to claim completion from narrow representative evidence.
- Applies to: requirement, verification, coverage ledger, closeout
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Coverage ledger required

- Decision: Requirement 007 requires `coverage-decision.yml` and `coverage-ledger.yml`.
- Rationale: The slice spans 468 inventory rows, three behavior classes, multiple CLI/MCP surfaces, owner-state variants, remote trust boundaries, and runtime/test modules.
- Applies to: requirement acceptance, planning, implementation, closeout
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Runtime policy must be code-native with inventory parity tests

- Decision: Do not make product runtime read `pglite-access-inventory.yml`; implement code-native TypeScript policy/dispatch tables and validate them against the requirement 006 inventory in tests or scripts.
- Rationale: Keeps product runtime independent of requirement YAML while preserving 468-row inventory coverage through deterministic parity evidence.
- Applies to: technical-design, implementation, tests
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Existing local IPC substrate should be generalized

- Decision: Reuse the existing local Unix-socket owner IPC and queue, extending operation identity/policy beyond `query`, `search`, and `think`.
- Rationale: The IPC already provides local-only owner dispatch, queueing, timeout statuses, and tested failure states; replacing it would add unnecessary risk.
- Applies to: technical-design, implementation, verification
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Requirement 007 evidence is class-complete, not final all-row matrix

- Decision: Requirement 007 must produce class-complete targeted implementation proof; requirement 008 owns the final N=3 all-row named matrix.
- Rationale: Preserves the accepted sequence boundary and prevents representative tests from being overclaimed as final verification.
- Applies to: technical-design, plan-eng-review, implementation-brake, closeout
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Create requirement-local architecture artifact

- Decision: Requirement 007 needs `architecture.md` in addition to `technical-design.md`.
- Rationale: The slice changes local owner runtime handoffs across CLI, MCP, IPC, lock inspection, owner dispatch, and evidence validators; cross-layer invariants need a separate architecture boundary record.
- Applies to: technical-design, plan-eng-review, implementation
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Command adapters return output instead of calling process.exit

- Decision: Owner-side CLI command adapters must return stdout, stderr, and exitCode to the caller process instead of calling `process.exit`.
- Rationale: The owner process is long-lived and must not terminate because a forwarded command wants a nonzero CLI verdict.
- Applies to: implementation, tests
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Additive v1-compatible IPC extension is the default

- Decision: Extend the existing owner IPC request shape additively by default, preserving legacy v1 query/search/think behavior unless implementation proves that impossible and records a requirement impact.
- Rationale: The current local socket, queueing, timeout, and stale-socket recovery substrate is already tested; a protocol replacement would add avoidable scope and compatibility risk.
- Applies to: technical-design, implementation, tests
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Command adapters are surface-id keyed and curated

- Decision: Owner-side command adapters must be keyed by accepted inventory surface id and may only cover true command-module/open-site rows that cannot use operation dispatch; no generic argv executor may be exposed over IPC.
- Rationale: This preserves the owner boundary without creating an overbroad command execution channel.
- Applies to: architecture, implementation, tests
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Scenario-brake is required before implementation

- Decision: Run scenario-brake and reconcile its scenario matrix into the secondary plan before implementation starts.
- Rationale: Requirement 007 has many distinct entry paths, owner states, trust boundaries, timeout states, and recovery outcomes; implementation readiness needs explicit scenario separation.
- Applies to: planning, secondary-plan, implementation
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Scenario-brake additions are implementation obligations

- Decision: Treat duplicate owner startup, separated owner-state matrix, serialized mutation `completion_unknown` re-entry, owner crash/restart after accept, partial/misleading command adapter output, filesystem payload drift, IPC version skew, wrong-owner identity, and mandatory request/status correlation as requirement 007 implementation evidence obligations.
- Rationale: Scenario-brake found missing scenario separations but no plan reframe; preserving them in the secondary plan and coverage ledger prevents a happy-path broker fix from overclaiming closeout.
- Applies to: secondary-plan, implementation, coverage-ledger closure, implementation-brake
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Accepted primary and secondary plans are implementation handoff

- Decision: Treat `plans/007-pglite-broker-guard-implementation/plan.md` and `plans/007-pglite-broker-guard-implementation/secondary_plan.md` as the local implementation handoff for requirement 007.
- Rationale: Plan-devex-review, plan-eng-review, and scenario-brake findings have been reconciled into the primary plan and preserved in the secondary guardrails before implementation.
- Applies to: worktree preflight, context-loading, implementation, implementation-brake
- Status: accepted
- Requirement Impact: none

### 2026-06-21 00:25 KST - Lifecycle, daemon, reset, and heavy local commands use typed guards under live owner

- Decision: Reclassify live-owner handling for local lifecycle/session/heavy commands that cannot safely run inside the owner broker as `typed_guard_fail_fast` instead of `serialized_owner_mutation`: `autopilot`, `claw-test`, `frontmatter`, `init`, `integrity`, `mounts`, `reinit-pglite`, `repair-jsonb`, `schema`, and `watch` variants. Keep `serve` on the owner-startup/proxy path.
- Rationale: These commands either start long-lived sessions, manage lifecycle/reset/schema/repair state, or execute local harness/config flows where running them inside the owner IPC handler would risk blocking the owner, destructive side effects, or misleading partial success. The user approved this treatment after asking how mutating/heavy maintenance commands should behave.
- Applies to: inventory, runtime policy, CLI live-owner guard, tests, requirement counts
- Status: accepted
- Requirement Impact: accepted inventory class counts changed from 217/236/15 to 217/223/28 for `broker_success_read` / `serialized_owner_mutation` / `typed_guard_fail_fast`.
