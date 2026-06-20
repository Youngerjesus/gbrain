# Technical Research: PGLite Access Path Inventory

Created: 2026-06-20
Status: Complete
Requirement source: requirements/006-pglite-access-path-inventory/requirements.md

## Research Decisions

### RD-001: Discovery must combine operation registry, CLI dispatcher, and PGLite open-site evidence

- Question: What source evidence is authoritative enough to prove "all PGLite-touching paths" without relying on loose string scans?
- Decision: The inventory must be derived from three structured surfaces: the `operations` array in `src/core/operations.ts`, the CLI-only command sets and dispatcher switch in `src/cli.ts`, and PGLite open-site/broker code in `src/core/engine-factory.ts`, `src/core/pglite-engine.ts`, `src/core/pglite-lock.ts`, and `src/core/pglite-operation-ipc.ts`.
- Rationale: `operations.ts` is the contract-first registry for shared CLI/MCP operations. `src/cli.ts` also contains many CLI-only commands that bypass the shared operation layer. PGLite ownership is established when `createEngine()` selects `PGLiteEngine`, and `PGLiteEngine.connect()` acquires the PGLite lock before `PGlite.create()`.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | --- | --- | --- | --- |
  | Grep for command names and `engine.` calls only | Fast | Omission-prone; not semantic enough for acceptance | Rejected |
  | Import `operations` at runtime | Structured | Current Bun import hit a zod cached-value initialization error before output | Rejected for research; may still be revisited in implementation with a test-safe harness |
  | TypeScript AST extraction plus direct source reads | Structured, avoids module side effects, repeatable | Requires a small repo-native helper or test fixture later | Accepted |
- Risk: AST extraction must be schema-validated so future object shapes or inline operations do not silently drop rows.
- Evidence: `src/core/operations.ts`, `src/cli.ts`, `src/core/engine-factory.ts`, `src/core/pglite-engine.ts`, `src/core/pglite-lock.ts`, `src/core/pglite-operation-ipc.ts`; local AST extraction command captured operation name/scope/localOnly/CLI-hint rows.

### RD-002: `gbrain call` makes every shared operation a local trusted PGLite access path

- Question: Should the inventory cover only operations that have direct CLI names, or every operation in `operations.ts`?
- Decision: Every shared operation row in `operations.ts` is in scope because `gbrain call <tool> <json>` dispatches to `handleToolCall()` with `remote: false` and a resolved local source.
- Rationale: `gbrain call list_pages` is the observed failing surface under a live owner, but the same call path can invoke read, write, admin, localOnly, file-touching, and schema/config operations. Limiting to visible CLI names would miss trusted-local operation access.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Inventory visible CLI hints only | Smaller matrix | Misses `call`-only operations and localOnly admin/file ops | Rejected |
  | Inventory all shared operations but test only known failures | Complete scope with bounded first gauntlet | Requires classification to distinguish safe live execution from safe non-execution | Accepted |
  | Inventory MCP-exposed ops only | Aligns with agent tools | Misses trusted local CLI boundary and the observed `call` failure | Rejected |
- Risk: Some shared operations are mutating or filesystem-sensitive; the gauntlet must use dry-run/safe fixtures or safe non-execution rows rather than executing destructive operations against real data.
- Evidence: `src/commands/call.ts` resolves source and calls `handleToolCall(engine, tool, params, { sourceId })`; `src/mcp/server.ts` documents that `handleToolCall` is the trusted local path; `src/mcp/dispatch.ts` defaults remote callers to untrusted while CLI call passes `remote: false`.

### RD-003: Current broker coverage is intentionally narrow and must remain a baseline row set

- Question: Which paths are already covered by the owner broker, and how should they appear in the inventory?
- Decision: `query`, `search`, and `think` are existing broker-success baseline rows. They must remain in the inventory and gauntlet as existing-pass controls, not as the whole scope.
- Rationale: `src/cli.ts` defines `BROKERED_OPERATIONS` as `query`, `search`, and `think`; `src/core/pglite-operation-ipc.ts` defines `OperationIpcOperation` and `VALID_OPERATIONS` with the same three operations. `test/pglite-concurrent-access.serial.test.ts` proves a real owner and proxy serve can handle those CLI/MCP interactive callers without raw lock failures.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Exclude already-solved brokered ops | Focuses on failures | Loses regression control for the prior fix | Rejected |
  | Treat brokered ops as the only runnable gauntlet | Easy | Violates AC3/AC5 and repeats the prior scope limit | Rejected |
  | Include brokered ops as controls beside direct-open candidates | Preserves regression and widens coverage | Slightly larger matrix | Accepted |
- Risk: If broker baseline tests are expensive, the first-slice gauntlet may use a focused subset, but the inventory must still include the full baseline rows.
- Evidence: `src/cli.ts`, `src/core/pglite-operation-ipc.ts`, `test/pglite-concurrent-access.serial.test.ts`.

### RD-004: Maintenance deferral currently covers only `sync`, `embed`, and `extract`

- Question: Which heavy maintenance paths already avoid direct open under a live owner?
- Decision: The inventory must record `sync`, `embed`, and `extract` as currently guarded by maintenance deferral, then separately classify whether the accepted future behavior is `serialized_owner_mutation` or `typed_guard_fail_fast`.
- Rationale: `src/cli.ts` defines `PGLITE_MAINTENANCE_COMMANDS` as `sync`, `embed`, and `extract`, and `maybeDeferPgliteMaintenanceCommand()` returns a typed `maintenance_deferred` broker failure before direct `connectEngine()` when the PGLite lock is live. This is not owner execution; it is a guard/defer behavior.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Treat maintenance deferral as already fixed | Simple | Does not prove all paths and does not serialize owner mutation | Rejected |
  | Require concurrent success for all maintenance | Strong | Unsafe for schema/file/heavy mutation without later design | Rejected |
  | Preserve typed guard as allowed future behavior when justified | Matches user decision and safety boundary | Requires explicit classification per command | Accepted |
- Risk: A user-supplied `--timeout` can still influence connect behavior for commands outside this set; the gauntlet must capture raw connect timeout separately from typed maintenance deferral.
- Evidence: `src/cli.ts`; earlier live check showed `gbrain sync --no-pull --no-embed --yes` returned `maintenance_deferred` under a live owner.

### RD-005: CLI-only DB-bound commands are in scope even when no MCP equivalent exists

- Question: Which non-operation CLI paths need inventory rows?
- Decision: The inventory must include every CLI-only command that reaches `connectEngine()` or otherwise creates an engine internally, including at minimum `call`, `config`, `doctor`, `sources`, `stats`/`health` operation aliases, `files`, `import`, `export`, `migrate`, `apply-migrations`, `eval`, `jobs`, `sync`, `embed`, `extract`, `enrich`, `features`, `autopilot`, `graph-query`, `reindex*`, `capture`, `watch`, `storage`, code-intel commands, `takes`, `founder`, `brainstorm`, `lsd`, `schema`, `onboard`, `skillopt`, and source/repo aliases.
- Rationale: After read-only timeout handling and the limited maintenance deferral, `src/cli.ts` calls `connectEngine()` once and dispatches many CLI-only commands with the same local PGLite engine. Several pre-engine branches also create their own engine or shell out to engine-using flows, such as `doctor --remediate`, `doctor --remediation-plan`, `apply-migrations`, and `cache`.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Only cover commands named by the user | Faster | Violates "all PGLite-touching paths" and misses adjacent direct-open bugs | Rejected |
  | Cover all CLI-only names as PGLite-touching | Complete but noisy | Some commands are pure filesystem/config and need `existing_direct_when_no_owner` or non-DB classification | Accepted as discovery input, not final classification |
  | Start from connect/open sites and back-map commands | Precise | Needs structured artifact/test support in implementation | Accepted for technical design |
- Risk: Some listed commands may prove no-DB or pure remote. They still need explicit non-PGLite or out-of-scope classification evidence rather than silent omission.
- Evidence: `src/cli.ts` `CLI_ONLY`, `THIN_CLIENT_REFUSED_COMMANDS`, `handleCliOnly()`, the main CLI dispatch switch, and `connectEngine()`.

### RD-006: Remote MCP exposure is `operations.filter(op => !op.localOnly)`, with HTTP scope enforcement

- Question: How should the inventory distinguish trusted local CLI from remote MCP exposure?
- Decision: Each shared operation row must record both local `gbrain call` exposure and MCP exposure. Stdio MCP uses all operations in `buildToolDefs(operations)`, while HTTP MCP filters `operations.filter(op => !op.localOnly)` and enforces scopes before dispatch. For the live-owner proxy path, `startMcpOperationProxyServer()` currently exposes only `query`, `search`, and `think`.
- Rationale: The trust boundary differs by transport: CLI `call` is trusted local, stdio/HTTP MCP set `remote: true`, HTTP excludes `localOnly`, and operation handlers may tighten filesystem/path behavior when `ctx.remote !== false`.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | One row per operation only | Compact | Hides different trust and exposure contracts | Rejected |
  | Separate rows per operation and caller/transport | Clear handoff to requirement 007 | Larger artifact | Accepted |
  | Ignore HTTP MCP because sequence is local PGLite | Simpler | HTTP `serve --http` is a PGLite owner path and remote agent surface | Rejected |
- Risk: Stdio MCP currently lists all operations, but localOnly semantics are still enforced in handlers/transport differences; the inventory must capture actual exposure and runtime guard behavior rather than assume parity.
- Evidence: `src/mcp/server.ts`, `src/mcp/dispatch.ts`, `src/commands/serve-http.ts`, `src/core/operations.ts`.

### RD-007: Gauntlet should use a named matrix with safe execution classes, not a destructive all-command blast

- Question: How can the first slice reproduce current failures without mutating real user data or forcing irreversible commands?
- Decision: The first-slice gauntlet should run a minimal named matrix under a temporary PGLite home with a live `gbrain serve` owner. It should include existing broker-success controls, known direct-open read/diagnostic failures, and safe typed-guard/non-execution rows for mutating, migration, remediation, and file-touching commands. Use N=3 concurrent attempts per runnable matrix entry for requirement 006; later sequence verification can raise the repetition count after implementation.
- Rationale: The user asked for a named command matrix with exit code, stderr, and error-shape capture. Requirement 006 is explicitly a reproducer/inventory slice, not a behavior fix. Destructive paths should be represented with dry-run, fixture data, or safe non-execution classification.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Execute every command concurrently | Maximum confidence | Unsafe for migrations, remediation, file deletion, external services, and user data | Rejected |
  | Only run read commands | Safe | Omits mutating/heavy maintenance scope | Rejected |
  | Run safe entries and require explicit safe-non-execution rows for dangerous entries | Safe and complete | Requires schema support for evidence classification | Accepted |
- Risk: The red reproducer may be timing-sensitive if it depends on connect timeouts. The harness must capture raw timeout text and exit code, and keep expected-red assertions narrow.
- Evidence: `test/pglite-concurrent-access.serial.test.ts` existing subprocess harness; `src/cli.ts` timeout/read-only handling; `src/core/pglite-operation-ipc.ts` broker response statuses.

### RD-008: Research does not change the accepted requirement scope

- Question: Did research uncover a requirement-impact change needing user approval?
- Decision: No requirement impact is needed. The user-approved scope remains feasible: all PGLite-touching paths are inventoried; unsafe paths are classified through `serialized_owner_mutation` or `typed_guard_fail_fast`, not removed.
- Rationale: The code evidence confirms the prior limitation and supports the accepted first-slice shape. The main uncertainty is implementation design, not product scope.
- Alternatives Considered:
  | Option | Pros | Cons | Verdict |
  | Ask to exclude CLI-only heavy paths | Smaller | Directly contradicts user answer | Rejected |
  | Ask to allow raw timeouts for risky paths | Simpler | Contradicts sequence outcome | Rejected |
  | Preserve scope and design safe classifications | Matches requirement | Requires careful design and tests | Accepted |
- Risk: Exact classification of individual rows may shift during technical design as deeper handler evidence is gathered.
- Evidence: `requirements/006-pglite-access-path-inventory/requirements.md`; code sources listed above.

## Requirement Impact

- None.

## Unresolved Items

| Item | Blocking? | Rationale | Downstream owner |
| --- | --- | --- | --- |
| Exact final inventory YAML schema | non_blocking | Research selected the structured artifact path and required fields; technical-design must pin schema and validator mechanics before implementation. | technical-design |
| Exact operation-by-operation behavior class | non_blocking | Research defined the evidence sources and allowed classes; implementation inventory will fill every row. | implementation |
| Final command matrix row list | non_blocking | Research defined the safe execution policy and N=3 requirement-006 concurrency count; technical-design must convert it into executable fixtures. | technical-design |
| Runtime import failure for `operations` | non_blocking | AST parsing succeeded without module side effects; technical-design can use AST or a test-safe helper instead of runtime import. | technical-design |

## Gate Self-Review

- All technical unknowns from the requirement were addressed or classified.
- Every decision has rationale and alternatives, unless a standard path is justified.
- Requirement Impact is absent.
- Every unresolved item is classified as non_blocking with a downstream owner.
- Evidence paths/sources are recorded in evidence.md.
