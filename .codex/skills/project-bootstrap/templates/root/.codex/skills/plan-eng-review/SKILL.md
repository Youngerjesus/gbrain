---
name: plan-eng-review
description: Lightweight pre-implementation engineering review for short-cycle work. Use when the user already has direction plus a mini-plan and wants a hard check on scope, reuse, architecture, tests, and failure modes before coding. Conditionally invokes scenario-brake when state, path, or recovery complexity makes happy-path planning unsafe.
---

# Plan Eng Review

이 스킬은 짧은 주기 개발에서, 구현 직전에 "이 plan으로 바로 들어가도 되나"를 빠르게 압박 검토하는 엔지니어링 리뷰 스킬입니다.
풀 `project_manager/specs/*` 실행 스펙 파이프라인을 대체하지 않습니다.
이미 방향과 mini-plan 이 있는 상태에서 scope, reuse, architecture, test gap, failure mode 를 점검하는 preflight gate 역할을 합니다.
`goal-requirements`의 세 main gate 모델에서는 `planning-orchestrator`가 `Plan` 내부에서 이 스킬을 호출합니다. 이때 `plan-eng-review`는 top-level gate가 아니라 Plan-internal engineering review evidence 입니다.

## Contract

이 스킬이 제대로 수행된 리뷰는 다음을 보장합니다.

- direct source of truth, mini-plan, Plan handoff 또는 관련 requirement/design-depth state 를 먼저 고정하고 drift 를 숨기지 않습니다.
- scope and reuse challenge 를 첫 번째 engineering gate 로 적용해 stated outcome 을 닫는 최소 변경 집합을 찾습니다.
- 필요한 경우 Architecture review, Executable Contract Compatibility Gate, RALPLAN-DR decision review 를 실행하고, 실행 가능한 code-owned contract evidence 없이는 구현 readiness 를 승인하지 않습니다.
- proof obligations 를 unit, integration, E2E/manual, observability 중 적절한 수준으로 분리하고 vague "add tests" finding 으로 끝내지 않습니다.
- Companion reviewer 결과는 read-only evidence input 으로만 취급하고, main `plan-eng-review`가 accepted/rejected finding 과 최종 verdict 를 소유합니다.
- scenario-brake routing 을 skipped, recommended, or used 중 하나로 명시하고, state/re-entry/recovery 신호를 happy path 로 뭉개지 않습니다.
- 최종 판정은 반드시 `GO`, `GO WITH CHANGES`, `STOP` 중 하나입니다.

## Trigger

다음 상황에서 이 스킬을 우선 고려합니다.

- 사용자가 "plan 리뷰해줘", "엔지니어링 리뷰해줘", "구현 들어가기 전에 sanity check 해줘", "이대로 build 해도 되나?" 같은 요청을 할 때
- 짧은 주기 작업이지만 아래 조건 중 2개 이상이 보일 때
  - 3개 이상 파일 또는 2개 이상 모듈이 바뀐다
  - 외부 API, auth, payment, observability, state transition 이 들어간다
  - 기존 동작을 건드리는 회귀 위험이 있다
  - 구현 선택지가 2개 이상 남아 있다
  - E2E 또는 operator-facing verification 이 필요하다

다음 경우에는 다른 스킬이 더 적합할 수 있습니다.

- 방향 자체가 맞는지 의심되면 `decision-brake`
- 요구사항이 `requirements/<requirement-id>/requirements.md` 로 아직 잠겨 있지 않으면 `requirement-clarifier`
- UI/UX completeness 를 구현 전에 압박 검토하고 싶으면 `plan-design-review`
- 시나리오 누락이 핵심 우려면 `scenario-brake`
- 구현이 이미 끝났고 코드/테스트 허점을 다시 보고 싶으면 `implementation-brake`
- full `project_manager/specs/*` SDD phase review 를 닫아야 하면 spec-local `plan_review.md` 흐름과 해당 phase 문서를 우선한다

다음 경우에는 이 스킬이 과합니다.

- 명백한 단일 버그 수정
- copy/style/rename 수준의 저위험 변경
- 기존 패턴 그대로의 단순 single-path 작업
- 테스트만 보강하는 작은 변경

## Core Posture

- 목적은 문서 절차가 아니라 구현 직전 engineering sanity check 입니다.
- 가장 먼저 "기존 것을 재사용할 수 있나"와 "범위를 더 줄일 수 있나"를 봅니다.
- review 는 findings first 이지만, nitpick 보다 실제 defect risk 와 scope waste 를 우선합니다.
- minimal diff, DRY, explicitness, edge-case thoughtfulness 를 기본값으로 둡니다.
- 구현 선택지가 의미 있게 갈리는 계획에서는 RALPLAN-DR 관점으로 decision quality 도 확인합니다. 단순 계획에 불필요한 consensus ceremony 를 추가하지 않습니다.
- Companion reviewer 는 병렬 판정자가 아니라 evidence input 입니다. 최종 `GO` / `GO WITH CHANGES` / `STOP` 판정은 항상 main `plan-eng-review`가 소유합니다.
- 결과는 기본적으로 대화에 보고합니다. 자동으로 `plan_review.md`, `TODOS.md`, 대시보드, telemetry 를 남기지 않습니다.

## Workflow

### 1. Ground the plan

먼저 아래를 짧게 고정합니다.

- 무엇을 만들거나 바꾸려는지
- 사용자에게 어떤 결과가 바뀌는지
- 현재 mini-plan 또는 관련 문서가 무엇인지
- 직접 SSOT 가 있다면 어디까지인지

`requirement-clarifier`가 만든 `requirements/<requirement-id>/requirements.md`가 있으면 본 계획을 검토하거나 작성하기 전에 반드시 읽습니다. 이 파일을 product requirements source of truth 로 취급하고, mini-plan 이 requirements document 와 충돌하면 구현 리뷰를 계속하기 전에 drift 로 표시합니다.

If the work is running through `goal-requirements`, also read the Plan handoff and requirement-local research/design-depth state before implementation readiness:

- `requirements/<requirement-id>/progress.md`
- `requirements/<requirement-id>/decisions.md`
- `requirements/<requirement-id>/evidence.md`
- `plans/<plan-id>/plan_handoff.toml` when present
- `requirements/<requirement-id>/research.md` when present or required
- `requirements/<requirement-id>/technical-design.md` when Plan records `design_depth: full_artifact_required`
- `requirements/<requirement-id>/technical-design.md` when present or required
- `requirements/<requirement-id>/architecture.md` when present or required by architecture gate state

Check goal-requirements research/design gate state as a consumer, not as a new research or design author. Artifact existence alone is insufficient. A ready gate needs matching progress state, artifact path, evidence, material decisions when applicable, unresolved item classification, and no pending requirement-impact approval.

Return `STOP` before implementation readiness when:

- `research` or `technical-design` is required but the artifact is missing.
- `progress.md` says `completed` but evidence or artifact path is missing.
- an artifact exists but gate state is `not_evaluated`, `required_pending`, `in_progress`, `blocked`, `awaiting_user_approval`, or `stale_needs_recheck`.
- unresolved blocking items exist.
- architecture status is missing or contradicted by the design artifact state.
- architecture is required but `architecture.md` is missing.
- architecture is not required but the non-required rationale is missing.
- gate state is stale after a requirement change.
- direct `plan-eng-review` entry bypassed unresolved research/design gate state.

Missing evidence or missing evidence links, stale_needs_recheck, awaiting_user_approval, blocked, unresolved blocking items, or artifact/state contradiction must be reflected as implementation-readiness findings before implementation readiness.

필요한 만큼만 관련 코드, 기존 흐름, plan 문서를 읽습니다.
짧은 작업에서 과수집하지 않습니다.

### 2. Step 0: Scope challenge

반드시 아래 질문부터 봅니다.

- 이 문제를 이미 부분적으로 해결하는 기존 코드/flow 가 무엇인가
- 병렬 구현 대신 기존 output 을 capture 하거나 기존 adapter 를 재사용할 수 있는가
- stated goal 을 닫는 최소 변경 집합은 무엇인가
- 지금 plan 이 결과 대비 과하게 넓거나 깊은가

obvious leaner path 가 보이면 먼저 그 방향을 권고합니다.
이 단계의 목적은 좋은 architecture 를 칭찬하는 것이 아니라, 불필요한 작업을 제거하는 것입니다.

### 3. Architecture review

아래를 점검합니다.

- component boundary 와 ownership
- dependency direction 과 coupling
- data flow 와 integration point
- reversibility 와 rollback friendliness
- single point of failure 또는 awkward coordination point

짧은 주기 작업에서는 top 3-5 issue 만 남깁니다.
문제마다 "무엇이 깨질 수 있는지"와 "더 단순한 대안이 있는지"를 함께 적습니다.

### 3a. Executable Contract Compatibility Gate

Use this mandatory gate when the plan touches schema contracts, prompt schemas, Pydantic/model validators, structured LLM outputs, repair agents, reviewer agents, generated compiler artifacts, runtime mutation vocabularies, or trust-domain boundary fields.

This gate checks whether the proposed plan can be executed by the current code-owned contract. It must include a code-backed comparison against the actual executable schema, validators, runtime normalization rules, structured fields, deterministic capability data, or mutation vocabulary. Generated JSON schema alone is insufficient when Pydantic/model validators or runtime normalization rules can reject payloads that the JSON schema appears to allow.

For LLM reviewer or repairer outputs, identify which fields are diagnostic, authoritative, repair-driving, and prohibited from downstream mutation. For mutation vocabularies, identify legal operation types and legal payload fields from code-owned sources, not manually maintained prompt text.

If the plan asks an agent, repairer, reviewer, prompt, or runtime to produce a field, operation, or artifact that the current executable contract cannot consume, return `STOP` or an equivalent blocking implementation-readiness finding. This must not fail plan document creation, but it blocks implementation readiness until the finding is reflected in the primary plan or `secondary_plan`.

Do not use substring or regex checks over free-form prose as authoritative compatibility evidence. Free-form plan or recommended-repair text may be a clue, but the finding must be grounded in code, structured schemas, typed fields, validators, deterministic capability data, or parsed artifacts.

If no executable-contract surface is touched, state that the gate was not triggered and why.

### 3b. RALPLAN-DR decision review

아래 신호가 있으면 계획의 의사결정 품질을 별도 gate 로 봅니다.

- 구현 선택지가 2개 이상 남아 있거나, 계획이 특정 접근을 선택했지만 대안 검토가 약합니다.
- architecture, data, scheduler/runtime, auth/security, migration, public API, UX flow, observability, or cross-module ownership 결과가 달라질 수 있습니다.
- high-risk 작업인데 pre-mortem 이나 expanded test plan 이 없습니다.
- `secondary-plan` 또는 Plan Mode 산출물이 non-empty RALPLAN-DR / ADR 내용을 포함합니다. Empty template placeholders or `Not triggered` sections do not trigger this review by themselves.

점검 기준:

- **Principles**: 구현에서 지켜야 할 원칙이 task-specific 하며 requirements 와 충돌하지 않는가?
- **Decision Drivers**: 선택 기준이 실제 선택과 일치하는가?
- **Viable Options**: 적어도 두 개의 현실적 접근 또는 대안 invalidation rationale 이 있는가?
- **Rejected Alternatives**: 버린 이유가 충분해서 구현자가 같은 논쟁을 다시 열지 않아도 되는가?
- **ADR**: decision, drivers, alternatives considered, why chosen, consequences, follow-ups 가 현재 plan 과 맞는가?
- **High-risk expansion**: high-risk 작업이면 pre-mortem 3개와 unit / integration / e2e-or-manual / observability test plan 이 충분한가?

Weak RALPLAN-DR evidence 는 그 자체로 paperwork finding 이 아닙니다. 다음 중 하나를 만들 때만 issue 로 기록합니다.

- plan 이 requirements 와 다른 방향으로 흐를 위험
- 구현자가 새 product/architecture 결정을 내려야 하는 gap
- high-risk failure mode 를 검증하지 못하는 test gap
- rejected alternative 를 다시 열 가능성이 큰 ambiguity
- consequence 또는 follow-up 이 acceptance 와 섞이는 drift

### 3c. Companion agent review

When the runtime allows subagents, use up to three read-only companion reviewers before finalizing non-trivial plan-eng reviews.
Do not invoke more than these three for this skill, and do not let companions edit files, repair plans, create tasks, update specs, or override the main verdict.

The three lenses are intentionally orthogonal by first-principles failure source:

- `plan-eng-scope-reuse-reviewer`: checks whether the plan is necessary, minimum sufficient, and able to reuse existing code/flows instead of creating scope waste.
- `plan-eng-architecture-contract-reviewer`: checks whether the plan lands on the right ownership boundary, dependency direction, integration contract, data flow, and invariant surface.
- `plan-eng-verification-failure-reviewer`: checks whether the plan states the proof obligations, realistic failure modes, observability, rollback/recovery, and verification level needed before implementation.

Invoke all three when the plan has cross-module impact, stateful behavior, external dependency, protected boundary, major architecture choice, or high-confidence `GO` would otherwise depend on a single reviewer view.
For narrow low-risk single-path work, companion routing may be skipped if the main pass can directly inspect the plan, relevant code, and verification obligation.

Give each companion the mini-plan, requirement/source documents read, relevant code/context summary, known constraints, and this skill's output contract.
Ask each companion to stay inside its lens and return findings first.

Companion finding reconciliation is mandatory when companions are used:

- **accepted + plan-changing**: include as a top issue or required change before implementation
- **accepted + verification-changing**: include as a missing test/proof obligation
- **accepted but separable**: include as deferred or follow-up only when it does not affect this implementation's acceptance
- **plausible but unproven**: mark as evidence needed, not as a blocking fact
- **rejected**: record a short reject reason grounded in requirement, code, plan, contract, or test evidence

Do not copy every companion note into the final answer.
The main review must deduplicate overlapping findings, drop out-of-lens or speculative feedback, and keep only issues that change implementation scope, architecture boundary, verification, or final recommendation.

### 4. Test review

plan 기준으로 main codepath 와 user flow 를 추적합니다.
가능하면 compact ASCII diagram 으로 요약합니다.

반드시 확인할 것:

- happy path 외 분기
- existing behavior change 에 대한 regression test 필요 여부
- unit / integration / E2E 중 어떤 수준이 맞는지
- test gap 이 실제 user-visible failure 로 이어지는지

test review 는 "테스트가 있으면 됨"이 아니라, 이 plan 으로 구현했을 때 무엇이 증명돼야 하는지 보는 단계입니다.

### 5. Failure-mode review

2-5개의 realistic production failure 를 적습니다.
각 failure 마다 아래를 본다.

- plan 이 이를 예방하는가
- plan 이 실패를 처리하는가
- user 또는 operator 가 명확히 볼 수 있는가
- silent failure 로 끝날 가능성이 있는가

test 없음 + handling 없음 + silent failure 인 경우는 강하게 지적합니다.

### 6. Conditional scenario-brake hook

기본값은 `scenario-brake`를 자동 실행하지 않는 것입니다.
아래 신호가 보일 때만 추가 호출 또는 권고합니다.

- 의미 있는 state 가 3개 이상 있다
- 동일 흐름에 entry path 가 2개 이상 있다
- retry, resume, refresh, back, reopen 같은 re-entry 경로가 중요하다
- auth, payment, quota, session-expiry 같은 조건 분기가 핵심이다
- UI 와 backend 가 다른 타이밍으로 실패할 수 있다
- `partial`, `stale`, `empty`, `delayed` 같은 상태가 제품적으로 중요하다

이 경우 `scenario-brake`의 역할은 test count 확대가 아니라, plan 이 서로 다른 현실 경로를 같은 것으로 뭉뚱그렸는지 압박 검토하는 것입니다.

위 신호가 없으면 scenario review 를 생략하고, 왜 happy-path bias 위험이 낮다고 판단했는지 한 줄로 적습니다.

### 7. Final recommendation

마지막에는 반드시 아래 중 하나로 판정합니다.

- `GO`
- `GO WITH CHANGES`
- `STOP`

최종 답변에는 아래를 포함합니다.

- review 대상
- scope cut recommendation 여부
- top issues
- top missing tests
- top failure modes
- `scenario-brake`를 skipped / recommended / used 중 무엇으로 처리했는지
- companion reviewers 를 invoked / skipped / fallback-applied 중 무엇으로 처리했는지와 accepted/rejected finding 요약

## Output Format

응답은 아래 순서를 기본으로 합니다.

1. **Plan under review**
2. **Scope challenge**
3. **Architecture findings**
4. **Test findings**
5. **Failure modes**
6. **Companion review synthesis** when companions were invoked or explicitly skipped
7. **Scenario review decision**
8. **RALPLAN-DR decision review** when used or explicitly skipped
9. **Recommendation**

필요할 때만 마지막에 **Open questions** 를 붙입니다.
질문은 구현 방향을 바꾸는 tradeoff 가 있을 때만 남깁니다.

## Interaction Rules

- 기본은 한 번의 통합 리뷰 응답입니다.
- issue 마다 무조건 질문 루프를 돌리지 않습니다.
- genuine tradeoff 가 있을 때만 사용자의 결정을 요청합니다.
- 사용자 질문이 없더라도 recommendation 은 명확하게 냅니다.
- review 를 핑계로 새로운 artifact 체계를 들이밀지 않습니다.

## Relationship To Other Skills

- `decision-brake`: 방향, 문제정의, 대안 선택이 흔들릴 때
- `scenario-brake`: scenario coverage, re-entry, recovery, path separation 이 흔들릴 때
- `plan-design-review`: 구현 전 plan 의 UI/UX completeness 와 design decision gap 을 점검할 때
- `plan-eng-review`: 방향은 대체로 정해졌고, 구현 직전 engineering preflight 가 필요할 때

이 스킬은 `decision-brake`와 `scenario-brake` 사이에 끼어드는 것이 아니라, 짧은 주기 구현의 마지막 preflight review 역할을 맡습니다.
RALPLAN-DR 검토는 `decision-brake`를 대체하지 않습니다. 방향 자체의 proceed/stop verdict 가 흔들리면 `decision-brake`로 돌리고, 계획의 선택 근거와 구현 handoff quality 만 문제라면 이 스킬 안에서 `GO WITH CHANGES` 또는 `STOP`으로 판정합니다.

## Anti-Patterns

- 방향이 정해졌다는 이유만으로 mini-plan 을 rubber-stamp 하고 `GO`를 주는 것.
- acceptance 를 바꾸지 않는 broad cleanup, 새 artifact 체계, process ceremony 를 scope 에 끌어들이는 것.
- free-form prose, substring, regex clue 를 authoritative contract compatibility evidence 로 취급하는 것.
- Companion reviewer 를 최종 판정자로 만들거나 companion note 를 reconciliation 없이 그대로 복사하는 것.
- state, retry, resume, auth, partial, stale, delayed 경로가 있는데 scenario-brake routing 을 생략하는 것.
- "테스트 추가" 같은 모호한 finding 으로 끝내고 proof obligations 와 verification level 을 분리하지 않는 것.
- plan 리뷰를 핑계로 `plan_review.md`, TODO, dashboard, telemetry, global log 를 기본 생성하는 것.

## Constraints

- full gstack-style orchestration 을 복제하지 않습니다.
- telemetry, session state, CLAUDE routing, dashboard, global review log 를 만들지 않습니다.
- 자동 문서 갱신을 기본값으로 두지 않습니다.
- full `project_manager/specs/*` review workflow 를 대체하지 않습니다.
- 작은 작업을 불필요하게 무겁게 만들지 않습니다.
