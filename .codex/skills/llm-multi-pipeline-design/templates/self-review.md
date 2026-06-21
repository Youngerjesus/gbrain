# Self Review

## Required output fields

- State ownership complete: `yes` or `no`
- Invariants mapped to validators: `yes` or `no`
- Judge rubric limited and orthogonal, or not required: `yes` or `no`
- Failure dispositions complete: `yes` or `no`
- Repair/retry/replan preserves authoritative state: `yes` or `no`
- Checkpoint/replay lineage complete: `yes` or `no`
- Deterministic assembly boundary complete: `yes` or `no`
- Keyword-only compliance rejected: `yes` or `no`
- Handoff evidence ready: `yes` or `no`

## Reject when

- Any item is `no`.
- The review cites vocabulary without concrete fields, validators, and recovery behavior.
- An LLM judge rubric has more than three criteria, overlapping criteria, or criteria that belong in deterministic validators.
