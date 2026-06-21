# Context Projection

## Required output fields

- Model-visible fields:
- System-owned fields withheld from the model:
- Derived fields allowed in prompts:
- Fields forbidden from model mutation:
- Projection refresh rule:
- Stale-context rejection rule:

## Reject when

- The prompt gives the model authority over product identity.
- The projection can include stale nested metadata without a validator.
- The context projection cannot be reconstructed deterministically.
