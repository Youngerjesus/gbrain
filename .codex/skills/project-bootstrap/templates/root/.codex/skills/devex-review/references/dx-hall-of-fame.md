# DX Hall Of Fame Reference

Read only the section for the current review pass. These examples are calibration references, not a substitute for current competitor research when a live market claim matters.

## TTHW Benchmarks

| Tier | Time | Adoption Impact |
|------|------|-----------------|
| Champion | under 2 min | Best-in-class first impression |
| Competitive | 2-5 min | Strong baseline |
| Needs Work | 5-10 min | Meaningful drop-off risk |
| Red Flag | over 10 min | High abandonment risk |

## Pass 1: Getting Started

Gold standards:

- Stripe: short charge example, docs that can pre-fill test keys, and in-doc API exploration.
- Vercel: push or CLI deploy to a live preview with HTTPS.
- Clerk: a few framework components create a complete auth flow.
- Supabase: database schema quickly exposes usable APIs and realtime behavior.
- Firebase: a few lines demonstrate realtime sync.

Anti-patterns:

- value hidden behind email verification, credit card, demo call, or sales contact
- several equivalent quickstarts with no recommended path
- API keys buried in settings
- code examples that cannot be run as shown
- docs and dashboard requiring constant context switching

## Pass 2: API/CLI/SDK Design

Gold standards:

- prefixed IDs that make object types self-documenting
- idempotency keys for mutation retries
- API version pinning or per-request version overrides
- CLI output that adapts to terminal vs pipe
- progressive disclosure from simple production-shaped calls to advanced options
- owned source-code components or templates where version drift would otherwise hurt

Anti-patterns:

- chatty APIs requiring many calls for one user-visible action
- inconsistent naming grammar
- `200 OK` responses that hide errors in the body
- endpoints or commands with many unrelated modes
- APIs that require reading pages of docs before the first correct call

## Pass 3: Error Messages And Debugging

Three useful tiers:

- Elm-like: conversational explanation, exact location, suggested fix.
- Rust-like: error code, primary and secondary labels, concrete help.
- Stripe-like: structured error with type, code, message, parameter, and docs URL.

Formula: what happened, why, how to fix, where to learn more, and actual values involved.

Anti-pattern:

- the actionable suggestion is buried after a long stack trace or internal framework noise

## Pass 4: Documentation And Learning

Gold standards:

- docs with navigation, explanation, and live code/reference visible together
- language or framework switcher that persists coherently
- API references connected to runnable examples
- docs treated as part of feature completion
- beginner path and expert reference both present

Useful calibration:

- developer adoption often fails when docs are missing, stale, or examples are too abstract

## Pass 5: Upgrade And Migration Path

Gold standards:

- one-command codemods for common major upgrades
- every breaking change has a migration guide
- deprecations include replacement instructions
- versioning policy is predictable
- automated transforms are small, composable, and testable

Anti-patterns:

- changelog only describes internal implementation
- breaking changes discovered at runtime
- migration docs assume too much context

## Pass 6: Developer Environment And Tooling

Gold standards:

- fast install and test feedback
- editor support and accurate types
- CI examples and non-interactive mode
- local dry-run, fixtures, mocks, or sample apps
- cross-platform setup that calls out real prerequisites

DX principle:

- speed is part of usability; slow setup and slow iteration compound into abandonment

## Pass 7: Community And Ecosystem

Gold standards:

- clear license and contribution model
- public support path with visible response quality
- examples for real integrations
- transparent pricing, quota, or hosted limitations
- extension/plugin story when ecosystem growth matters

DX principle:

- developers adopt tools partly on trust that help and ecosystem depth will exist later

## Pass 8: DX Measurement

Framework lenses:

- SPACE: satisfaction, performance, activity, communication, efficiency
- DevEx: feedback loops, cognitive load, flow state
- cognition, affect, conation: can they understand, feel confident, and act?

Gold standards:

- track TTHW and onboarding drop-off
- collect docs search failures or common error paths without sensitive payloads
- run periodic friction audits
- compare plan promises against live dogfooding

## Codex Skill And Agent Tool Checklist

Use when reviewing Codex skills, MCP servers, or AI developer tools.

- trigger description is precise and reusable
- `SKILL.md` is lean, with one-hop references only
- no host-specific telemetry, update checks, or routing preambles
- interactive choices have a plain chat fallback
- deterministic scripts handle repeated mechanical work
- prompt output contracts and validators share field names and enums
- evidence is code-owned or structured where state decisions depend on it
- verification includes deterministic checks, plus live smoke evidence when model or external boundaries change
