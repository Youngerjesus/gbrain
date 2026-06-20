# Requirement Decisions

## Decisions

### 2026-06-20 22:24 KST - Scenario coverage hardening

- Decision: Requirement 006 must explicitly cover no-owner versus live-owner state separation, owner startup and duplicate-owner-start handling, mode-sensitive row granularity, MCP transport representative evidence, lock/broker split-brain states, harness environment hygiene, row-specific data preconditions, result-manifest completeness, and cleanup/restart-after-failure evidence.
- Rationale: Scenario-brake found that the prior plan could produce a passing inventory/gauntlet while conflating no-owner direct-open behavior with live-owner behavior, hiding subcommand/flag differences inside coarse command rows, mistaking harness setup failures for product row outcomes, or closing evidence with omitted runnable rows.
- Alternatives considered: accept healthy-owner gauntlet as sufficient; treat command groups as single rows; defer MCP transport evidence to requirement 008; rely on teardown best effort without manifest fields.
- Impact: Technical design and primary plan now require explicit row granularity, setup/readiness fields, split-brain fixture coverage, environment scrubbing/backend confirmation, transport representative coverage or non-runnable rationale, data preconditions, result-manifest validation, and cleanup/restart evidence.
- Source artifact: scenario-brake companion synthesis recorded in progress/evidence and reflected into `plans/006-pglite-access-path-inventory/plan.md`
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none for scenario-brake; secondary-plan remains required before implementation.

### 2026-06-20 22:24 KST - Plan Eng contract hardening

- Decision: The inventory validator must compare YAML rows against code-derived PGLite candidate sets, the gauntlet must use inventory row ids as its canonical matrix, expected-red rows must record both current and future outcomes, and closeout must validate the coverage ledger in closure mode.
- Rationale: A curated-only inventory could falsely pass while omitting real PGLite paths; a separate gauntlet matrix could drift from the requirement-007 handoff; loose expected-red semantics could allow current failures to be mistaken for accepted final behavior.
- Alternatives considered: curated `required_surface_ids` only; gauntlet-local matrix ids; readiness-mode ledger validation at closeout; generic expected-red assertion.
- Impact: Technical design and primary plan now require code-derived candidate extraction, pinned enum validation, raw-timeout fixture corpus, serial live-owner gauntlet path, and owner/subprocess harness reuse or justification.
- Source artifact: `plans/006-pglite-access-path-inventory/reviews/plan-eng-review.md`
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none for plan-eng-review; scenario-brake and secondary-plan remain required before implementation.

### 2026-06-20 22:24 KST - Research source-of-truth and gauntlet policy

- Decision: Requirement 006 inventory must be derived from the `operations` registry, CLI-only dispatcher, MCP transport filters, and PGLite open-site/lock code; the minimal reproducing gauntlet should use N=3 concurrent attempts per runnable matrix row in a temporary PGLite home.
- Rationale: The shared operation registry alone misses CLI-only commands, while CLI command names alone miss `gbrain call` access to all operations. A safe named matrix must include existing broker-success controls, direct-open read/diagnostic failures, and safe non-execution/dry-run evidence for destructive or irreversible paths.
- Alternatives considered: grep-only discovery; importing `operations` at runtime; executing every command concurrently; limiting the matrix to read-only commands.
- Impact: Technical design must define the inventory schema, validation strategy, and safe gauntlet rows from these sources without weakening the all-path scope.
- Source artifact: `requirements/006-pglite-access-path-inventory/research.md`
- Requirement Impact: none
- Blocking/non-blocking unresolved items: exact inventory schema, row classifications, and final executable matrix are non-blocking for research and owned by technical-design/implementation.

### 2026-06-20 22:24 KST - Inventory schema and validator design

- Decision: Requirement 006 will use `requirements/006-pglite-access-path-inventory/pglite-access-inventory.yml` plus a repo-local validator/test harness; product runtime must not import requirement artifacts or gain new broker behavior in this slice.
- Rationale: A structured YAML handoff keeps operation classification reviewable for requirement 007, while validator and gauntlet tests make the artifact executable enough to avoid documentation-only foundation drift.
- Alternatives considered: prose-only inventory; JSON artifact instead of YAML; runtime product instrumentation as the inventory source.
- Impact: Implementation must add the inventory artifact, schema/required-surface validation, and expected-red/safe gauntlet evidence before closeout.
- Source artifact: `requirements/006-pglite-access-path-inventory/technical-design.md`
- Requirement Impact: none
- Blocking/non-blocking unresolved items: exact implementation worktree path and final row count are non-blocking until pre-implementation.

### 2026-06-20 22:24 KST - Plan DevEx obligations

- Decision: The implementation plan must require row-specific validator and gauntlet diagnostics, and it must separate fast validator/unit checks from slow serial live-owner gauntlet checks.
- Rationale: Requirement 007 implementers need actionable evidence, not a generic failing matrix. Fast/slow split keeps the feedback loop usable while preserving live concurrency evidence.
- Alternatives considered: generic nonzero validator failure; single all-in serial test command; public docs in this slice.
- Impact: Validator negative tests and gauntlet result assertions must prove diagnostic shape, and closeout must record both verification tiers.
- Source artifact: `plans/006-pglite-access-path-inventory/reviews/plan-devex-review.md`
- Requirement Impact: none
- Blocking/non-blocking unresolved items: none for plan-devex-review.

### 2026-06-20 18:16 KST - Sequence scope and first-slice shape

- Decision: The new sequence covers every PGLite-touching path, and the first requirement combines access-path inventory with a minimal failing/reproducing concurrency gauntlet before behavior fixes.
- Rationale: The prior sequence intentionally solved only `query`, `search`, and `think`; jumping straight to another partial implementation would risk leaving hidden direct PGLite access paths unresolved.
- Alternatives considered: immediately implement broker expansion for known commands; limit scope to read/diagnostic commands; leave mutating/heavy maintenance out of scope.
- Impact: Later requirements must consume this inventory and choose broker-success, serialized owner mutation, or typed guard-fail-fast behavior per operation.
- Source artifact: current conversation and `goal-requirements/002-pglite-all-access-concurrency/sequence.md`
- Requirement Impact: approved by user
- Blocking/non-blocking unresolved items: exact inventory schema and N value are non-blocking for requirement acceptance, owned by research/technical-design.

### 2026-06-20 18:16 KST - Product boundary is zero raw lock/connect timeout

- Decision: In-scope paths must not expose raw PGLite lock/connect timeout as the product-boundary result under a live owner; typed fail-fast is acceptable when recorded as the intended behavior.
- Rationale: The user wants the limitation addressed across all PGLite paths while preserving safety for mutating/heavy maintenance operations.
- Alternatives considered: require every path to succeed concurrently; allow current timeout semantics for risky commands.
- Impact: Tests must distinguish successful broker routing from typed guard-fail-fast and raw timeout failure.
- Source artifact: current conversation
- Requirement Impact: approved by user
- Blocking/non-blocking unresolved items: exact typed error vocabulary is non-blocking for this slice, owned by requirement 007 design.
