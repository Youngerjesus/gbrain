# Checkpoint Replay Rule

## Required output fields

- Checkpoint scope:
- Product input lineage:
- Manifest or state-machine version:
- Schema version:
- Provider/model identity where relevant:
- Artifact version or digest:
- Replay eligibility rule:
- Replay rejection rule:

## Reject when

- A checkpoint can replay across different product inputs.
- A checkpoint omits manifest, schema, model/provider, or artifact lineage when those fields affect correctness.
- Replay success can bypass semantic validators.
