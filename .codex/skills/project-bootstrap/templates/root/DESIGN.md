# DESIGN

Use this file only when the project has a meaningful UI, brand, or user-facing experience.

## Design Goals

- Product Tone: `[e.g. calm, precise, trustworthy, energetic]`
- Visual Priority: `[e.g. clarity over decoration, speed over density]`
- Trust Model: `[How the interface should earn trust: e.g. legibility, restraint, traceability, speed]`
- Non-Goals:
  - `[visual style or brand direction to avoid]`
  - `[interaction pattern or density level to avoid]`

## Brand And Experience Rules

- The interface should feel intentional, not generic.
- Hierarchy must be visible at a glance.
- Primary actions must be obvious without shouting.
- Empty, loading, and failure states must look owned, not forgotten.

## Design Contract And Foundation Reuse

- Treat this file as the product visual contract when the project has a meaningful UI, brand, or user-facing experience.
- Accepted foundations must be represented by reusable implementation paths, not only prose or screenshots. Use shared tokens, components, template helpers, fixtures, or verification checks when later surfaces are expected to rely on the same foundation.
- User-facing screens should reuse the accepted app shell, navigation treatment, typography scale, spacing system, layout primitives, cards/lists, form controls, CTA hierarchy, empty/loading/error states, and responsive rules unless a requirement records a product-level reason to diverge.
- Do not create route-local shells, page-local visual systems, or duplicate CSS foundations when a shared foundation exists.
- When a new UI surface needs a pattern not covered here, update this file first or record why the surface is exempt before implementation.
- A foundation is complete only when downstream work can reuse it without copying internals, and visual QA can detect bypasses or drift across related screens.

## Typography System

- Primary Font: `[font family]`
- Secondary Font or Mono: `[optional]`
- Heading Principle: `[e.g. bold, compact, high-contrast hierarchy]`
- Body Principle: `[e.g. quiet, readable, low-friction scanability]`
- Rules:
  - Use a limited type scale.
  - Keep body text readable at default viewport sizes.
  - Distinguish primary, secondary, and tertiary text semantically.

## Color And Semantic Tokens

- Background: `[token or example]`
- Surface: `[token or example]`
- Primary: `[token or example]`
- Success: `[token or example]`
- Warning: `[token or example]`
- Danger: `[token or example]`
- Text Primary: `[token or example]`
- Text Secondary: `[token or example]`
- Rules:
  - Colors must carry semantic meaning.
  - Avoid decorative accent sprawl.
  - Contrast must remain acceptable in core flows.

## Layout And Spacing

- Use a small set of spacing steps.
- Define max content width for reading-heavy surfaces.
- Cards, panels, and sections should have a predictable containment grammar.
- Dense views and narrative views may use different spacing, but each must stay internally consistent.

## Component Principles

- Buttons:
  - Primary buttons must be visually distinct from secondary and destructive actions.
- Forms:
  - Labels, helper text, and validation states must be explicit.
- Cards and Panels:
  - Surfaces should communicate grouping, not just decoration.
- Data Views:
  - Tables, lists, and charts should optimize for comparison and scanning.
- Navigation:
  - Current location and next available action should be obvious.

## Motion Rules

- Motion must explain state changes, not decorate emptiness.
- Prefer short, purposeful transitions.
- Use staged reveal only when it improves comprehension.
- Avoid animation that slows frequent tasks or obscures system state.

## UX Writing

- Voice: `[e.g. direct, calm, warm, technical]`
- Sentence Style: `[e.g. active, concise, conversational]`
- Button Style: `[e.g. verb-first, outcome-oriented]`
- Rules:
  - Prefer direct and specific language.
  - Avoid jargon unless the target user genuinely expects it.
  - Error messages should explain what happened and what to do next.

## Accessibility And Responsiveness

- Define mobile, tablet, and desktop expectations for the main flows.
- Keyboard and screen-reader basics must work for interactive surfaces.
- Visual hierarchy must survive reduced width and zoom.
- Do not hide critical meaning in color alone.

## Anti-Patterns

- visual noise without information value
- unclear action hierarchy
- placeholder-heavy interfaces shipped as final design
- unowned design drift across screens and components
- page-local shells or CSS foundations that bypass an accepted shared foundation
- foundation work that exists only as prose, screenshots, or isolated artifacts with no reusable implementation path
- motion without state meaning
- card stacks with no information grammar
