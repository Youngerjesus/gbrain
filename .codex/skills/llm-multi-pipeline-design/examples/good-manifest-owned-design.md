# Good Manifest-Owned Design

The product manifest owns `chapter_id`, `section_id`, source identity, and chapter order. The LLM receives only content slots and local style constraints. The system assembles final artifacts by copying product-owned identity from the manifest and inserting generated prose into known slots.

The invariant is `product_identity_preserved`. The deterministic validator compares generated output against the active manifest and rejects any generated identity that differs from product-owned state. Conflict precedence is `manifest_over_generated`.

The LLM judge rubric is `not_required` for identity preservation because the deterministic validator owns that decision. If a downstream prose-quality judge is added, it must use at most three orthogonal first-principles criteria and exclude identity, ordering, schema, and artifact-existence checks.

Repair may regenerate content for the same manifest slot, but it cannot mutate identity fields. Checkpoint replay requires product input digest, manifest version, schema version, provider/model identity, and artifact digest.
