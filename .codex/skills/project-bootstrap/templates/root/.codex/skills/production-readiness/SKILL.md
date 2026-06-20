---
name: production-readiness
description: Final MVP launch readiness gate for goal-requirements sequences; use after feature slices pass closeout and before marking a sequence production-ready or complete.
---

# Production Readiness

Use this skill as the final sequence-level launch gate for an MVP, production deployment, beta launch, or first real-user exposure.

This skill answers a different question than `implementation-brake` or `closeout`:

- `implementation-brake` decides whether a completed code change can ship as an implementation slice.
- `closeout` reconciles the completed slice and local state after `[SHIP]`.
- `production-readiness` decides whether the assembled MVP can be safely exposed to real users and operated after launch.

## When To Run

Run this gate after all functional MVP requirement slices have passed their required gates, `implementation-brake`, verification, and `closeout`, and before marking the goal sequence complete.

For a goal-requirements MVP sequence, reserve a final readiness slice such as:

```text
requirements/<goal-id>-production-readiness/requirements.md
```

If that requirement file is missing or stale when the sequence reaches the final slice, create or update it with `requirement-clarifier` before running this skill. Do not invent acceptance criteria only inside the chat transcript.

## Required Inputs

Gather current evidence before issuing a verdict:

- the goal sequence, sequence progress, and final readiness requirement
- completed requirement evidence for the MVP slices
- accepted plans and decisions that affect deployment, operations, data, external dependencies, or launch scope
- `scripts/verify` result and any required `scripts/verify*` or live smoke evidence
- deployment target, environment variables, secrets policy, migration path, rollback or repair path
- observability evidence: health checks, logs, metrics, alerts, error reporting, or documented diagnostic commands
- performance evidence for common paths: query plans, indexes, bounded loops, queue/backlog behavior, or load smoke checks when relevant
- external dependency status: domains, DNS, OAuth, email, payment, storage, CDN, third-party APIs, accounts, and human-owned setup
- operator runbook or handoff notes for launch, incident triage, and known limitations

## Review Checklist

Review only launch readiness, not the feature implementation from scratch.

1. Launch boundary: who will use this, in which environment, and what "production" means for this MVP.
2. Deployment: reproducible build, deploy command, environment separation, config, secrets, migrations, and rollback or repair.
3. External setup: domain, DNS, certificates, OAuth apps, payment/email/storage/provider accounts, quotas, and ownership.
4. Data safety: schema migration safety, backup/restore expectations, destructive operations, retention, and seed/test data separation.
5. Observability: health endpoints, logs, metrics, alerts, error tracking, operator-visible status, and diagnostic commands.
6. Stability: timeouts, retries, rate limits, idempotency, graceful degradation, job recovery, and restart behavior.
7. Performance: common queries, indexes, N+1 risks, unbounded scans, request latency, background workload, and resource ceilings.
8. Security and privacy: auth/authz, secret handling, input validation, dependency exposure, user data handling, and least privilege.
9. Verification: baseline checks, required live smoke checks, critical user journeys, and evidence freshness.
10. Launch handoff: known limitations, external human tasks, owner, due condition, and whether the limitation blocks first exposure.

## Blocker Classification

Classify every unresolved item using exactly one of these states:

- `ready`: no unresolved launch blocker remains.
- `ready_with_external_handoff`: launch may proceed after explicit human-owned external tasks are recorded with owner, action, and acceptance signal.
- `blocked_internal`: repo-owned code, config, data, performance, observability, security, deployment, or documentation work must be completed before launch.
- `blocked_external`: launch depends on unavailable human action, account access, domain/DNS, vendor approval, production credential, or infrastructure outside the repo.
- `deferred_non_goal`: real issue, but outside the accepted launch boundary and not required for this MVP exposure.

Do not hide an internal blocker behind `ready_with_external_handoff`. External handoff is for tasks Codex cannot complete inside the repo, not for unfinished implementation work.

## Workflow

1. Rehydrate state from the sequence, the readiness requirement, all requirement evidence, and current git status/diff.
2. Confirm every non-readiness requirement is checked complete and has closeout evidence. If not, stop with `[PRODUCTION READINESS BLOCKED]`.
3. Confirm the readiness requirement exists, is accepted, and describes the actual launch boundary. If it is missing or stale, route to `requirement-clarifier`.
4. Review the checklist using direct evidence. Prefer product-owned files, commands, dashboards, logs, smoke results, and structured artifacts over conversational claims.
5. Classify unresolved work as `ready`, `ready_with_external_handoff`, `blocked_internal`, `blocked_external`, or `deferred_non_goal`.
6. For `blocked_internal`, create or request a new requirement slice before sequence completion.
7. For `blocked_external`, record the owner, needed action, evidence needed to unblock, and whether Codex can continue without it.
8. Update the readiness requirement's `progress.md`, `decisions.md`, and `evidence.md`, plus sequence-level `progress.md`.

## Verdicts

Use one final verdict:

- `[PRODUCTION READY]`: final state is `ready`; the sequence may be marked complete after state files are reconciled.
- `[PRODUCTION READY WITH EXTERNAL HANDOFF]`: final state is `ready_with_external_handoff`; the sequence may complete only if the user explicitly accepts the recorded external handoff.
- `[PRODUCTION READINESS BLOCKED]`: any unresolved item is `blocked_internal` or launch-blocking `blocked_external`; do not mark the sequence complete.

`deferred_non_goal` items may remain only when they are explicitly outside the MVP launch boundary and have a recorded reason.

## Output Shape

Report:

1. Launch boundary reviewed
2. Evidence checked
3. Readiness findings by blocker classification
4. Required internal follow-up slices
5. External handoff items
6. Deferred non-goals
7. Final verdict

Keep the final report concise. Store durable evidence and handoff details in requirement state files, not only in chat.
