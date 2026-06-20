# Debug Report Template

Use this template while investigating and before proposing a fix.

```text
Symptom:
- What failed, where, and how it surfaced

Expected:
- What should have happened instead

Reproduced:
- Yes / No / Partial
- Exact reproduction method or why reproduction is currently unreliable

Evidence:
- Error messages, logs, traces, diffs, screenshots, or working-vs-broken comparisons

Tier:
- trivial / standard / complex / architecture-brake
- Why this tier fits the observed evidence

Current hypothesis:
- One explicit candidate root cause
- Use `none/not ready` when reproduction is unavailable, evidence is insufficient, or the issue currently passes

Hypothesis space:
- For complex debugging only: competing candidates and what evidence would eliminate each one

Delegated evidence status:
- not used / usable / unavailable / partial / stale / contradictory / unsourced / out-of-lens
- Context-loader or subagent reports are evidence inputs only, not root-cause authority

Debug packet status:
- not used / missing / usable / partial / stale / contradictory / unsourced / out-of-lens / cleaned up
- `debugging/<debug-id>/` is optional ignored local-only working context, not root-cause authority
- Path-only citation to a debug packet is not evidence; parent revalidation must summarize current claim, evidence, command or artifact, result, and files

Root Cause Claim Gate:
- not ready / passed / blocked with reason / architecture-brake
- Check direct vs deeper cause, masked downstream failure, path coverage, architecture-brake, and evidence quality

Next step:
- One experiment, check, or verification action

Fix gate:
- Blocked until root cause is evidenced
- Open only after the Root Cause Claim Gate passes

Likely category:
- implementation defect
- spec mismatch
- test defect
- environment or config drift
- observability gap
- data issue
- external dependency issue
- unknown
```

## Notes

- Do not list multiple hypotheses unless the evidence truly leaves you with more than one viable explanation.
- If more than one remains viable, keep the list short and say what evidence would eliminate each one.
- `Likely category` is a working classification, not a final verdict.
- A subagent report, stale local artifact, conversation memory, or string-presence hint cannot open the fix gate by itself.
- If the issue is connected to a spec in this repository, include the relevant spec or contract reference in `Evidence`.
