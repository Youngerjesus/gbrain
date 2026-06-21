---
name: llm-multi-pipeline-design
description: Design LLM multi-phase pipelines where structured outputs, semantic state ownership, validators, LLM judge rubrics, repair/retry/replan, checkpoint/replay, and handoff evidence are one contract.
---

# LLM Multi-Pipeline Design

Use this skill when designing a new LLM multi-phase pipeline, reviewer/repair loop, agent workflow, or structured-output pipeline where model output crosses phase, state, checkpoint, or handoff boundaries.

Do not use this skill for a single prompt with no persisted state, no generated artifact handoff, and no repair/retry/replay path.

## Contract

A design is ready only when it separates structured-output shape from semantic state consistency, names authoritative state owners, maps invariants to deterministic validators, limits any LLM judge rubric to orthogonal first-principles criteria, classifies failures, defines recovery and checkpoint lineage, and completes a self-review before handoff.

The design must reject keyword-only compliance. Terms such as `manifest-first`, `deterministic validator`, `checkpoint/replay`, or `repair loop` are not evidence unless connected to concrete state fields, invariants, validators, and recovery behavior.

When an LLM judge is used, design the rubric from first principles: define the smallest independent judgments needed to decide the phase outcome, keep at most three criteria, make each criterion orthogonal to the others, and exclude anything a deterministic validator already checks.

## Workflow

1. Define the product-owned state and generated-state boundary with [state ownership](templates/state-ownership-map.md).
2. Map every semantic invariant to a validator with [invariant validators](templates/invariant-validator-matrix.md).
3. If an LLM judge is needed, define its rubric with [judge rubric](templates/judge-rubric.md).
4. Classify failures using [failure disposition](templates/failure-disposition-matrix.md): prevention, detection, repair/retry/replan, checkpoint/replay, or escalation.
5. Decide what model context may see with [context projection](templates/context-projection.md).
6. Define replay safety with [checkpoint replay](templates/checkpoint-replay-rule.md).
7. Define deterministic assembly boundaries with [deterministic assembly](templates/deterministic-assembly-boundary.md).
8. Complete [self review](templates/self-review.md) before handing the design to implementation.
9. Compare the design against the [good manifest-owned example](examples/good-manifest-owned-design.md).
10. Check the structured fixtures: [good](fixtures/good-manifest-owned-design.yml), [keyword-only](fixtures/bad-keyword-only.yml), [LLM-owned identity](fixtures/bad-llm-owned-identity.yml), [missing precedence](fixtures/bad-missing-precedence.yml), and [stale repair checkpoint](fixtures/bad-stale-repair-checkpoint.yml).
11. Preserve the non-executed optimizer handoff in [skillopt/handoff.yml](skillopt/handoff.yml), then use [skillopt/readiness.yml](skillopt/readiness.yml) to find the [benchmark](skillopt/benchmark.yml) and [heldout](skillopt/heldout.yml) readiness assets. Requirement 003 owns benchmark rows, held-out seeds, provider regression material, and any optimizer execution readiness.

## Output Format

Return a design package with:

- State ownership map.
- Invariant and validator matrix.
- Judge rubric, or `not_required` with reason.
- Failure disposition matrix.
- Context projection rule.
- Checkpoint/replay rule.
- Deterministic assembly boundary.
- Self-review result.
- Verification and handoff notes.

## Anti-Patterns

- Treating schema-valid JSON as semantic state consistency.
- Using more than three LLM judge criteria, overlapping criteria, or criteria that duplicate deterministic validators.
- Letting the LLM own product identifiers, ordering, manifest identity, or source identity.
- Repairing a local field while preserving stale nested metadata.
- Replaying a checkpoint without input, manifest, schema, model/provider, or artifact lineage.
- Claiming optimizer readiness, benchmark improvement, or provider success before the dedicated readiness slice owns that evidence.
- Using keyword presence as acceptance evidence.
