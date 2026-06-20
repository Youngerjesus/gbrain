---
name: reset-rebuild
description: Exception-path workflow for cases where modifying existing code is clearly more expensive and riskier than deleting a bounded implementation and rebuilding it from extracted contracts.
---

# Reset Rebuild

This skill is an exception path for bounded implementation areas where incremental modification is more expensive and riskier than rebuilding from a verified behavioral boundary.

Reset-rebuild does not mean throwing away behavior. It means extracting valid contracts from the old implementation, proving those contracts through tests, specs, or docs, rebuilding a clean replacement, and deleting old code only after verification.

## Trigger

Use this skill when either condition is true:

- The user explicitly asks for reset/rebuild, delete-and-reimplement, rewrite-from-boundary, rebuild-from-contracts, or similar.
- Exploration shows `cost_to_modify_existing >>> cost_to_delete_and_rebuild`.

Do not use this skill for:

- Simple bugfixes
- Small refactors
- Cleanup-only changes
- Ordinary implementation review
- Bounded implementation work where `tdd-workflow` can safely drive the change

If evidence for reset-rebuild is weak, stop this workflow and use `tdd-workflow` or `implementation-brake` instead.

## Ground The State

Before proposing deletion or replacement, read only the relevant sources needed to understand the existing boundary:

- Specs and contracts
- Current tests
- User-facing docs and durable memory when relevant
- Current implementation and call sites
- `git diff`

Then decide whether reset-rebuild is justified or whether a smaller TDD change is enough.

## Justify The Reset

Require concrete evidence before continuing. Valid evidence includes:

- Repeated patch failure
- Cross-layer coupling that prevents local reasoning
- Legacy fallback buildup
- Spec drift between intended behavior and implementation structure
- Untestable structure
- File, class, or function boundary collapse

Name the evidence in the working notes or final handoff. If the evidence is weak, do not continue with reset-rebuild.

## Define The Boundary

Classify every relevant part of the current implementation as one of:

- `preserve`: keep as-is and verify compatibility
- `rebuild`: replace with a clean implementation
- `delete`: remove after proof that no supported behavior depends on it
- `adapter-only`: keep temporarily to bridge old callers to the replacement

If the boundary crosses 2 or more subsystems, call an architect reviewer before implementation.

If the boundary touches auth, payment, privacy, data deletion, migration, or observability approval paths, require explicit contracts and reviewer scrutiny before deleting anything.

## Extract Before Delete

When mutation is allowed, create a transition artifact at:

```text
contexts/reset-rebuild/<topic>-<YYYYMMDD>/extraction.md
```

Capture each preserved contract with:

- Source reference
- Business or validation rule
- Oracle priority
- Target test, spec, or doc
- Verification command

Use this oracle priority order:

```text
spec/contracts/docs SSOT > intended user behavior > current tests > observed legacy behavior
```

The extraction file is transition evidence only. It is not durable SSOT. Durable rules must be promoted into tests, specs, contracts, docs, or memory before the reset-rebuild task is complete.

## Rebuild

Convert extracted contracts into tests or contract checks before writing replacement production code.

Use `tdd-workflow` for the replacement:

1. Write the smallest failing test or contract check for one extracted behavior.
2. Confirm it fails for the expected reason.
3. Implement the minimum replacement code.
4. Re-run the targeted test.
5. Repeat until the extracted contract set is implemented.

Keep the old code in place until the replacement proves the extracted contracts.

## Delete Only After Proof

Delete old code only when all of the following are true:

- Extracted contracts are implemented.
- Targeted tests pass.
- Relevant broader verification passes.
- Import/reference scan confirms old paths are unused.
- Architect or reviewer objections are resolved where applicable.

Do not delete first and reconstruct behavior from memory.

## Ship Gate

After rebuild and deletion, run `implementation-brake`.

If `implementation-brake` finds must-fix issues, return to `tdd-workflow` repair before closing the task.

## Validation Checklist

For skill behavior, verify:

- Explicit reset/rebuild requests load this skill.
- High modification cost can justify this skill.
- Simple bugfixes and small refactors redirect away from this skill.
- Deletion is blocked when extracted contracts lack target tests, specs, or docs.
- Boundaries crossing 2 or more subsystems require architect review.
- Protected areas require explicit contracts and reviewer scrutiny.
- `implementation-brake` is required after rebuild and deletion.

For repo fit, verify:

- `SKILL.md` has valid YAML frontmatter.
- No unnecessary README, scripts, or reference files are added in v1.
- The extraction artifact path is documented as `contexts/reset-rebuild/<topic>-<YYYYMMDD>/extraction.md`.
