# Closed Loop Harness Design Packet

Use this packet when the target project lacks its own closed-loop harness design format.

## Task

- Request:
- Target artifact or decision:
- Target repo/root:
- Relevant AGENTS or project guidance:
- Existing harness/eval/test/trace utilities found:
- Reuse, extend, replace, or defer decision:

## Loop Fit

- Is a loop needed, or is direct execution enough:
- Target state:
- Current state:
- Distance signal:
- Failure-cause signal:
- Allowed intervention size:
- Iteration budget:
- Stop condition:
- Fail-fast condition:
- Escalation condition:
- Why convergence is plausible:
- Why this is not Goodhart-prone, or how Goodhart risk is controlled:
- Convergence cost estimate:
- Expensive call budget:
- Deferred finding count:
- Repeated failure categories:
- Safe deterministic batchability:
- Batch repair policy:
- Batch regression or partial-success handling:

## Loop Family

- Selected family or hybrid:
- State values:
- Transition rules:
- Actor authority:
- Reject path:
- Recovery and resume path:
- Duplicate active-run handling:
- Terminal or already-done handling:
- Reopen versus resume rule:
- Collision-safe trace/log write mechanism:
- Stale active-run cleanup or escalation:

## Shared Harness Contract

- Lifecycle owner:
- State record shape:
- Evaluation record shape:
- Decision record shape:
- Trace record shape:
- Running-log fields:
- Artifact inspection hooks:
- Stale artifact or stale feedback protection:
- Structured validation or parser used:

## Runtime Dependency Allowlist

| Dependency | Owner stage | Purpose | Run-local source | Auth/cache requirement | Expected signal | Failure classification | Fallback or block behavior |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## Contract Gauntlet

| Stage | Boundary crossed | Artifact producer | Downstream consumer | Preflight method | Runtime dependency snapshot | Pass/fail/block signal | Successor action |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

- Applies to new harness design:
- Applies to existing/partial harness reuse, extension, replacement, or deferral:
- Prior gauntlet evidence ref:
- Freshness condition:
- Invalidation triggers:
- Duplicate or concurrent preflight handling:
- Reopen, rerun, no-op, block, or escalation rule:
- Whether full live execution is allowed, blocked, or only weakly evidenced:

## Downstream Artifact Contract Preflight

| Artifact or bundle | Producer | Consumer | Identity/freshness source | Schema/format/graph rule | Evidence/provenance owner | Failure classification | Verification method | Retry/quarantine/no-promotion/block behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |

- Artifact bundle or graph manifest rule:
- Cross-artifact reference or ordering rule:
- Dynamically discovered downstream consumer handling:
- Fields the generator/evaluator/judge may reference but not create:
- Stale, partial, or provenance-invalid output rejection rule:
- Candidate artifact quarantine or diagnostic-retention rule:

## Domain Adapter Contract

- Domain goal:
- Artifact target:
- Generator binding:
- Evaluator binding:
- Deterministic checks:
- LLM judge rubric:
- LLM judge verdict schema:
- False-pass risk and mitigation:
- False-fail tracking:
- Required evidence refs:
- Evidence and provenance source of truth:
- Downstream artifact consumers:
- Downstream artifact contract preflight:
- Runtime dependency declarations:
- Confidence policy:
- Severity classification:
- Primary finding or next-focus selection rule:
- Deterministic batch repair grouping criteria:
- Non-conflicting target scope rule:
- Regression checks for batch repair:
- Batch repair fallback when partial, conflicting, or regressive:
- Accept/retry/reject thresholds:
- Search/prune criteria:
- Diagnosis hypotheses, if relevant:
- Real-domain pilot path, if safe:

## 1.5 Validation Evidence

- Focused harness test command:
- Adapter or fixture test command:
- Deterministic smoke fixture:
- Real domain pilot path, if safe:
- First generator output ref:
- Evaluator feedback ref:
- Feedback id or category consumed:
- Second generator action ref:
- Artifact change or diff ref:
- Next eval result or decision ref:
- Evidence that the second generator consumed feedback:
- If skipped or blocked, why:

## Running Log

| Iteration | Current best score/state | Changed this round | Improved | Worsened | Next thing to try | Remaining risks |
| --- | --- | --- | --- | --- | --- | --- |
| 1 |  |  |  |  |  |  |

## Review Handoff

- Reviewer packet includes diff or artifact:
- Requirements included:
- Verification method included:
- Execution trace included:
- Evaluation output included:
- Artifact evidence included:
- Reviewer perspectives:
- Adjudicator:
- False-positive filtering method:

## Blocked-Run Report

- Required check:
- Blocker:
- Failure classification:
- Failed Contract Gauntlet stage:
- Downstream consumer protected:
- Candidate artifact promotion status:
- Run-local dependency evidence:
- Fixture-only or weak-preflight evidence:
- Weaker evidence available:
- What would unblock:
- Completion impact:

## Final Decision

- Decision: `PASS`, `FAIL`, `ACCEPT`, `RETRY`, `REJECT`, `FAIL_FAST`, or `BLOCKED`
- Decision evidence:
- Targeted improvement:
- Regressions or worsening:
- Remaining risk:
- Future domain pilot obligations:
