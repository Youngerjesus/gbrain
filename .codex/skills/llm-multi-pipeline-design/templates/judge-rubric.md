# Judge Rubric

Use this template only when an LLM judge is needed for semantic evaluation that deterministic validators cannot decide.

## Required output fields

- Judge purpose:
- Phase outcome controlled:
- Criteria count: integer from `1` to `3`
- Criteria:
  - Criterion id:
  - First-principles question:
  - Distinct from:
  - Input evidence:
  - Allowed scores:
  - Passing threshold:
  - Failure disposition:
- Deterministic validator exclusions:
- Tie-break or precedence rule:

## Rubric rules

- Start from the phase decision, then derive the smallest set of independent questions needed to make that decision.
- Keep at most three criteria.
- Make criteria orthogonal: failing one criterion must not imply another criterion fails for the same reason.
- Do not include criteria for schema validity, required fields, IDs, ordering, artifact existence, or other checks owned by deterministic validators.
- Prefer atomic pass/fail or small ordinal scores with explicit thresholds over broad quality scores.

## Reject when

- The rubric has more than three criteria.
- Two criteria measure the same semantic property with different wording.
- A criterion can be replaced by a deterministic validator.
- A criterion is a vague quality word without input evidence and a threshold.
