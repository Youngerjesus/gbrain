# Requirement Decisions

## Decisions

### 2026-06-20 19:10 KST - Treat priority as bounded queue/checkpoint behavior

- Decision: Requirement 003 defines priority at the owner-broker queue boundary or safe maintenance checkpoints, not arbitrary mid-transaction process preemption.
- Rationale: PGLite lock safety must remain intact, and maintenance operations may not support safe interruption inside an active DB transaction.
- Alternatives considered: Claim full preemption of running maintenance work; defer all maintenance behavior to final verification.
- Status: accepted in draft pending reviewer.

### 2026-06-20 19:20 KST - Require per-command maintenance coverage matrix

- Decision: Requirement 003 cannot close on generic IPC maintenance-class tests alone; `sync`, `embed`, and `extract` each need real-command coverage, deterministic safe fallback evidence, or explicit user-approved blocked classification.
- Rationale: The sequence outcome names concrete commands. Synthetic queue evidence proves scheduler mechanics but not CLI command behavior or operator-facing fallback.
- Alternatives considered: Let implementation-brake decide command coverage later; rely on generic queue priority only.
- Status: accepted by reviewer rerun.

### 2026-06-20 19:35 KST - Advance requirement 003 to research

- Decision: Requirement 003 is ready for research after reviewer rerun returned `SHIP`.
- Rationale: The reviewer confirmed the draft now prevents overclaiming synthetic queue tests as real `sync`/`embed`/`extract` command evidence and contains the required contract preservation and iteration policy.
- Alternatives considered: Ask for user confirmation before research; run another reviewer pass.
- Status: accepted.

### 2026-06-20 19:50 KST - Use maintenance deferral instead of brokering maintenance commands

- Decision: Requirement 003 will not add `sync`, `embed`, or `extract` as brokered operations. A maintenance command that already owns PGLite will expose the existing owner broker; a second maintenance command will be classified before `connectEngine()` and receive deterministic fallback while a live owner exists.
- Rationale: The broker currently dispatches operation-level `query`, `search`, and `think`; brokering real maintenance commands would require command-specific schema, output, cancellation, and lifecycle contracts beyond this slice. Pre-connect deferral closes the lock-timeout storm while preserving lock safety and public syntax.
- Alternatives considered: Add maintenance operations to `OperationIpcOperation`; add mid-command yield/preemption; leave second maintenance callers to PGLite lock timeout.
- Status: accepted by research.
