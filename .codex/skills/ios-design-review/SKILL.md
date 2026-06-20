---
name: ios-design-review
description: Review a real iOS app's visual design through the gstack iOS QA daemon when the user asks for iPhone design QA, iOS visual audit, HIG review, accessibility/design scoring, or UI polish feedback.
---

# iOS Design Review

Use this for designer-eye QA on a real iOS device. It is read-only by default and uses the running `ios-qa` daemon. If no daemon is running, bootstrap the same observe-only path as `ios-qa`.

## Rubric

Score each major screen 0-10 across:

1. Typography hierarchy
2. Spacing rhythm
3. Color hierarchy and contrast
4. Touch targets
5. Loading, empty, and error states
6. Accessibility
7. Animation discipline
8. iOS idiom alignment
9. Information density
10. AI-slop check

For each score, explain what would move it to 10.

## Workflow

1. Acquire an observe-capability session.
2. Use the user's screen list, or discover major screens from the accessibility tree.
3. For each screen, capture screenshot and elements.
4. Apply the rubric and record concrete findings.
5. Produce a Markdown report with screenshots, per-screen scores, and highest-leverage fixes.
6. For scores below 7, ask the user before making any design changes; this skill itself is review-only unless they explicitly ask for implementation.

## Failure Handling

- If screenshots are black or blank, ask the user to confirm the app state.
- If expected screens cannot be reached, report which states are missing and what interaction or fixture is needed.
- If tailnet capability is insufficient, ask the owner to mint observe capability.
