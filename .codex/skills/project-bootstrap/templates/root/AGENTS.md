# AGENTS (<project-name>)

Primary audience: coding agents and maintainers working inside this product repo.

## Product Direction

- Core value: `[Describe the primary value this project must deliver.]`
- Current milestone or invariant: `[Describe the current target state.]`
- Non-goals:
  - `[What this project must not become.]`
  - `[What complexity or maintenance burden must be rejected.]`

## Critical Operating Rules

- Plan non-trivial work before implementation, including verification steps and rollback or repair assumptions when the change can affect stable contracts.
- Do not mark work complete without concrete verification evidence from `scripts/verify` and any contract-required checks.
- Prefer root-cause fixes over temporary workarounds.
- Read the direct task SSOT first, then inspect the affected implementation and tests, then expand to durable docs or history only when they reduce ambiguity.
- Keep durable documentation aligned when user-facing behavior, compatibility guarantees, architecture boundaries, or verification commands change.
- For UI-bearing work, read `DESIGN.md` before planning or implementation when it exists. Treat it as the product visual contract for app shell, navigation, layout, typography, spacing, component primitives, state treatment, and reference-fidelity boundaries.
- Prefer subtraction and narrow changes over additive compatibility logic unless stability, migration, or an explicit contract requires the extra path.

## Context Loading Before Implementation

- Use `context-loading` before `tdd-workflow` when the user asks for delegated context, or when the task requires inspecting three or more files, crosses module/component/package/service/policy/evidence/repo boundaries, has an unclear implementation path or test strategy, or touches safety, persistence/state, external side effects, or a verification contract.
- If those triggers appear after a narrow first read, stop broad parent-side exploration and invoke `context-loader` through `context-loading`.
- A usable context-loading report must include inspected files or directories, core findings, change candidate files, and test strategy. It is exploratory context only, not acceptance evidence or completion evidence.

## Engineering Rules

- Keep changes scoped to the active spec and contract.
- Keep hand-written implementation files small and cohesive. As a default pressure, avoid letting a single source file grow beyond roughly 220 lines.
- When a file exceeds that size, split it along a real ownership boundary or document why keeping it together is simpler and safer.
- Treat any hand-written code file at or above roughly 1000 lines as a strong maintenance signal. Before adding more behavior there, prioritize refactoring toward smaller ownership units when that would improve stability, testability, reviewability, or delivery speed.
- Do not split files merely to satisfy a line count. Prefer modules that reflect stable product or data boundaries, with one-way dependencies and focused tests.
- Preserve compatibility-sensitive behavior unless the contract changes it.
- Prefer deterministic behavior and deterministic tests.
- Make errors explicit at product boundaries.
- Add dependencies only when the task needs them and the repo policy allows them.
- Keep documentation aligned when durable assumptions change.

## Module Design For AI Workability

- Do not treat file count or line count as the quality target. A good structure has small public interfaces, cohesive internal implementation, clear ownership, and nearby test boundaries: deep modules.
- Avoid shallow wrappers, pass-through modules, role-free file splits, circular dependencies, and scattered dependencies because they make it harder for AI agents to identify edit locations, test boundaries, and change impact.
- Refactor only when the change improves boundaries, dependency direction, testability, or local reasoning; do not split files just to make them smaller.
- Add an abstraction only when it reduces real complexity, removes meaningful duplication, or clearly matches an established local pattern.

## Anti Coding Patterns

- Do not use substring, regex, or string-presence checks to decide semantic acceptance, boundary, safety, evidence correctness, or state diagnosis.
- Because string scans can create false positives and false negatives, do not use them as evidence that affects state decisions, user-facing reports, blocking, deferral, escalation, success, or failure.
- String scans may be used only as non-authoritative human-readable hints or debugging candidate discovery. To promote a string-scan result into state, use an authoritative structured source, parser, schema, typed field, or deterministic validator, with regression cases for allowed and forbidden counterexamples.
- Treat LLM prompt output contracts and deterministic validator input contracts as one typed interface. Keep field names, enums, required/optional rules, reference formats, and retry/error semantics synchronized across prompts, parsers, validators, and fixtures.
- Prefer preventive design and root-cause fixes that make forbidden failures unable to occur over after-the-fact detection, cleanup, or repair logic.
- Do not make the system less flexible merely to make evidence stricter. Keep strictness at the boundary or evidence contract that needs it, and support project-specific differences through explicit policy, structured input, or escalation path.
- Treat full-pipeline live runs as final acceptance evidence, not as the default debugging tool for finding regressions. Before expensive AI/live boundaries, persist product-owned checkpoints or intermediate artifacts that allow retry/resume without repeating completed model calls; when a failure is suspected, isolate it with focused deterministic checks, fixtures, unit/integration tests, logs, or smaller smoke runs before spending full live-run budget.
- Changes to an AI/model/Codex invocation boundary, prompt/schema contract, multi-agent handoff, repair/evaluator/generator loop, or live output parsing require deterministic verification plus the relevant `scripts/verify_live` target or request-local live smoke evidence. If live proof cannot run, report the verification gap.
- Do not copy scheduler, control-plane, runtime, or automation ids into product evidence identity fields, product tests, or acceptance artifacts. Product evidence must be identified by product-owned inputs and outputs such as scenario ids, repo-relative fixtures, report digests, artifact hashes, or explicit CLI arguments.
- Do not add or preserve fallback or legacy compatibility paths unless the active spec/contract requires them, the owner and removal condition are clear, and regression coverage proves the fallback does not hide failures.
- Do not complete a visual foundation, design system, app shell, layout primitive, prompt/schema contract, adapter boundary, or validation contract as documentation-only intent when later slices are expected to rely on it.
- If a requirement creates a reusable foundation, later implementations must depend on it through an explicit code path, shared module, template helper, schema, validator, fixture, or verification gate.
- Avoid creating route-local shells, route-local visual systems, duplicate CSS foundations, duplicate prompt envelopes, duplicate validators, or parallel adapter contracts when a prior accepted foundation exists.
- A reusable foundation is not complete unless at least one downstream consumer can reuse it without copying its internals, and verification can detect when later work bypasses it.
- Exceptions are allowed only when the later surface has a documented product reason to diverge, records the divergence in the relevant design or requirement artifact, and still passes the relevant cross-surface consistency check.

## Execution Source Selection

- If the task provides or selects `specs/<feature>/spec.md` and `specs/<feature>/contracts.md`, use the specs-based SDD path. Treat `contracts.md` as the completion contract: every listed behavior, non-goal, required check, and acceptance artifact must be satisfied or explicitly blocked.
- If the task provides or selects `goal-requirements/<id>/sequence.md`, use the goal-requirements path. Start with the first unchecked requirement and read `requirements/<requirement-id>/requirements.md`, `requirements/<requirement-id>/research.md`, `requirements/<requirement-id>/technical-design.md`, `requirements/<requirement-id>/architecture.md`, `requirements/<requirement-id>/progress.md`, `requirements/<requirement-id>/decisions.md`, `requirements/<requirement-id>/evidence.md`, any accepted `plans/<plan-id>/plan.md` and `plans/<plan-id>/secondary_plan.md`, plus current git status/diff.
- If a broad initiative has no accepted sequence yet, use `goal-requirement-orchestrator` to create `goal-requirements/<id>/sequence.md`, `goal-requirements/<id>/progress.md`, and the first requirement's requirement/progress/decisions/evidence state; later requirement documents remain deferred until their slice starts.
- A ready requirement document is not permission to implement directly. For each goal-requirements slice, evaluate the conditional hard gates in this order: `requirement-clarifier`, `research`, `technical-design`, `plan-design-review`, `plan-ux-review`, `plan-devex-review`, `plan-eng-review`, `scenario-brake`, `secondary-plan`, then after implementation and applicable live evidence `ux-review` and `devex-review`; `research` writes `requirements/<requirement-id>/research.md` when required, `technical-design` writes `requirements/<requirement-id>/technical-design.md` when required, optional architecture design writes `requirements/<requirement-id>/architecture.md` only when needed, `plan-design-review` is required before `plan-eng-review` for UI-bearing slices, `plan-ux-review` is required before `plan-eng-review` for user-facing experience slices, and `plan-devex-review` is required before `plan-eng-review` for developer-facing experience slices.
- For goal-requirements research/design gates, record `not_required` skips with reasons. Artifact existence alone is insufficient: progress, artifact path or chat-only review outcome, evidence, decisions, unresolved-item classification, and approval state must agree before `plan-eng-review`.
- After planning is accepted, run `context-loading` before `tdd-workflow` when the context-loading triggers apply; for UI-bearing work, run `visual-qa-hardening` with the `visual-qa-reviewer` companion after browser screenshot verification and before `implementation-brake`, and also use the `reference-fidelity-reviewer` companion for reference-driven visual work; for user-facing experience work, run `ux-review` after runnable/browser evidence exists and before `implementation-brake`; for developer-facing experience work, run `devex-review` after runnable docs/API/CLI/SDK evidence exists and before `implementation-brake`; after implementation and verification, run `implementation-brake`, then `closeout` only after `[SHIP]`. UI-bearing work must have passed `plan-design-review` before planning is accepted; user-facing experience work must have passed `plan-ux-review` before planning is accepted; developer-facing experience work must have passed `plan-devex-review` before planning is accepted; non-triggered slices must record the relevant review gates as `not_required` with the reason.
- For MVP, beta, launch, or production-bound goal sequences, reserve a final production readiness requirement slice and run `production-readiness` as the sequence-level launch gate before marking the goal sequence complete.
- Treat scheduler result artifacts, including run-local `result.md`/`status.txt` and any legacy `result_<phase>.md` files, as scheduler-owned phase status reports. They express phase outcome, next owner, and readiness only; they are not substitutes for `contracts.md`, requirement evidence, product acceptance evidence, or verification artifacts.
- Before editing, identify the affected product contract: public API, CLI behavior, persisted data, UI behavior, external integration, tests, docs, or migration state.
- Preserve existing public behavior unless the active spec, contract, or accepted requirement explicitly changes it.
- If the selected source of truth and repo reality conflict, stop and report the conflict instead of weakening the contract.
- Implement in a tight loop: read the selected contract, write or update focused tests, change code/docs, run targeted verification, then run `scripts/verify` once as the final repo baseline before completion.
- Completion is blocked until the selected contract, `scripts/verify`, and any required `scripts/verify*` checks pass.
- When no task-provided spec or goal requirement exists, use the repo's documented product contracts and tests as the fallback contract and keep the change narrow.

## Architecture Boundary

- Define the current boundary map only when this repo has meaningful modules or layers to protect.
- Keep the map repo-specific; do not impose a fixed architecture vocabulary across all repos.
- Boundaries must be unidirectional: higher-level or more volatile modules may depend on lower-level or more stable modules, but lower-level modules must not import back upward.
- Cross-boundary calls should go through the owning boundary's public interface, not through private implementation details.
- Cycles are architecture violations.
- Once boundaries are declared, enforce them mechanically through `scripts/verify`.
- If no meaningful boundaries exist yet, say so and document only the current structure.

## Verification Scripts

- `scripts/verify` is the canonical baseline verification entrypoint for this repo.
- If this repo does not have `scripts/verify`, create it before the first implementation is marked complete. The initial script may be minimal, but it must run the repo's stable local baseline checks and fail clearly on missing tools or failed checks.
- `scripts/verify` must work from any caller cwd, including absolute-path invocation from outside the repo.
- `scripts/verify` must be local, secret-free, and expected to finish in roughly one minute or less.
- If ordinary `scripts/verify` runtime exceeds roughly one minute, prioritize refactoring the verification path before expanding it: parallelize deterministic checks, remove redundant work, improve test isolation, or move slow non-baseline checks into separate `scripts/verify*` entrypoints.
- `scripts/verify` should run all stable baseline checks required before ordinary task completion.
- When the stable baseline changes, update `scripts/verify`, this section, and any spec/contract templates or task contracts that reference required verification.
- Slow checks, external-service checks, real-service smoke checks, and checks expected to exceed roughly one minute belong in separate scripts named `scripts/verify*`, such as `scripts/verify_full`, `scripts/verify_e2e`, or `scripts/verify_external`.
- Verification scripts must fail clearly when required tools or environment variables are missing. They must not silently skip required checks.
- A failing `scripts/verify*` check required by the active contract blocks completion just like a failing baseline.

## Environment And Secrets

- Keep real secrets and machine-specific env files uncommitted.
- Track only placeholder examples such as `.env.example` or setup docs.
- `scripts/verify` must not require secrets.
- Secret-dependent or external checks must live in separate `scripts/verify*` scripts with explicit env requirements.
- If this repo needs setup whenever a fresh task worktree is created, document it and implement it in `scripts/init_worktree.sh`.
- `scripts/init_worktree.sh`, when present, must be idempotent, accept the task worktree path as its first argument, and avoid writing external automation runtime state into this repo.
- Do not copy external automation runtime state, logs, generated task state, or local machine paths into this repo.

## Document Map

- `README.md`: project entrypoint and onboarding.
- `DESIGN.md`: product visual contract and UI foundation source of truth when the repo has a meaningful UI, brand, or user-facing experience.
- `docs/project_overview.md`: durable product direction and product constraints.
- `docs/tech_stack.md`: chosen runtime, tooling, and delivery constraints.
- `docs/history_archives/history.md`: durable project history and milestone notes.
- `work_queue/progress.md`: current product progress summary.
- `specs/<feature>/spec.md`: specs-based SDD implementation requirements when selected by the task.
- `specs/<feature>/contracts.md`: specs-based SDD acceptance contract and required verification when selected by the task.
- `goal-requirements/<id>/sequence.md`: multi-slice goal execution order and gate contract when selected by the task.
- `goal-requirements/<id>/progress.md`: sequence-level state for the selected goal.
- `requirements/<requirement-id>/requirements.md`: requirement-slice source of truth for goal-requirements execution.
- `requirements/<requirement-id>/research.md`: requirement-local technical research artifact when the `research` gate is required.
- `requirements/<requirement-id>/technical-design.md`: requirement-local module-level technical design artifact when the `technical-design` gate is required.
- `requirements/<requirement-id>/architecture.md`: optional requirement-local architecture design artifact when system-level design is required.
- `requirements/<requirement-id>/progress.md`: current gate, status, and next action for a requirement slice.
- `requirements/<requirement-id>/decisions.md`: material decisions made while executing a requirement slice.
- `requirements/<requirement-id>/evidence.md`: verification and review evidence for a requirement slice.
- `plans/<plan-id>/plan.md`: accepted primary implementation plan for a requirement slice.
- `plans/<plan-id>/secondary_plan.md`: accepted detailed implementation plan for a requirement slice.
- `tests/`: executable behavior and regression coverage.

## AGENTS.md Update Policy

Update this file when durable repo-level product direction, engineering rules, architecture boundaries, verification commands, env policy, document locations, or dependency policy changes. Do not put temporary task notes, secrets, local machine paths, scheduler state, generated logs, or runtime output in this file.
