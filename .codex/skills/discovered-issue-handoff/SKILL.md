---
name: discovered-issue-handoff
description: Create a local diagnostic handoff report only after the user explicitly asks or approves it for a separable issue found during other work.
---

# Discovered Issue Handoff

Use this skill only when a separate issue is discovered while solving another problem and the user explicitly asks for, or approves, creating a handoff report.

Reference:
- `references/report_template.md`

## Purpose

Create a local observation packet that helps a later Codex session revalidate and investigate a separable issue. These reports are not backlog items, specs, approvals, task queue entries, SSOT, progress truth, or current artifact truth.

Generated reports live in:

```text
.runtime/discovered-issues/
```

## Use Only When

All of these must be true:
- The user explicitly requests or approves report creation.
- The issue is separable from the current root problem.
- The issue is non-blocking for completing the current task.
- The issue can be owned by another session without carrying the current session's whole context.

Do not use this skill for:
- Current blockers.
- Same-root-cause work.
- Speculative notes without evidence.
- Style TODOs.
- Already-approved execution work.
- Anything that should mutate SSOT, specs, contracts, task queues, manual requests, or human requests.

## Workflow

1. Confirm the report is user-requested or user-approved.
2. Recheck that the issue is separate, non-blocking, and separately ownable.
3. Check existing `.runtime/discovered-issues/` files for a similar title, slug, symptom, or affected component. Also check legacy `reports/discovered-issues/` files if that directory exists, but do not create new reports there.
4. If a likely duplicate exists in `.runtime/discovered-issues/`, append a `## New Observation - <YYYY-MM-DD>` note to the existing report instead of creating a duplicate. If a duplicate exists only in the legacy path, migrate or merge the continued handoff into `.runtime/discovered-issues/` instead of appending to `reports/discovered-issues/`.
5. If no duplicate exists, create `.runtime/discovered-issues/<YYYY-MM-DD>-<slug>.md` using the local repo date.
6. If the filename already exists for a non-duplicate, append `-2`, `-3`, and so on.
7. Use `references/report_template.md` and fill every section.

Use `date +%F` from the repo environment for the local date unless the user provided a more specific discovery date.

Duplicate append notes must preserve handoff quality. Each `New Observation` note must include:
- Source Context for the new observation.
- Observed Symptom and Evidence.
- Evidence Quality using the same `strong`, `medium`, or `weak` rubric.
- First Actions or Revalidation Criteria specific to the new observation.
- Privacy And Redaction confirmation when the new evidence came from logs, traces, customer/user context, private environments, or other sensitive surfaces.

## Source Context Requirements

Every report must include:
- Source type: `autopilot-root`, `managed-repo`, or `unknown`.
- Repo id when known.
- Worktree or path.
- Branch when known.
- SHA or ref when known.
- Discovery context: the task, command, test, log, code path, or review activity that surfaced the issue.

## Evidence Rules

Classify evidence quality as exactly one of:
- `strong`: direct reproduction, test, log, trace, or code reference evidence.
- `medium`: partial reproduction or code-path evidence with unresolved gaps.
- `weak`: plausible hypothesis with limited confirmation.

`First Actions` must start with revalidating or reproducing the issue and checking whether the observation is stale.

`Provisional Hypothesis` must be explicitly non-authoritative.

`Privacy And Redaction` must state that secrets, credentials, customer data, and private raw logs are forbidden in the report. Summarize sensitive evidence instead.

## Boundary

This skill records observations only. It must not enqueue work, create approval requests, edit SSOT, edit specs or contracts, update progress truth, or imply that the issue is accepted as current truth.
