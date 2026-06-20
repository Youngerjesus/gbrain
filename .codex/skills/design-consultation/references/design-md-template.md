# `DESIGN.md` Template

Use this structure when creating or updating the project-level design SSOT.

```markdown
# Design System

## Product Context
- What this product is
- Who it serves
- Which user trust problem the interface solves
- Which primary surfaces the system optimizes for

## Design Principles
- 3 to 5 concise principles that guide tradeoffs

## Aesthetic Direction
- Direction name
- Mood and rationale
- What the system should not become

## Typography
- Display font and role
- Body font and role
- UI/label font and role
- Data/mono font and role when needed
- Type scale with concrete sizes and weights

## Color System
- Core neutrals
- Primary accent
- Secondary/supporting accent if needed
- Semantic colors
- Usage rules and contrast expectations

## Spacing and Shape
- Base spacing unit
- Density target
- Radius scale
- Border and elevation rules

## Layout
- Grid and breakpoint logic
- Max content widths
- Surface composition rules
- Mobile-first layout constraints

## Motion
- Motion philosophy
- Duration bands
- Easing rules
- Where motion is encouraged and where it should be avoided

## Component Principles
- Buttons
- Inputs and forms
- Cards and panels
- Navigation
- Data displays
- Report sections and drill-down surfaces

## Voice in UI
- Tone of labels, helper text, errors, and CTA copy

## Implementation Notes
- Token naming expectations
- Theming expectations
- Accessibility and performance constraints

## Decision Log
| Date | Decision | Rationale |
|------|----------|-----------|
```

## Writing Rules

- Prefer exact values over adjectives when possible.
- Keep every section implementation-facing.
- If the design direction inherits from the existing Toss-like baseline, say so explicitly.
- If the user intentionally departs from that baseline, document the deviation and rationale.
