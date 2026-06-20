# Audit Checklist

Use this checklist to structure findings. Keep the review visual, specific, and tied to user outcomes.

## 1. First Impression

- What does the page communicate in the first 3 seconds?
- Is the primary action obvious?
- Does the page feel trustworthy or improvised?
- Does the screen read like an app workspace or like stacked promotional cards?

## 2. Hierarchy and Composition

- Is there one clear focal point per screen?
- Do headings, metrics, and actions compete with each other?
- Is the eye drawn to the right thing first on mobile and desktop?
- Are surfaces and separators doing real organizational work?

## 3. Typography

- Are font choices aligned with the project baseline?
- Is body text comfortably readable on mobile?
- Does heading scale step cleanly, or jump arbitrarily?
- Are number-heavy sections using stable numeric presentation?
- Does copy density help comprehension, or bury the signal?

## 4. Spacing and Layout

- Do gaps and padding follow a recognizable system?
- Are cards, panels, and sections aligned to a shared rhythm?
- Is the layout calm, or is everything boxed and equally loud?
- On app screens, are cards used only where the card is the interaction?

## 5. Color and Surface Discipline

- Does the UI use a restrained, trustworthy palette?
- Are semantic states clear without becoming noisy?
- Are accents reserved for meaning, not sprayed everywhere?
- Do neutral surfaces feel consistent across pages?

## 6. Interaction States

- Are hover, focus, active, disabled, loading, and error states clearly designed?
- Does tap/click feedback feel responsive?
- Do transitions help orientation, or just add motion for its own sake?
- Are touch targets large enough on mobile?

## 7. Responsive Behavior

- Does the mobile layout feel intentionally designed, not just vertically stacked?
- Is there any horizontal overflow or cramped text?
- Does the hierarchy survive at narrow widths?
- Are sticky elements, sheets, and bottom actions behaving safely on mobile?

## 8. AI-Slop and Template Smell

Flag these fast:

- purple or blue-purple gradient defaults
- decorative icon circles in repeated feature grids
- centered-everything layout with no hierarchy
- identical card rhythm everywhere
- ornamental blobs, waves, and filler shapes
- generic "premium SaaS" polish that weakens product trust

## 9. Four-Axis Score

End each rendered audit with `0-10` scores and one-sentence rationale for:

- `design_quality`: Do color, typography, layout, imagery, and interaction treatment form one trustworthy product identity?
- `originality`: Does the UI avoid template defaults, generic AI slop, decorative filler, and arbitrary component spam?
- `craft`: Are spacing, alignment, contrast, wrapping, density, responsive adaptation, and visual states executed cleanly?
- `functionality`: Can users understand the state, identify the primary action, complete the flow, and recover from loading/error/empty/disabled states?

The scores do not replace findings. A single high-severity trust, comprehension, or task-completion issue can still require fixes even when the average score is high.

## Finding Format

For each finding, record:

- `Finding`: concise title
- `Severity`: `high`, `medium`, or `polish`
- `Observation`: what is visibly wrong
- `Impact`: what the user feels or misunderstands
- `Likely source`: file, component, or style layer to inspect next
