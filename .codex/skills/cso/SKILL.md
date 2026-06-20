---
name: cso
description: Run a security posture audit and produce a findings report when the user asks for a security audit, threat model, pentest-style review, OWASP review, supply-chain audit, infra audit, or CSO review.
---

# CSO

Use this skill as a read-only Chief Security Officer audit. Do not make code changes. Produce concrete findings with severity, confidence, exploit scenario, evidence, and remediation.

## Modes

- No flags: full daily audit, confidence gate 8/10.
- `--comprehensive`: full audit, confidence gate 2/10 with tentative findings clearly labeled.
- `--infra`: phases 0-6 and 12-14.
- `--code`: phases 0-1, 7, 9-11, and 12-14.
- `--skills`: phases 0, 8, and 12-14.
- `--supply-chain`: phases 0, 3, and 12-14.
- `--owasp`: phases 0, 9, and 12-14.
- `--scope <domain>`: focused audit.
- `--diff`: constrain scanning to current branch changes where possible.

Scope flags are mutually exclusive. `--diff` can combine with any scope flag and `--comprehensive`.

## Workflow

1. Detect stack and framework from structured project files such as package manifests, lockfiles, build files, Docker/IaC, CI config, and app entrypoints. Use `rg` for discovery, but promote findings only through source reads, parsers, schemas, or deterministic checks.
2. Build an architecture mental model: components, trust boundaries, data flows, auth boundaries, external integrations, and invariants.
3. Create an attack-surface census covering public endpoints, authenticated/admin endpoints, machine APIs, uploads, webhooks, jobs, sockets, CI/CD, containers, IaC, deploy targets, and secret handling.
4. Read `references/audit-phases.md` before executing scope-dependent phases 2-11. That file is the source of truth for the detailed audit phase list.
5. Filter and actively verify all candidate findings before reporting.
6. Write a Security Posture Report. Save it under a task-appropriate local path such as `.gstack/security-reports/<date>-cso.md` when the repo permits generated reports.

## Finding Gate

Every promoted finding must include:

- severity and confidence score
- verified or unverified status
- category and phase
- file:line evidence
- quoted motivating source line(s)
- concrete exploit scenario
- remediation plan

If you cannot quote the motivating source line(s), force confidence to 4-5 and keep it out of the main critical findings section.

## False Positive Discipline

Discard low-impact or non-security items unless there is a concrete exploit path. Do not report generic missing hardening, log spoofing, documentation-only issues, non-security input validation, or test fixture patterns as vulnerabilities. CI/CD, skill supply-chain, LLM cost-amplification, and production container findings may still be valid when the detailed phase rules support them.

## Codex Adjustments

- Use `rg` for candidate discovery.
- Use available subagents only when they exist; otherwise self-verify by re-reading the code skeptically.
- Do not use live external exploit attempts or test real credentials.
- If web search is unavailable, proceed local-only and note the gap.
