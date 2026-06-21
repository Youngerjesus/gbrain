# State Ownership Map

## Required output fields

- Pipeline phase:
- Ownership mode: `manifest-first` or `explicit-state-machine`
- Product-owned fields:
- Generated fields:
- Authoritative owner for each identity field:
- Forbidden LLM-owned identity fields:
- Precedence rule when generated state conflicts with product state:
- Conflict resolution behavior:
- Validator coverage:

## Reject when

- Any product-owned identifier, order, source identity, or manifest identity is owned by the LLM.
- The design omits conflict precedence.
- The design has validators but does not name which state fields they protect.
