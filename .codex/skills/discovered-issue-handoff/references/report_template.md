# Title

`<short descriptive issue title>`

## Source Context

- Source type: `<autopilot-root | managed-repo | unknown>`
- Repo id: `<id if known, otherwise unknown>`
- Worktree/path: `<path or unknown>`
- Branch: `<branch if known, otherwise unknown>`
- SHA/ref: `<sha/ref if known, otherwise unknown>`
- Discovery context: `<current task, command, test, log, code path, review, or investigation that surfaced the issue>`

## Why This Is Separate

`<Explain why this is separable from the current root problem, non-blocking for current completion, and separately ownable by another session.>`

## Observed Symptom

`<What was observed. Include exact commands, tests, paths, line references, or log summaries when available.>`

## Expected Behavior

`<What should happen instead.>`

## Evidence

- `<Evidence item 1>`
- `<Evidence item 2>`

## Evidence Quality

`<strong | medium | weak>`

Rubric:
- `strong`: direct reproduction, test, log, trace, or code reference evidence.
- `medium`: partial reproduction or code-path evidence with unresolved gaps.
- `weak`: plausible hypothesis with limited confirmation.

## Likely Scope

`<Known or suspected affected component, workflow, command, test layer, repo boundary, or user path.>`

## Non-Goals

- `<What this handoff is not trying to solve or decide.>`
- `<State any areas that should not be mutated without separate approval.>`

## First Actions

1. Revalidate or reproduce the issue from a fresh checkout/session.
2. Check whether the observation is stale by comparing branch, SHA/ref, config, generated state, and recent changes.
3. `<Next smallest evidence-gathering action.>`

## Provisional Hypothesis

`<Non-authoritative hypothesis only. This is not accepted root cause or current truth.>`

## Revalidation Criteria

- `<What evidence would confirm the issue is still present.>`
- `<What evidence would show it is resolved, stale, or invalid.>`

## Risks And Unknowns

- `<Risk or unknown 1>`
- `<Risk or unknown 2>`

## Privacy And Redaction

Do not include secrets, credentials, customer data, or private raw logs. Summarize sensitive evidence and redact values that could identify users, systems, tokens, webhooks, or private environments.

## Next Session Starter

`<A concise prompt a future Codex session can use to begin revalidation and investigation.>`
