---
name: design-consultation
description: Design consultation workflow for establishing or updating this project's visual system. Use when the user asks for a design system, brand guidelines, visual direction, or to create/update `DESIGN.md`. This skill inspects the current repo first, aligns with the existing Toss-like product direction, and produces a project-level design source of truth instead of generic UI advice.
---

# Design Consultation

Use this skill when the user wants a project-wide visual system, not a one-off component tweak.

## What This Skill Produces

- A coherent design direction for the product
- A project-level `DESIGN.md` proposal or update
- Clear rationale for typography, color, spacing, layout, motion, and component principles

## Operating Rules

1. Inspect local truth first.
   Read `AGENTS.md`, existing `DESIGN.md` if present, and the current design-related specs or docs before proposing a direction.
2. Preserve the established visual language when it already exists.
   Do not invent a new direction if the repo already has a strong design baseline unless the user asks for a reset.
3. Optimize for product trust, clarity, and modernity.
   This repository already points toward a clean, analytic, Toss-like experience. Treat that as the baseline unless the user explicitly wants a different direction.
4. Stay project-level.
   The default output is a project design SSOT, not a feature-local mock redesign.
5. Keep the workflow conversational.
   Propose a complete system, explain why it works, then refine based on user feedback.

## Workflow

### 1. Ground in the Repository

Inspect the following before proposing anything:

- `AGENTS.md`
- `DESIGN.md` if it exists
- `specs/008-toss-design-system/spec.md` or the closest active design-system spec
- relevant long-lived design docs under `docs/`
- current frontend token or theme files if the task requires implementation follow-through

Then read [project-alignment.md](./references/project-alignment.md).

### 2. Decide the Mode

Choose one mode explicitly:

- **Create**: no `DESIGN.md` exists and the project needs a first design SSOT
- **Update**: `DESIGN.md` exists and needs refinement or extension
- **Review**: the user wants critique of an existing visual system before changing it

If the repo already contains a stable visual direction, default to **Update** or **Review**, not **Create**.

### 3. Research Only When It Helps

If the user wants competitive or current visual references, browse current sources and use those findings.
Otherwise, rely on repo context plus design judgment.

When researching:

- prioritize directly relevant product references
- extract concrete observations, not vague trend language
- identify what is table stakes versus what would differentiate this product

### 4. Propose a Complete System

Present a coherent package that covers:

- aesthetic direction
- typography
- color system
- spacing and density
- layout and composition
- motion rules
- component principles for app, dashboard, form, and report surfaces

Always include:

- what is safe and expected in this category
- where the product should deliberately differentiate
- why each major choice supports user trust and comprehension

### 5. Produce `DESIGN.md`

Use the template and required sections in [design-md-template.md](./references/design-md-template.md).

If the user only wants planning, provide a complete proposed `DESIGN.md` in the response.
If the user wants execution, write or update `DESIGN.md` at the repo root.
If the result is meant to feed `project_manager/design_loop.py`, also save a consultation markdown artifact under `project_manager/contexts/design-consultation/...` so the loop can consume it directly.

### 6. Cross-Check Before Finishing

Before finalizing:

- confirm the system does not conflict with `AGENTS.md`
- confirm it does not silently contradict the Toss-like design-system spec unless the user requested a change
- confirm the recommendations are specific enough for implementation
- flag any unresolved tradeoffs plainly

## Constraints and Anti-Patterns

- Do not import gstack-specific telemetry, session, or binary workflows into this repo.
- Do not mutate `AGENTS.md` or add routing rules as part of this skill.
- Do not produce generic startup-brand output detached from the actual product.
- Do not recommend overused default font stacks as the primary answer when a stronger option is available.
- Do not treat `DESIGN.md` as marketing copy. It is an implementation-facing source of truth.

## References

- [project-alignment.md](./references/project-alignment.md)
- [consultation-flow.md](./references/consultation-flow.md)
- [design-md-template.md](./references/design-md-template.md)
