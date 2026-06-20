---
name: scenario-brake
description: General-purpose pre-implementation review skill for pressure-testing whether a plan, spec, or design covers enough realistic scenarios. Use when the user wants a hard pass on missing scenarios, conflated paths, parameter variations, recovery paths, or whether a plan only covers the happy path.
---

# Scenario Brake

reference @./references/review-lenses.md

이 스킬은 구현 전에 계획안, 설계안, spec 초안을 대상으로 "이 문서가 실제로 충분한 시나리오를 커버하나"를 압박 검토하는 리뷰 스킬입니다.
테스트 종류를 늘리는 것이 목적이 아니라, 계획이 서로 다른 현실 경로를 하나의 문제로 뭉뚱그렸는지와 주요 파라미터를 바꿨을 때 빠지는 시나리오가 생기는지를 드러내는 것이 목적입니다.

## Trigger

다음 상황에서 이 스킬을 우선 고려합니다.

- 사용자가 "시나리오가 충분한지 봐줘", "happy path 말고 다른 경로를 더 생각해봐", "이 계획이 뭘 놓치고 있나?", "엣지 시나리오를 더 세게 봐줘" 같은 요청을 할 때
- 테스트 개수보다, 현실적인 변형 경로와 누락된 검증 대상을 더 중요하게 보고 싶을 때
- 같은 문제처럼 보이는 경로가 실제로는 다른 원인, 다른 진입 방식, 다른 복구 전략을 요구하는지 확인하고 싶을 때

다음 경우에는 다른 스킬이 더 적합할 수 있습니다.

- 방향 자체의 타당성과 대안을 검토하려면 `decision-brake`
- 구현이 이미 끝난 뒤 defect risk 와 test gap 을 보려면 `implementation-brake`
- spec/contracts 를 SSOT 수준으로 잠그려면 `spec-reviewer`

## Core Posture

- checklist 를 채우는 것이 아니라 scenario coverage 를 압박 검토합니다.
- 시나리오를 한 줄 사건으로 보지 않고, 그것을 구성하는 주요 파라미터를 먼저 봅니다.
- "엣지 케이스가 빠졌다" 같은 뭉뚱그린 말로 끝내지 않고, 무엇을 같은 경로로 잘못 취급했는지와 무엇을 분리해야 하는지 적습니다.
- 같은 최종 상태, 같은 에러 문자열, 같은 retry label 이라고 해서 같은 시나리오로 보지 않습니다. actor, entry path, persisted state, artifact ownership, recovery owner, observability signal 이 다르면 별도 시나리오 후보입니다.
- 상태 머신, scheduler, resumable workflow, retry loop 처럼 stateful control plane 이 있는 계획에서는 하나의 상태나 phase 추가가 enum, transition graph, retry/continue budget, result artifact, prompt context, resume source, hook/metric/status signal 로 어떻게 전파되는지 추적합니다.
- Companion reviewer 는 병렬 판정자가 아니라 evidence input 입니다. 최종 `[SCENARIOS SUFFICIENT]` / `[SCENARIOS MISSING]` / `[PLAN NEEDS REFRAME]` verdict 는 항상 main `scenario-brake`가 소유합니다.
- 결과는 기본적으로 사용자에게 보고합니다. review 결과를 자동으로 spec/contract 에 반영하는 것을 기본값으로 두지 않습니다.

## Workflow

### 1. Ground the plan

먼저 아래를 짧게 고정합니다.

- 무엇을 계획 중인지
- 어떤 핵심 흐름을 닫으려는지
- 현재 문서가 이미 커버한다고 주장하는 시나리오가 무엇인지
- 어떤 source input 을 읽었고, 어떤 입력은 없어서 추정하고 있는지

필요하면 관련 문서, 코드, 과거 버그 맥락을 읽되, 중심은 현재 계획의 scenario coverage 입니다.

State-machine or scheduler-like plans need an explicit ripple map before verdict:

- phase/status registries and ordered pipelines, for example `BASE_PIPELINE_PHASES`, status enums, `WATCHED_STATUSES`, `TERMINAL_STATUSES`, and `RECOVERY_STATUSES`
- transition selectors, next/retry routing, watchdog or timeout paths, and restart/replay entry points
- retry and continue budgets, attempt counters, and names such as `DEFAULT_RETRY_COUNTS` or `DEFAULT_CONTINUE_COUNTS`
- result/status artifact naming, attempt-specific files, previous-result loading, and scheduler-owned `PM_RESULT` or result path behavior
- prompt builders and review-file selectors such as `PHASE_REVIEW_FILES`
- resume sources such as `RESUME_SOURCE_PHASES`, stale-session exclusion, `resume_blacklist`, strict resume versus fresh restart behavior
- observability hooks, operator signals, event kinds such as `recovery_checkpoint`, and hook error handling

CAO candidate review 에서는 먼저 아래 canonical inputs 를 읽습니다.

- 루트 `AGENTS.md`
- `policies/autonomy-policy.yml`
- 관련 `ssot/*.md`
- `human-requests/inbox.md`
- `memory/*`
- `project_manager/AGENTS.md`
- `project_manager/project_profile.json`
- `project_manager/tasks/tasks.json`
- `project_manager/specs/<feature_slug>/` 아래의 `design.md`, `plan.md`, `spec.md`, `contracts.md`, 기존 review artifacts

Managed repo 증거가 필요하면 `project_manager/project_profile.json`에서 active repo 의 `source_repo_root`, `workspace_root`, `main_worktree`를 resolve 한 뒤 해당 경로만 탐색합니다. 필요한 입력이 없으면 legacy path 로 대체하지 말고 `missing evidence`로 기록합니다.

### 2. Identify scenario classes

현재 계획에서 중요한 scenario class 를 고릅니다.

- entry path
- actor
- state
- data shape
- dependency behavior
- recovery path
- environment/runtime context
- invariants
- observability
- artifact and prompt ownership
- state-machine transition and phase ripple

모든 class 를 기계적으로 다 쓰지 말고, 계획의 pass/fail 을 가장 많이 바꿀 것만 고릅니다.
단, 상태나 phase 를 추가/수정하는 계획은 transition, artifact/prompt, resume/restart, observability 중 어떤 class 를 의도적으로 제외했는지 근거를 남깁니다.

### 3. Mutate key parameters

`references/review-lenses.md`를 참고해 baseline scenario 의 주요 파라미터를 식별하고 값을 바꿔 봅니다.

핵심 원칙은 다음과 같습니다.

- baseline scenario 를 먼저 한 문장으로 적습니다.
- 그 시나리오를 성립시키는 주요 파라미터를 3-7개 식별합니다.
- 파라미터를 하나씩 바꿔 변형 시나리오를 만듭니다.
- 필요한 경우 고위험 조합만 2개 이상 함께 바꿉니다.
- 새 시나리오가 기존 시나리오와 truly same path 인지, 별도 시나리오인지, 다른 시나리오의 선행/후속 경로인지 판정합니다.

Stateful control-plane plans should consider these parameter mutations when relevant:

- `entry`: first run, manual retry, automatic retry, strict resume, cold restart, stale session lookup, fresh session fallback
- `state`: initial, in-progress, partial success, failed, terminal fail, already-completed, stale, waiting retry, waiting restart
- `transition`: normal next phase, retry phase, continue phase, watchdog mutation, timeout recovery, terminalization
- `budget`: retry count exhausted, continue count exhausted, per-phase default absent, attempt index mismatch
- `artifact`: missing result, malformed result, previous verify result, attempt-specific status/result prefix, scheduler-owned report path
- `prompt`: phase-specific review files, recovery preamble, previous failure context, fresh finalization context
- `observability`: watched status, terminal status, recovery status, hook failure, operator signal, silent success, misleading success
- `environment`: process restart, cold start, config drift, feature flag difference, missing cookies, mobile/browser context, replay safety
- `invariant`: idempotency, uniqueness, ownership, stale exclusion, ordering, monotonic progression

### 4. Separate vs connect

특히 아래 질문을 우선합니다.

- 현재 계획이 서로 다른 진입 경로를 같은 시나리오로 뭉뚱그렸는가?
- 같은 실패 현상이 실제로는 다른 원인과 다른 복구 전략을 가지는가?
- 특정 시나리오의 후속 경로나 재진입 경로가 빠져 있는가?
- 한 파라미터 변화가 다른 scenario class 와 연결되며 전혀 다른 검증 전략을 요구하는가?
- 상태나 phase 추가가 phase list 만 바꾸고 transition graph, retry/continue counters, result status normalization, prompt context, resume source, observability hook 을 빠뜨렸는가?
- recovery plan 이 retry success 만 보며 rollback failure, cleanup failure, terminal fail, operator decision signal 을 같은 실패로 묶고 있지 않은가?

When a plan only updates a registry or map, treat it as incomplete until the review explains why downstream selectors, persisted artifacts, restart behavior, and operator signals are either unaffected or explicitly covered.

### 5. Recommend coverage additions

빠진 시나리오를 찾으면 아래를 함께 적습니다.

- 왜 기존 계획으로는 커버됐다고 보기 어려운지
- 어떤 변형 파라미터가 새 시나리오를 만들었는지
- 이후 어떤 수준의 검증이 필요한지
  - unit
  - integration
  - e2e
  - restart/replay
  - concurrency
  - manual ops check

For scheduler/state-machine changes, recommended additions should name the concrete surface that must be covered, such as phase registry, transition graph, retry or continue budget, result/status artifact prefix, prompt builder, resume source, status hook, or operator-facing recovery signal.

### 6. Companion agent review

When the runtime allows subagents, use up to three read-only companion reviewers before finalizing non-trivial scenario-brake reviews.
Do not invoke more than these three for this skill, and do not let companions edit files, repair plans, update specs/contracts, enqueue tasks, or override the main verdict.

The three lenses are intentionally orthogonal by first-principles scenario failure source:

- `scenario-path-separation-reviewer`: checks whether entry paths, actors, states, sequence, and re-entry paths are being conflated.
- `scenario-parameter-mutation-reviewer`: checks whether data shape, dependency behavior, environment, timing, and high-risk parameter combinations create missing scenarios.
- `scenario-recovery-observability-reviewer`: checks whether failure recovery, invariant preservation, cleanup, user/operator signals, and silent-success paths are covered.

Invoke all three when scenario coverage is the requested deliverable, when CAO candidate review depends on the scenario verdict, or when the plan includes meaningful state, dependency, recovery, or operator-facing behavior.
For narrow low-risk plans with a single entry path, no state/recovery behavior, and directly inspectable scenario evidence, companion routing may be skipped.

Give each companion the baseline scenario, source inputs read, plan/spec/contracts under review, known covered scenarios, and this skill's output contract.
Ask each companion to stay inside its lens and return findings first.

Companion finding reconciliation is mandatory when companions are used:

- **accepted + missing scenario**: include in `Missing or conflated scenarios`
- **accepted + plan reframe**: include in `Highest-risk blind spots` and consider `[PLAN NEEDS REFRAME]`
- **accepted + verification addition**: include in `Recommended scenario additions`
- **plausible but unproven**: mark as evidence needed, not as a scenario fact
- **rejected**: record a short reject reason grounded in plan/spec/contract/code/evidence

Do not copy every companion note into the final answer.
The main review must deduplicate overlapping findings, drop out-of-lens or speculative feedback, and keep only scenario gaps that change the verdict, handoff impact, or required followups.

### 7. Companion review synthesis

When companions are invoked or explicitly skipped, include a short `Companion review synthesis` section in the final answer.
Name which findings were accepted, which were plausible but unproven, which were rejected, and why a low-risk review skipped companions when that is the case.

## Output Shape

응답은 아래 순서를 기본으로 합니다.

1. **Scenario classes reviewed**
2. **Key parameters identified**
3. **Parameter mutations explored**
4. **Scenario links and separations**
5. **What the plan already covers**
6. **Missing or conflated scenarios**
7. **Highest-risk blind spots**
8. **Recommended scenario additions**
9. **Companion review synthesis** when companions were invoked or explicitly skipped
10. **Overall verdict**

판정은 반드시 아래 중 하나를 사용합니다.

- `[SCENARIOS SUFFICIENT]`
- `[SCENARIOS MISSING]`
- `[PLAN NEEDS REFRAME]`

Use `[PLAN NEEDS REFRAME]` when the missing scenarios are not just extra cases but reveal that the plan's model of control flow is incomplete, especially when state-machine phase/status changes omit transition, artifact, resume, or observability surfaces.

CAO candidate review 에서는 이 verdict 를 그대로 `project_manager/specs/<feature_slug>/scenario_review.md`에 기록하고, scenario coverage 결론을 이 세 값 밖으로 벗어나지 않게 유지합니다.

CAO candidate review 에서는 아래 normalized fields 를 포함합니다.

- `feature_slug`
- `source_inputs_read`
- `missing_inputs`
- `verdict`
- `missing_or_conflated_scenarios`
- `highest_risk_blind_spots`
- `handoff_impact`
- `required_followups`

CAO runtime 이 structured output schema 를 함께 제공하면, 최종 응답은 해당 schema 와 정확히 일치하는 plain JSON object 여야 합니다. 위 normalized fields 중 runtime schema 에 없는 값은 `scenario_review.md` human-facing artifact 에만 기록하고, 최종 structured response 의 top-level key 로 추가하지 않습니다.

CAO policy mapping:

- `[SCENARIOS SUFFICIENT]`: 후보가 남은 handoff gate 를 계속 통과할 수 있음
- `[SCENARIOS MISSING]`: 정책상 defer; 누락 시나리오를 planning/spec artifact 에 반영해야 함
- `[PLAN NEEDS REFRAME]`: 정책상 defer; 시나리오 보강이 아니라 plan 재구성이 먼저 필요함

Protected area 변경, security/data-loss/deploy risk, conflicting evidence 가 시나리오 결론에 영향을 주면 `handoff_impact=escalation-needed` 또는 `human-input-needed`로 기록합니다.

## Benchmark And Verification

- Repo에 상시 SkillOpt benchmark artifact를 보관하지 않습니다.
- SkillOpt를 다시 실행해야 하면 request-local `skillopt-benchmark.jsonl`을 생성하고, task와 judge를 검토한 뒤 실행 종료 후 산출물을 정리합니다.
- Benchmark rows 는 scenario review 품질을 직접 겨냥해야 하며, 단순 heading 존재만으로 충분하다고 보지 않습니다. Rule checks 는 verdict, scenario separation, parameter mutation, verification level, and companion reconciliation 같은 handoff-changing behavior 를 함께 요구해야 합니다.
- `# BOOTSTRAP_PENDING_REVIEW` sentinel 이 있는 benchmark 는 optimizer wiring 검증용 초안입니다. 사람이 task 와 judge 를 검토하고 보강하기 전에는 direct skill mutation 의 acceptance 기준으로 사용하지 않습니다.

## Compact Examples

예:

- baseline: `resume 실패 후 같은 phase strict resume 시 no rollout found -> fresh session fallback`
- parameters: `persisted status`, `entry trigger`, `session lookup source`, `prior stale knowledge`
- mutation: `persisted status=FAILED`, `entry trigger=scheduler restart`, `lookup=find_session_id()`
- result: strict resume 시나리오와 다른 일반 재진입 경로가 생성되므로, stale session 재선택 위험은 별도 시나리오로 분리해야 함

State-machine 예:

- baseline: `새 phase 를 BASE_PIPELINE_PHASES 에 추가하면 normal next transition 으로 실행된다`
- parameters: `retry budget`, `continue budget`, `WAITING_RETRY re-entry`, `result/status prefix`, `resume source`, `status hook`
- mutation: `entry=automatic retry`, `budget=missing default`, `status=WAITING_RETRY`
- result: phase list 추가만으로는 재시도, attempt naming, resume exclusion, recovery observability 가 닫히지 않으므로 transition graph 와 artifact/hook 시나리오를 분리해야 함

이 예시는 상태 전이 사례를 보여주지만, 스킬 자체는 특정 상태 머신 전용이 아니라 parameter mutation 으로 missing scenario 를 찾는 범용 리뷰 스킬입니다.

## Constraints

- 구현, 스캐폴딩, 코드 수정은 하지 않습니다.
- unit 테스트 개수나 파일 수로 coverage 를 판단하지 않습니다.
- 리뷰 결과를 자동으로 spec/contract SSOT 에 반영하지 않습니다.
- 특정 버그 클래스에 맞춘 체크리스트로 축소하지 않습니다.
