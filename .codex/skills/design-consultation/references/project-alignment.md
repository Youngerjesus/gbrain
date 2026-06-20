# Project Alignment

Use these repo-specific constraints when proposing or updating the design system.

## Product Direction

- The product is a data-first Saju analysis system, not a mystical or ornate fortune-telling site.
- The UI should feel trustworthy, modern, and analytically legible.
- The user should feel they are reading a serious risk-analysis product, not decorative spirituality content.

## Existing Direction to Preserve

- `AGENTS.md` explicitly requires a modern, trust-heavy UX.
- `specs/008-toss-design-system/spec.md` establishes a Toss-like baseline:
  - clean global design tokens
  - mobile-first readability
  - card-based report surfaces
  - clear typography hierarchy
  - subtle micro-interactions
  - high performance and accessibility targets

Treat that baseline as the default unless the user requests a new strategic direction.

## Practical Design Priorities

Bias the system toward:

- high signal-to-noise ratio
- calm surfaces and clear information hierarchy
- strong mobile readability
- restrained but intentional motion
- semantic tokens that can support future theming

Avoid:

- mystical ornament as the primary visual language
- generic AI landing-page tropes
- flashy gradients that reduce trust
- novelty that hurts report scanning or decision-making

## Document Role

`DESIGN.md` is the project-level visual SSOT.

It should be detailed enough that an implementer can:

- define tokens
- style components consistently
- review visual diffs against a written standard
- reject UI changes that drift from the approved system
