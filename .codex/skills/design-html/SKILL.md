---
name: design-html
description: Finalize a design into a standalone HTML reference artifact for this project. Use when the user asks to turn a mockup, approved design, or page brief into HTML, finalize a design direction, or build a high-fidelity reference page after planning or design consultation. This skill always uses the vendored Pretext runtime and saves artifacts inside the repository under `contexts/`.
---

# Design HTML

Use this skill when the user wants a page made real as a standalone HTML artifact, not just another prose design note.

## What This Skill Produces

- A standalone `finalized.html` reference artifact
- A companion `finalized.json` metadata file
- A page that reflects the current project design direction closely enough to guide future frontend implementation

## Operating Rules

1. Inspect repo truth first.
   Read `AGENTS.md`, `DESIGN.md` if present, the Toss-like design-system spec/design docs, and relevant frontend style/token files before generating anything.
2. Treat the HTML as a reference artifact.
   The default output is not a production Next.js page. It is a high-fidelity design artifact that can be reviewed, refined, and translated into `frontend/src/...` later.
3. Always use Pretext.
   This skill must use the vendored runtime at `./vendor/pretext.js` for text measurement and relayout behavior.
4. Save artifacts inside the repo.
   Store generated pages under `project_manager/contexts/design-html/...`, not in home-directory skill state.
   When an orchestration engine provides a specific output directory inside `project_manager/contexts/design-loop/...`, use that directory instead of inventing a parallel location.
5. Stay aligned with the existing product direction.
   This repository already targets a modern, trustworthy, Toss-like analysis experience. Do not drift into generic startup landing-page output.

## Workflow

### 1. Ground in the Current Design Context

Inspect these in order:

- `AGENTS.md`
- `DESIGN.md` if it exists
- `specs/008-toss-design-system/spec.md`
- `specs/008-toss-design-system/design.md`
- relevant frontend token/theme files such as `frontend/tailwind.config.ts`, `frontend/src/styles/globals.css`, and layout/font setup

Then read [project-alignment.md](./references/project-alignment.md).

### 2. Choose the Input Mode

Use one of these modes explicitly:

- **Approved Mockup**: the user provides a mockup, screenshot, or other visual source
- **Plan-Driven**: the user wants a page from design notes, `DESIGN.md`, or design/spec docs
- **Freeform**: the user describes the page directly
- **Evolve**: an existing artifact in `project_manager/contexts/design-html/...` should be refined

### 3. Build an Implementation Spec

Before writing HTML, summarize the intended output:

- page purpose and audience
- key sections and hierarchy
- colors, fonts, spacing, radius, and motion cues
- component inventory
- which parts must feel exact versus flexible

If `DESIGN.md` exists, its system-level tokens override ad hoc choices.

### 4. Route to the Right Pretext Pattern

Read [pretext-patterns.md](./references/pretext-patterns.md) and choose the simplest correct pattern:

- basic height/layout for standard marketing or app sections
- segmented line-walking when tight-fit or editorial behavior is needed
- obstacle-aware or full line rendering only when the design genuinely needs it

State the chosen pattern in the artifact metadata.

### 5. Generate the Artifact

Use the storage contract in [artifact-contract.md](./references/artifact-contract.md).

Requirements for `finalized.html`:

- standalone file
- semantic HTML
- CSS custom properties for tokens
- real content, never lorem ipsum
- responsive behavior
- accessible states and focus handling
- Pretext runtime sourced from `./vendor/pretext.js`

If the user wants iteration, edit the same artifact surgically instead of regenerating from scratch.

### 6. Verify Before Finishing

Check that:

- the artifact matches the supplied design context closely
- mobile and desktop layouts both hold up
- text does not overflow or collapse awkwardly
- the output still aligns with repo design direction

## Constraints and Anti-Patterns

- Do not depend on gstack telemetry, session files, or custom gstack binaries.
- Do not save artifacts outside the repo by default.
- Do not default to generic SaaS hero patterns unless the user explicitly asked for that shape.
- Do not silently convert the artifact into production React code.
- Do not skip Pretext because the page looks simple.

## References

- [project-alignment.md](./references/project-alignment.md)
- [artifact-contract.md](./references/artifact-contract.md)
- [pretext-patterns.md](./references/pretext-patterns.md)
