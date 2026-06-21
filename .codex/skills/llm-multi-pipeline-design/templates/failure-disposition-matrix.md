# Failure Disposition Matrix

## Required output fields

- Failure:
- Category: `prevention`, `detection`, `repair-retry-replan`, `checkpoint-replay`, or `escalation`
- Preventive design rule:
- Detection signal:
- Recovery behavior:
- Escalation condition:
- Evidence required:

## Reject when

- Recovery is mentioned but not classified.
- A provider hang, quota failure, or timeout is treated as local success.
- A repair path can hide a semantic invariant failure.
