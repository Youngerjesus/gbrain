---
name: policy-review
description: Explanation-only CAO policy review. Use inside the CAO review pipeline after deterministic policy evaluation to explain why a candidate is allowed, deferred, blocked, or escalated.
---

# Policy Review

This skill explains a deterministic CAO policy gate result. It does not decide policy compliance and must not override the gate.

## Trigger

Use this skill only after CAO code has evaluated `policies/autonomy-policy.yml` for a reviewed candidate.

## Inputs

- Candidate context
- Review chain outputs
- Deterministic `PolicyGateResult`
- `policies/autonomy-policy.yml`
- CAO root and project manager contracts

## Workflow

1. Read the deterministic policy result as authoritative.
2. Explain which policy clauses allowed, deferred, blocked, or escalated the candidate.
3. Translate violations and escalations into human-visible notes.
4. If the gate allowed the candidate, explain the remaining assumptions without adding new approval conditions.

## Output Rules

Return only the structured output requested by the runtime schema.

The explanation must make clear:

- Policy verdict
- Whether human action is required
- Which violations or escalations matter
- Why the candidate may or may not proceed to spec handoff

## Constraints

- Do not modify files.
- Do not reinterpret the policy result.
- Do not approve a candidate that deterministic policy blocked.
- Do not invent policy clauses not present in the provided policy.
