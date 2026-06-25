**Source reviewed**
requirements/123-example/requirements.md

**Readiness summary**
The draft is close to handoff-ready, but implementation could still satisfy it with a narrower evidence bar. The highest risk is that completion can be claimed without proving source-derived obligations were preserved.

**Highest-risk gaps**
- Evidence level could be lowered from durable verification to a prose-only review.

**Prioritized good questions**
1. Lens: intent-contraction
   Priority: blocker
   Question: Does completion require executable verification evidence, or can a written review satisfy the requirement?
   Why it matters: An implementer could replace the requested evidence level with a weaker documentation-only artifact.
   Answer impact: verification proof and implementation handoff

2. Lens: verification
   Priority: verification gap
   Question: Which deterministic command proves the accepted behavior and which artifact should be cited as evidence?
   Why it matters: The requirement could pass review without a repeatable completion signal.
   Answer impact: verification strategy and evidence references

**Skipped-lens rationale**
- failure: No separate failure question passed the criticality gate after the evidence-level blocker.

**Recommended next step**
Answer the blocker question, update the requirement through requirement-clarifier if needed, then proceed to planning.
