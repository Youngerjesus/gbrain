# Agents working on GBrain

This is your install + operating protocol. Claude Code reads `./CLAUDE.md` automatically.
Everyone else (Codex, Cursor, OpenClaw, Aider, Continue, or an LLM fetching via URL):
start here.

## Install (5 min)

1. Install gbrain via Bun (the canonical path):
   ```bash
   curl -fsSL https://bun.sh/install | bash
   export PATH="$HOME/.bun/bin:$PATH"
   bun install -g github:garrytan/gbrain
   ```
   If `bun install -g` aborts or `gbrain doctor` reports `schema_version: 0`,
   the CLI prints a recovery hint pointing at [#218](https://github.com/garrytan/gbrain/issues/218).
   Run `gbrain apply-migrations --yes` to recover, or fall back to the
   deterministic install: `git clone https://github.com/garrytan/gbrain.git ~/gbrain && cd ~/gbrain && bun install && bun link`.
2. Init the brain: `gbrain init` (defaults to PGLite, zero-config). For 1000+ files or
   multi-machine sync, init suggests Postgres + pgvector via Supabase.
3. **STOP — ask the user about search mode.** `gbrain init` auto-applied a
   default but printed a 9-cell cost matrix (mode × downstream model)
   preceded by `[AGENT]` markers. You MUST relay the matrix to the operator
   and confirm their choice before continuing. Cost spread between corners
   is 25x — silent acceptance is the wrong default. See
   [`./INSTALL_FOR_AGENTS.md`](./INSTALL_FOR_AGENTS.md) Step 3.5 for the
   exact ask-the-user protocol. Same banner fires on `gbrain post-upgrade`
   for existing users (search modes were added in v0.32.3).
4. Read [`./INSTALL_FOR_AGENTS.md`](./INSTALL_FOR_AGENTS.md) for the full 9-step flow
   (API keys, identity, cron, verification).

## Read this order

1. `./AGENTS.md` (this file) — install + operating protocol.
2. [`./CLAUDE.md`](./CLAUDE.md) — orientation + resolver: architecture, cross-cutting
   invariants, the reference map, inline ship rules. It routes to on-demand detail docs:
   [`./docs/architecture/KEY_FILES.md`](./docs/architecture/KEY_FILES.md) (per-file index —
   read a file's entry before editing it), [`./docs/TESTING.md`](./docs/TESTING.md) (test
   tiers + isolation lint + E2E lifecycle), and
   [`./docs/architecture/thin-client.md`](./docs/architecture/thin-client.md) (remote-MCP seam).
3. [`./docs/architecture/brains-and-sources.md`](./docs/architecture/brains-and-sources.md)
   — the two-axis mental model (brain = which DB, source = which repo in the DB). Every
   query routes on both axes. Read before writing anything that touches brain ops.
4. [`./skills/conventions/brain-routing.md`](./skills/conventions/brain-routing.md) —
   agent-facing decision table: when to switch brain, when to switch source, how
   cross-brain federation works (latent-space only; the agent decides).
5. [`./skills/RESOLVER.md`](./skills/RESOLVER.md) — skill dispatcher. Read before any task.

## Human role and product direction

The human user acts as the agent work environment designer. When the user points
out an agent mistake, treat it as a signal to discuss the surrounding contracts,
checks, docs, or workflow so future agents are less likely to repeat it.

GBrain's product direction lives in `./CLAUDE.md`, especially the North Star and
cross-cutting invariants. Do not replace that with generic scaffold language.
When durable product direction, architecture boundaries, verification commands,
or operating policy change, update this file and the linked GBrain docs together.

## Trust boundary (critical)

GBrain distinguishes **trusted local CLI callers** (`OperationContext.remote = false`,
set by `src/cli.ts`) from **untrusted agent-facing callers** (`remote = true`, set by
`src/mcp/server.ts`). Security-sensitive operations like `file_upload` tighten filesystem
confinement when `remote = true` and default to strict behavior when unset. If you are
writing or reviewing an operation, consult `src/core/operations.ts` for the contract.

## Codex operating rules

- Plan non-trivial work before implementation, including verification steps and
  repair assumptions when the change can affect stable contracts.
- Read the direct task source of truth first, then inspect the affected
  implementation and tests, then expand to durable docs only when they reduce
  ambiguity.
- Keep durable documentation aligned when user-facing behavior, compatibility
  guarantees, architecture boundaries, or verification commands change.
- Do not silently downgrade the user's requested behavior, execution boundary,
  artifact class, or evidence level. If the requested contract cannot be met
  with this repo's current capabilities, stop and state the gap before changing
  scope.
- Prefer root-cause fixes, deterministic behavior, deterministic tests, and
  narrow changes over temporary workarounds or broad compatibility branches.
- Preserve compatibility-sensitive behavior unless the active spec, contract,
  accepted requirement, or user request explicitly changes it.
- Make errors explicit at product boundaries. Add dependencies only when the
  task needs them and this repo's policy allows them.
- Keep real secrets, machine-specific env files, automation runtime state, logs,
  and local paths out of committed artifacts. Track only placeholders such as
  `.env.example` or setup docs.

## Context loading before implementation

Use `.codex/skills/context-loading/SKILL.md` before `.codex/skills/tdd-workflow/SKILL.md`
when the user asks for delegated context, or when the task requires inspecting
three or more files, crosses module/component/package/service/policy/evidence
boundaries, has an unclear implementation path or test strategy, or touches
safety, persistence/state, external side effects, or a verification contract.

A context-loading report is exploratory context only, not acceptance evidence.
It should name inspected files or directories, core findings, candidate change
files, and a test strategy.

## Engineering rules

- Keep changes scoped to the active spec and contract.
- Keep hand-written implementation files small and cohesive, but do not split
  files merely to satisfy a line count. Split only along real ownership
  boundaries that improve stability, testability, reviewability, or delivery
  speed.
- Treat very large hand-written files as a maintenance signal. Before adding
  behavior there, consider whether a focused refactor would make the change
  safer.
- Prefer modules with small public interfaces, cohesive internals, one-way
  dependencies, and nearby test boundaries.
- Avoid shallow wrappers, pass-through modules, role-free file splits, circular
  dependencies, and scattered ownership.
- Add abstractions only when they reduce real complexity, remove meaningful
  duplication, or clearly match an established local pattern.

## Anti coding patterns

- Do not use substring, regex, or string-presence checks as authoritative proof
  for semantic acceptance, safety, evidence correctness, state diagnosis, or
  completion. String scans may be useful hints; promote them to decisions only
  through structured sources, parsers, schemas, typed fields, or deterministic
  validators.
- Treat LLM prompt output contracts and deterministic validator input contracts
  as one typed interface. Keep field names, enums, required/optional rules,
  reference formats, and retry/error semantics synchronized across prompts,
  parsers, validators, and fixtures.
- For AI/model/Codex invocation boundaries, prompt/schema contracts,
  multi-agent handoffs, repair/evaluator/generator loops, or live output
  parsing, require deterministic verification plus the relevant live smoke
  evidence when the active contract calls for it. If live proof cannot run,
  report the gap.
- Do not add or preserve fallback or legacy compatibility paths unless the
  active spec/contract requires them, the owner and removal condition are clear,
  and regression coverage proves the fallback does not hide failures.
- Do not complete a reusable foundation as documentation-only intent when later
  slices are expected to rely on it. A foundation needs an explicit code path,
  shared module, template helper, schema, validator, fixture, or verification
  gate that downstream work can actually use.

## Execution Source Selection

- If the task provides or selects `goal-requirements/<id>/sequence.md`, use the
  goal-requirements path. Start with the first unchecked requirement and read
  the requirement's `requirements.md`, `research.md`, `technical-design.md`,
  optional `architecture.md`, `progress.md`, `decisions.md`, `evidence.md`, any
  accepted `plans/<plan-id>/plan.md` and `secondary_plan.md`, plus current git
  status/diff.
- If a broad initiative has no accepted sequence yet, use
  `.codex/skills/goal-requirement-orchestrator/SKILL.md` to create the
  sequence and first requirement state before implementation.
- For each goal-requirements slice, evaluate the conditional hard gates in this order: `requirement-clarifier`, `research`, `technical-design`, `plan-design-review`, `plan-ux-review`, `plan-devex-review`, `plan-eng-review`, `scenario-brake`, `secondary-plan`, then after implementation and applicable live evidence `ux-review` and `devex-review`.
  `plan-design-review` is required for UI-bearing work before
  `plan-eng-review`; `plan-ux-review` is required for user-facing experience
  work before `plan-eng-review`; `plan-devex-review` is required for
  developer-facing experience work before `plan-eng-review`.
- After planning is accepted, run context loading and TDD implementation as
  required. For UI-bearing work, run `visual-qa-hardening` with the
  `visual-qa-reviewer` companion after browser screenshot verification and
  before implementation-brake, and also use the `reference-fidelity-reviewer`
  companion for reference-driven visual work.
- For MVP, beta, launch, or production-bound goal sequences, reserve a final
  `production-readiness` requirement slice and run `production-readiness` as
  the sequence-level launch gate before marking the goal sequence complete.
- Record `not_required` skips with reasons where the gate workflow requires
  them. Artifact existence alone is insufficient; progress, required artifact
  paths, evidence, decisions, unresolved items, and approval state must agree.
- Treat scheduler result artifacts as phase status reports only. They are not
  substitutes for requirement evidence, product acceptance evidence, or
  verification artifacts.
- Before editing, identify the affected product contract: public API, CLI
  behavior, persisted data, UI behavior, external integration, tests, docs, or
  migration state.
- If the selected source of truth and repo reality conflict, stop and report
  the conflict instead of weakening the contract.
- When no task-provided spec or goal requirement exists, use `CLAUDE.md`, the
  reference docs, and the repo's tests as the fallback contract and keep the
  change narrow.

## Test and verification principles

- Test additions should follow `.codex/skills/tdd-workflow/SKILL.md`: prove
  behavior or executable acceptance criteria with the narrowest honest evidence,
  and prefer observed red/green for behavior changes and bugfixes.
- Avoid artificial duplicate tests for already-covered or non-behavioral
  changes. Match verification type to the problem.
- `bun run verify` is the fast local baseline for GBrain's guard scripts.
  `bun test` runs the unit suite. `bun run ci:local` is the full pre-ship gate
  described below.
- Slow checks, external-service checks, Docker E2E, and checks that need secrets
  belong in explicit commands such as `bun run test:e2e`, `bun run test:slow`,
  `bun run ci:local`, or a documented `scripts/verify*` entrypoint. They must
  fail clearly when required tools or env vars are missing.
- Do not mark implementation work complete without concrete verification
  evidence from the selected contract and the relevant GBrain gate.

## Common tasks

- **Configure:** [`docs/ENGINES.md`](./docs/ENGINES.md),
  [`docs/guides/live-sync.md`](./docs/guides/live-sync.md),
  [`docs/mcp/DEPLOY.md`](./docs/mcp/DEPLOY.md).
- **Debug:** [`docs/GBRAIN_VERIFY.md`](./docs/GBRAIN_VERIFY.md),
  [`docs/guides/minions-fix.md`](./docs/guides/minions-fix.md), `gbrain doctor --fix`.
- **Migrate / upgrade:** `gbrain upgrade` (binary self-update + schema migrations + post-upgrade prompts),
  [`docs/UPGRADING_DOWNSTREAM_AGENTS.md`](./docs/UPGRADING_DOWNSTREAM_AGENTS.md),
  [`skills/migrations/`](./skills/migrations/), `gbrain apply-migrations --yes` (manual schema-only).
- **Eval retrieval changes:** capture is off by default. To benchmark a
  retrieval change against real captured queries, set
  `GBRAIN_CONTRIBUTOR_MODE=1`, then `gbrain eval export --since 7d > base.ndjson`
  and `gbrain eval replay --against base.ndjson`. For public benchmark
  coverage (LongMemEval, ground-truth scoring), `gbrain eval longmemeval
  <dataset.jsonl>` (v0.28.8) runs against an isolated in-memory PGLite
  per question — your `~/.gbrain` is never opened. Full guide:
  [`docs/eval-bench.md`](./docs/eval-bench.md).
- **Drive the brain to a target health score (v0.36.4.0):** the one-command
  loop. `gbrain doctor --remediation-plan --json` previews what would be
  fixed; `gbrain doctor --remediate --yes --target-score 90 --max-usd 5`
  walks a dependency-ordered plan (sync before extract, embed after
  consolidate), re-checking score between every step, refusing to spend
  past the cost cap. Empty brains (no entity pages) or unconfigured embedding
  keys hit a `max_reachable_score` ceiling and bail with what's missing.
  Three phase handlers (synthesize / patterns / consolidate) are
  PROTECTED — only trusted local callers can submit them; MCP cannot.
  Reference: [`docs/architecture/topologies.md`](./docs/architecture/topologies.md)
  and the CHANGELOG entry for v0.36.4.0.
- **Track a founder/company over time (v0.35.7):** when an entity has
  typed metric claims in its `## Facts` fence (`metric: mrr`, `value: 50000`,
  `unit: USD`, `period: monthly` columns), run
  `gbrain eval trajectory <entity-slug>` for the chronological history
  with regressions auto-flagged, or `gbrain founder scorecard <entity-slug>`
  for a four-signal JSON rollup (claim_accuracy / consistency /
  growth_trajectory / red_flags). MCP op `find_trajectory` exposes the
  same data — read scope, visibility-filtered for remote callers. **v0.40.2.0:**
  `gbrain think` now uses this substrate automatically on temporal /
  knowledge_update intent (default ON; flip `think.trajectory_enabled=false`
  to opt out). Migration v82 added `facts.event_type` so non-metric event
  rows (`meeting`, `job_change`, `location_change`) ride through the same
  pipeline; pass `kind: 'event'` or `'all'` to `find_trajectory` to query
  them.
- **Everything else:** [`./llms.txt`](./llms.txt) is the full documentation map.
  [`./llms-full.txt`](./llms-full.txt) is the same map with core docs inlined for
  single-fetch ingestion.

## Before shipping

Easiest path: `bun run ci:local` runs the full CI gate inside Docker (gitleaks,
guards + typecheck, then 4-shard parallel unit + E2E against four pgvector
containers plus a transaction-mode PgBouncer; unit phase keeps `DATABASE_URL`
unset) and tears down. Use `bun run ci:local:diff` for the
diff-aware subset during fast iteration on a focused branch. Requires Docker
(Docker Desktop / OrbStack / Colima) and `gitleaks` (`brew install gitleaks`).

Manual path: `bun test` plus the E2E lifecycle described in `./CLAUDE.md` (spin
up the test Postgres container, run `bun run test:e2e`, tear it down).

Ship via the `/ship` skill, not by hand. The full release + contributor process
(CHANGELOG voice, version-locations sync, PR conventions, community-PR-wave) lives in
[`./docs/RELEASING.md`](./docs/RELEASING.md); read it before shipping.

## Document map

- `AGENTS.md`: install and cross-agent operating protocol.
- `CLAUDE.md`: always-loaded GBrain orientation, North Star, invariants,
  reference map, and release rules.
- `docs/architecture/KEY_FILES.md`: per-file index; read a file's entry before
  editing that file.
- `docs/TESTING.md`: test tiers, isolation lint, and E2E lifecycle.
- `docs/architecture/brains-and-sources.md`: brain/source topology and routing
  model.
- `skills/RESOLVER.md`: GBrain skill dispatcher.
- `.codex/skills/`: Codex skill workflows used for planning, implementation,
  review, and closeout.
- `goal-requirements/<id>/sequence.md`: multi-slice goal execution order and
  gate contract when selected by the task.
- `requirements/<requirement-id>/`: requirement-slice source of truth,
  progress, decisions, evidence, research, and design artifacts.
- `plans/<plan-id>/`: accepted primary and secondary implementation plans.

## Privacy

Never commit real names of people, companies, or funds into public artifacts. See the
Privacy rule in `./CLAUDE.md`. GBrain pages reference real contacts; public docs must
use generic placeholders (`alice-example`, `acme-example`, `fund-a`).

## AGENTS.md update policy

Update this file when durable repo-level product direction, engineering rules,
architecture boundaries, verification commands, env policy, document locations,
or dependency policy change. Do not put temporary task notes, secrets, local
machine paths, scheduler state, generated logs, or runtime output in this file.

## Forks

If you are a fork, regenerate `llms.txt` + `llms-full.txt` with your own URL base before
publishing: `LLMS_REPO_BASE=https://raw.githubusercontent.com/your-org/your-fork/main bun run build:llms`.
