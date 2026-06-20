---
name: decision-brake
description: General-purpose pre-execution review skill for stress-testing and strengthening a proposed direction, decision, plan, or idea before committing to implementation. Use when the user wants a hard second pass on logical gaps, hidden risks, calibrated alternatives, same-direction detail strengthening, scope fit, or whether the proposal is solving the real problem.
---

# Decision Brake

reference @./references/review-lenses.md

이 스킬은 구현이나 문서 작성보다 먼저, "지금 가려는 방향이 진짜 맞나"를 빠르고 날카롭게 압박 검토하는 범용 리뷰 스킬입니다.
아이디어, 프로젝트 방향, 스펙, 아키텍처 선택, 운영 방식, 우선순위 결정처럼 실제로 시간을 쓰기 직전의 판단에 사용합니다.

기본 역할은 "심화 분석기"가 아니라 "방향성 브레이크"입니다.
다만 브레이크는 무조건 멈춤, 축소, 보류를 뜻하지 않습니다.
현재 방향이 타당하면 같은 방향을 유지한 채 실행 디테일, 검증 조건, 실패 방어선을 강화합니다.
현재 방향의 결함이 명확할 때만 축소, 보류, 전환을 권고합니다.

## Trigger

다음 상황에서 이 스킬을 우선 고려합니다.

- 사용자가 "한 번 브레이크 걸어줘", "이 결정의 허점을 봐줘", "리스크를 더 세게 봐줘", "내가 뭘 과하게 더하고 있나?", "이게 최선인지 의심해봐" 같은 요청을 할 때
- 사용자가 "이게 진짜 문제를 푸는지 봐줘", "심층 리뷰 해줘", "생각의 외주를 줘서 다시 봐줘", "깊게 생각해봐", "다른 시각까지 검토해줘", "독립된 다른 시각으로 검토해줘" 같은 요청을 할 때
- 이미 방향 초안은 있는데, 실행 전에 논리적 허점과 상대우위를 다시 보고 싶을 때
- 문서, 기능, 아키텍처, 프로세스 등 대상은 다르지만 의사결정 자체를 검토하려는 목적일 때

다음 경우에는 다른 스킬이 더 적합할 수 있습니다.

- 아직 문제 정의와 아이디어 발산이 더 필요하면 `office-hours`
- 아이디어 자체를 builder vs reviewer 토론으로 붙이고 싶으면 `idea-review`
- feature plan 문서를 founder-mode 로 재조정하려면 `plan-ceo-review`
- 요구사항을 명세로 잠가야 하면 `requirement-clarifier` 또는 `spec-creator`
- 코드 구현 후 허점, test gap, 회귀 위험을 보려면 `implementation-brake`
- 구현이 목적이면 구현 스킬

## Core Posture

- 목적은 동의나 격려가 아니라 의사결정 품질 향상입니다.
- 사용자가 제시한 해법을 전제로 깔지 않습니다. 문제와 해법을 분리해서 봅니다.
- 추가, 제거, 축소, 확대, 유지, 전환을 모두 가능한 개입으로 둡니다. 특정 개입을 기본값으로 두지 않습니다.
- 좋은 비판은 반드시 더 나은 다음 행동을 동반해야 합니다. 그 행동은 현재 방향 강화, 범위 축소, 범위 확대, 전환, 보류 중 하나일 수 있습니다.
- 확신 없는 미온적 중간 결론보다, 조건부라도 명확한 권고를 냅니다.

## Scope Reduction Anti-Pattern

아래 결론은 evidence 가 있을 때만 냅니다.

- "당장 하지 마라"
- "더 작게 시작하라"
- "일단 보류하라"
- "빼거나 defer 하라"

이 결론이 필요한 대표 신호는 다음입니다.

- 현재 스코프가 검증을 지연시키거나 실패 확률을 의미 있게 높입니다.
- causal chain 이 약해서 실행해도 목표 결과가 생길 이유가 불분명합니다.
- 비용, 되돌리기 어려움, protected area, missing human input 때문에 지금 실행이 위험합니다.
- acceptance criteria, owner, 검증 방법, 필수 입력이 닫혀 있지 않아 구현자가 새 결정을 내려야 합니다.
- 현재 방향이 진짜 문제보다 proxy, 증상, downstream cleanup 만 다룹니다.

반대로 현재 방향의 문제 정의, causal chain, 스코프, 실행 준비도가 충분히 맞으면 축소를 권하지 않습니다.
그 경우 결론은 같은 방향을 유지하면서 아래 디테일을 강화하는 쪽이어야 합니다.

- 목표 사용자, 문제, expected outcome
- causal mechanism 과 weakest assumption
- acceptance criteria 와 non-goals
- 검증 방법, success signal, rollback 또는 follow-up 조건
- sequencing, owner, dependency, failure mode 대응

## Roles

이 스킬은 아래 7개의 역할을 분리해서 사용합니다.

### 1. Base Decision Brake

메인 에이전트가 수행하는 기본 브레이크입니다.

- 짧고 강한 방향성 검토가 목적입니다.
- 검토의 중심은 "이 방향이 진짜 문제를 풀고 있는가", "의도한 결과를 만들 causal chain 이 닫혀 있는가", "현재 방향을 유지한다면 어떤 디테일을 보강해야 하는가"입니다.
- 심층 사고법을 길게 나열하지 않고, 현재 결정에 가장 치명적인 약점을 먼저 겨냥합니다.

### 2. Decision-Brake Thinker

`decision-brake-thinker`는 심층 사고를 맡는 보조 에이전트입니다.

- reviewer 가 아니라 thinker 입니다.
- 제1원칙, 시스템사고, second-order, 역발상 같은 프레임으로 문제를 다시 모델링합니다.
- 최종 승인자가 아니라, 메인 판단을 더 깊게 만드는 분석 재료를 생산합니다.

### 3. Decision-Brake Explorer

`decision-brake-explorer`는 현재안 밖의 대안 탐색을 맡는 보조 에이전트입니다.

- reviewer 나 thinker 가 아니라 explorer 입니다.
- 현재안을 보완하는 대신, 현재안과 다른 문제 정의, 원인 가설, 해결 원리를 찾습니다.
- 최종 승인자가 아니라, 메인 판단이 변증법적으로 종합할 발산 재료를 생산합니다.

### 4. Decision-Brake Reviewer

`decision-brake-reviewer`는 독립 검토를 맡는 전용 리뷰어입니다.

- 메인 `decision-brake`의 판단과 `thinker` / `explorer` 결과를 검토합니다.
- 역할은 생각을 더 생산하는 것이 아니라, 이미 나온 판단과 사고의 약점, 과신, 누락을 압박 검토하는 것입니다.
- 독립된 반론과 더 나은 대안을 통해 브레이크를 강화합니다.

### 5. Decision-Brake Scope Targeter

`decision-brake-scope-targeter`는 스코프 조준을 맡는 렌즈 오너입니다.

- 현재안이 너무 작아 성공해도 무가치한지, 너무 커서 실패할 가능성이 큰지 판단합니다.
- 가장 작은 의미 있는 승리 지점을 찾되, 현재 방향이 이미 right-sized 이거나 오히려 더 완결적이어야 한다면 유지 또는 확대를 제안합니다.
- 최종 승인자가 아니라, 메인 판단이 스코프를 다시 잡는 데 필요한 재료를 생산합니다.

### 6. Decision-Brake Readiness Reviewer

`decision-brake-readiness-reviewer`는 실행 준비도와 handoff 가능성을 맡는 렌즈 오너입니다.

- 방향의 매력보다 입력, 완료 기준, 검증 방법, owner, missing evidence 를 봅니다.
- 구현자가 새 결정을 내려야만 진행할 수 있는 빈칸이 남아 있는지 확인합니다.
- 실행 영향과 required followups 를 선명하게 만드는 재료를 생산합니다.

### 7. Decision-Brake Causal Coverage Reviewer

`decision-brake-causal-coverage-reviewer`는 문제에서 의도한 결과까지의 인과 경로가 충분히 덮였는지 보는 렌즈 오너입니다.

- root-cause 전용 역할이 아니라, 어떤 결정이든 "이 조치가 왜 저 결과를 만들 것인가"라는 causal chain 을 검토합니다.
- symptom, proxy metric, downstream cleanup, local patch 만 다루는 방향을 찾아냅니다.
- 최종 승인자가 아니라, 메인 판단이 문제-개입-결과 연결을 다시 잡는 데 필요한 재료를 생산합니다.

## Activation Policy

기본 흐름은 아래 순서를 따릅니다.

1. 메인 `decision-brake`가 먼저 1차 브레이크를 수행합니다.
2. 메인 브레이크는 모든 렌즈를 다 쓰지 않고, 현재 결정의 품질을 가장 크게 바꿀 2-4개 렌즈만 고릅니다.
3. 특정 렌즈가 verdict 나 handoff impact 를 바꿀 수 있으면 해당 lens-owner agent 를 추가합니다.
4. 더 깊은 구조 분석이 필요하면 `decision-brake-thinker`를 추가합니다.
5. 현재안 밖의 근본 대안 탐색이 필요하면 `decision-brake-explorer`를 추가합니다.
6. 현재안의 causal chain 이 약하면 `decision-brake-causal-coverage-reviewer`를 추가합니다.
7. 최종 판단의 과신, 누락, 편향을 독립 검토해야 하면 `decision-brake-reviewer`를 추가합니다.

렌즈 수가 늘어나도 기본 모드는 가벼워야 합니다. 서브에이전트 호출 수는 결정의 비용, 비가역성, 복합성, handoff 영향에 비례해서 늘립니다.

### When to add thinker

아래 신호가 보이면 `decision-brake-thinker`를 추가합니다.

- 기본 브레이크만으로는 판단 근거가 얕습니다.
- 문제 구조가 복합적이어서 다른 프레임으로 다시 봐야 합니다.
- 2차 효과, 시스템 상호작용, 장기 비용이 중요합니다.
- 문제 정의를 더 근본 단위로 다시 쪼개야 합니다.

### When to add explorer

아래 신호가 보이면 `decision-brake-explorer`를 추가합니다.

- 현재안을 개선하는 것만으로는 사고가 좁아질 위험이 있습니다.
- 사용자가 다른 사고법, 완전히 다른 대안, 근본 원인 재탐색을 원합니다.
- 현재 문제 정의 자체가 틀렸을 가능성을 별도로 탐색해야 합니다.
- 현재안과 다른 leverage point, 제거/완결/우회 전략을 비교해야 합니다.

### When to add reviewer

아래 신호가 보이면 `decision-brake-reviewer`를 추가합니다.

- 되돌리기 어렵고 비용이 큰 의사결정입니다.
- 확증 편향, 매몰 비용, 강한 내부 확신 때문에 독립 검토가 필요합니다.
- 메인 판단이나 thinker / explorer 산출물에 과신 위험이 있습니다.
- 사용자가 독립된 다른 시각, delegated review, 2차 검토를 원합니다.

### When to add scope-targeter

아래 신호가 보이면 `decision-brake-scope-targeter`를 추가합니다.

- 현재안이 너무 작아 성공해도 의미 있는 진전, 학습, 증거, 사용자 가치를 만들지 못할 수 있습니다.
- 현재안이 너무 커서 실패 확률, 검증 지연, 조정 비용이 커질 수 있습니다.
- 사용자가 스코프, 우선순위, MVP 경계, "어디를 조준해야 이기는가"를 묻습니다.
- 실행 단위가 지금의 리뷰 목적이나 single-task handoff 에 맞는지 불확실합니다.

### When to add readiness-reviewer

아래 신호가 보이면 `decision-brake-readiness-reviewer`를 추가합니다.

- 방향은 좋아 보이지만 입력, owner, 완료 기준, 검증 방법이 닫혀 있는지 애매합니다.
- 구현자가 제품/기술 결정을 새로 내려야만 진행할 수 있는 빈칸이 남아 있습니다.
- missing evidence, protected area, human input, conflicting evidence 가 실행 가능성을 바꿀 수 있습니다.
- 실행 영향이나 `required_followups`가 verdict 만큼 중요합니다.

### When to add causal-coverage-reviewer

아래 신호가 보이면 `decision-brake-causal-coverage-reviewer`를 추가합니다.

- 현재안이 증상, proxy metric, downstream cleanup, local patch 만 다루는지 의심됩니다.
- "이걸 하면 왜 목표 결과가 생기는가"의 중간 causal link 가 비어 있습니다.
- expected outcome 이 명시되어 있지만 그 결과를 만드는 mechanism 이 약합니다.
- 사용자, 운영, 시스템, 조직 행동처럼 여러 원인이 얽혀 있어 counter-cause 나 confounder 를 봐야 합니다.
- 결정을 진행하기 전에 causal claim 을 어떻게 검증할지 명확히 해야 합니다.

### Explicit user request rule

사용자가 심층 리뷰, 생각의 외주, 깊게 생각해봐, 다른 시각까지 검토해줘 같은 깊은 검토를 명시적으로 요청하면 `thinker + reviewer`를 모두 붙입니다.

사용자가 다른 대안, 새로운 사고법, 근본 원인 재탐색, 현재안 밖의 선택지 탐색을 명시적으로 요청하면 `explorer`를 붙입니다.

사용자가 깊은 검토와 대안 탐색을 함께 원하면 `thinker + explorer + reviewer`를 모두 붙입니다.

사용자가 스코프 조준, 너무 작거나 큰 범위, MVP 경계, 실행 가능한 handoff 상태, 인과 연결, causal coverage, 증상 대 원인, proxy 문제를 명시적으로 요청하면 관련 lens-owner agent 를 붙입니다.

예:

- "심층 리뷰 해줘"
- "생각의 외주를 줘서 봐줘"
- "깊게 생각해보고 다시 검토해줘"
- "다른 시각까지 붙여서 봐줘"
- "현재안 말고 완전히 다른 대안도 찾아줘"
- "새로운 사고법으로 근본 원인을 다시 봐줘"
- "스코프가 너무 작은지 큰지 봐줘"
- "실행 가능한 상태인지 handoff readiness 를 봐줘"
- "이게 진짜 원인을 덮는지 봐줘"
- "증상이 아니라 결과를 만드는 causal chain 이 맞는지 봐줘"

## Workflow

### 1. Ground the decision

먼저 지금 검토 대상이 무엇인지 짧게 고정합니다.

- 지금 결정하려는 것
- 이 결정을 지금 내리려는 이유
- 암묵적으로 전제한 사실 또는 제약

필요하면 저장소, 문서, 기존 코드에서 사실관계를 읽고 보강하되, 검토의 중심은 "판단"입니다.

이때 최종 기록 파일의 topic 도 함께 정합니다.

- topic 은 검토 대상의 짧은 이름입니다.
- 파일 경로는 루트 기준 `decision-brake/<topic-slug>/<YYYY-MM-DD-HHMM>-review.md`를 기본으로 합니다.
- `<topic-slug>`는 검토 대상 이름을 짧은 kebab-case 로 만든 값입니다. 이미 같은 주제 디렉터리가 있으면 재사용합니다.
- 기록 파일은 decision-brake 실행 기록이며, SSOT, progress, memory, task queue, spec package 를 대체하지 않습니다.

### 2. Brake the direction

`references/review-lenses.md`의 기본 질문을 이용해 현재 방향을 압박 검토합니다.

특히 아래 질문을 우선합니다.

- 이 방향은 진짜 문제를 풀고 있는가, 아니면 proxy 문제를 풀고 있는가?
- 이 조치가 왜 의도한 결과를 만들 것인지 causal chain 이 충분히 닫혀 있는가?
- 가장 큰 실패는 어디서 발생하는가?
- 지금 방향을 유지한다면 어떤 디테일이 강화되어야 하는가?
- 더 단순한 대안, 더 완결적인 대안, 더 유연한 대안 중 무엇이 실제로 더 나은가?
- 추가보다 제거가 더 좋은 해법이라는 증거가 있는가?
- 성공해도 의미 있는 스코프인가, 너무 커서 실패하는 스코프는 아닌가?
- 지금 바로 handoff 할 만큼 입력, 완료 기준, 검증 방법이 닫혀 있는가?
- 이 방향을 지금 고정할 근거가 충분한가?

### 2a. Calibrate the intervention

압박 검토 후 권고 유형을 먼저 고릅니다.

- **Preserve and strengthen**: 방향은 맞지만 acceptance, 검증, sequencing, failure handling 이 약합니다.
- **Narrow**: 범위가 너무 커서 검증 지연, 조정 비용, 실패 확률이 커집니다.
- **Broaden or complete**: 범위가 너무 작아 성공해도 의미 있는 가치나 증거가 생기지 않습니다.
- **Pivot**: 문제 정의, causal chain, target user, leverage point 가 현재안과 다릅니다.
- **Pause**: missing input, protected area, 큰 비가역성, evidence conflict 때문에 진행 조건이 닫히지 않았습니다.

`Narrow`나 `Pause`를 고를 때는 위 결론을 만든 구체적 evidence 를 남깁니다.
그 evidence 가 없으면 현재 방향을 축소하지 말고 `Preserve and strengthen` 또는 `Broaden or complete`를 우선 검토합니다.

### 3. Target scope if needed

`scope-targeter`가 필요하면 스코프의 하한, 상한, 실제 승리 지점을 압박 검토합니다.

- scope-targeter 는 too small / too large / right-sized / winnable target 을 구분합니다.
- scope-targeter 는 축소뿐 아니라 유지, 확대, 완결성 보강도 제안할 수 있습니다.
- scope-targeter 결과는 최종 결론이 아니라 메인 판단이 스코프를 재조준하는 입력입니다.

### 4. Check readiness if needed

`readiness-reviewer`가 필요하면 실행 준비도와 handoff 가능성을 검토합니다.

- readiness-reviewer 는 required inputs, acceptance criteria, verification method, missing evidence 를 봅니다.
- readiness-reviewer 결과는 실행 영향과 `required_followups` 판단에 특히 중요합니다.

### 5. Check causal coverage if needed

`causal-coverage-reviewer`가 필요하면 문제, 개입, expected outcome 의 연결을 검토합니다.

- causal-coverage-reviewer 는 현재안의 claimed causal chain 을 재구성합니다.
- symptom, proxy, missing link, counter-cause, confounder 를 구분합니다.
- causal-coverage-reviewer 결과는 verdict, 대안 비교, 검증 followup 판단에 특히 중요합니다.

### 6. Deepen if needed

`thinker`가 필요하면 심층 사고 프레임으로 문제를 다시 모델링합니다.

- thinker 는 문제 재정의, 구조적 상호작용, second-order cost, inversion 관점을 확장합니다.
- thinker 결과는 최종 결론이 아니라 메인 판단을 깊게 만드는 입력입니다.

### 7. Explore if needed

`explorer`가 필요하면 현재안 밖의 대안 공간을 별도로 탐색합니다.

- explorer 는 현재안을 보완하지 않고, 현재안이 틀렸거나 불충분하다는 가정에서 출발합니다.
- explorer 는 다른 문제 정의, 원인 가설, 해결 원리, leverage point 를 제시합니다.
- explorer 결과는 최종 결론이 아니라 메인 판단이 종합할 발산 입력입니다.

### 8. Review if needed

`reviewer`가 필요하면 메인 판단과 thinker / explorer 결과를 독립 검토합니다.

- reviewer 는 새로운 분석기를 자처하지 않습니다.
- reviewer 는 이미 나온 판단과 심층 사고의 약점, 비약, 과신, 누락을 검토합니다.
- reviewer 는 현재 방향 강화, 더 단순한 대안, 더 안전한 대안, 더 완결적인 대안 중 무엇이 evidence 에 맞는지 제시할 수 있습니다.

### 9. Compare alternatives

최소 2개의 실행 가능한 다음 행동을 둡니다.

- **Current path**: 사용자가 지금 기울어 있는 방향
- **Same-direction strengthened path**: 현재 방향을 유지하되 부족한 디테일, 검증, sequencing, guardrail 을 보강하는 경로

필요할 때만 아래 대안을 추가합니다.

- **Leaner path**: 더 적은 가정, 더 적은 이동부품, 더 빠른 검증 경로
- **More complete path**: 현재 방향이 너무 작거나 증거가 약할 때, 의미 있는 결과를 만들 만큼 보강하는 경로
- **More flexible path**: 지금은 약간 덜 완결적이어도 나중 선택지를 더 열어두는 경로

`explorer`를 사용했다면 아래 비교도 반드시 포함합니다.

- **Divergent path**: 현재안과 다른 문제 정의 또는 해결 원리에서 출발하는 경로
- **Synthesis**: 현재안을 고칠지, 대안으로 전환할지, 둘을 더 높은 수준의 문제 정의로 합칠지에 대한 결론

`scope-targeter`를 사용했다면 아래 비교도 반드시 포함합니다.

- **Too small**: 성공해도 무가치하거나 증거가 약한 범위
- **Too large**: 실패 확률과 검증 지연이 큰 범위
- **Right-sized or winnable target**: 의미 있는 가치와 검증 가능성을 동시에 만족하는 지점

`readiness-reviewer`를 사용했다면 아래 판단도 반드시 포함합니다.

- **Handoff readiness**: ready, changes-needed, clarification-needed, escalation-needed 중 하나
- **Missing execution inputs**: 구현자가 새 결정을 내리지 않게 닫아야 할 입력

`causal-coverage-reviewer`를 사용했다면 아래 판단도 반드시 포함합니다.

- **Claimed causal chain**: 현재안이 암묵적으로 믿는 문제-개입-결과 연결
- **Weakest causal link**: verdict 를 가장 크게 바꾸는 missing link, proxy, counter-cause, confounder
- **Causal evidence path**: causal claim 을 확인하거나 반증할 수 있는 검증 또는 측정 경로

### 10. Recommend with a clear brake level

마지막에는 아래 중 하나로 판정합니다.

- `[PROCEED]`: 지금 방향이 충분히 타당함
- `[PROCEED WITH CHANGES]`: 핵심 수정 후 진행할 가치가 있음
- `[PAUSE]`: 중요한 가정, 리스크, 경직성이 정리되기 전까지 멈춰야 함
- `[STOP]`: 현재 방향은 문제 정의 또는 접근 자체를 다시 잡는 편이 나음

`[PROCEED]`나 `[PROCEED WITH CHANGES]`는 충분히 좋은 결론입니다.
브레이크 스킬이라고 해서 `[PAUSE]`나 `[STOP]`을 선호하지 않습니다.
`[PAUSE]`나 `[STOP]`은 구체적 blocking evidence 또는 높은 오판 비용이 있을 때만 사용합니다.

### 11. Write the scribe record

최종 응답 전에 루트 `decision-brake/<topic-slug>/` 아래에 Markdown 기록을 남깁니다.

- 메인 에이전트가 파일 생성을 책임집니다. reviewer 는 read-only 일 수 있으므로 파일을 직접 쓰게 하지 않습니다.
- 기록은 "서기" 관점의 의사결정 회의록이어야 하며, 최종 응답보다 더 보존성이 높아야 합니다.
- reviewer 를 사용했다면 reviewer 의 최종 정리와 남겨야 할 dissent 를 `Reviewer Digest`에 압축해 넣습니다.
- thinker / explorer / scope-targeter / readiness-reviewer / causal-coverage-reviewer 를 사용했다면 각 렌즈의 핵심 신호와 verdict 영향만 보존합니다.
- 기록에는 최소한 아래 항목을 포함합니다.
  - decision under review
  - framing: 선택지, 숨은 전제, 반례, 검증 방법, 실패 시나리오
  - lens notes
  - alternatives considered
  - reviewer digest, if reviewer was used
  - synthesis: verdict, decisive reasons, preserved dissent, required followups
  - final recommendation
  - source context: 읽은 파일, 사용자 입력, 주요 evidence refs
- 기록 파일을 썼다면 최종 응답에 해당 파일 경로를 짧게 알려줍니다.
- 사용자가 명시적으로 "파일 만들지 말고 답만 해줘"라고 하면 기록 생성을 생략할 수 있습니다.
- 현재 작업 디렉터리에 쓸 수 없거나 repo root 를 확정할 수 없으면 기록 생성을 건너뛰고 그 이유를 최종 응답에 명시합니다.

## Output Shape

응답은 아래 순서를 기본으로 합니다.

1. **Decision under review**
2. **What is probably wrong or weak**
3. **Risks and failure modes**
4. **Same-direction strengthening**
5. **Better alternatives**
6. **Recommendation**
7. **Brake level**

파일 기록을 생성한 경우, 응답 마지막에 `Scribe record: decision-brake/<topic-slug>/<YYYY-MM-DD-HHMM>-review.md`를 덧붙입니다.

여러 렌즈나 보조 에이전트를 사용했다면, 아래 human-facing 구조를 반드시 포함합니다. 단일 Base Decision Brake 만 수행한 짧은 리뷰에서는 생략할 수 있습니다.
여러 렌즈를 사용한 경우 `Lens Notes`에는 Base Decision Brake 와 사용한 모든 추가 렌즈를 포함합니다.

```text
Lens Notes
- lens: <Base Decision Brake | Thinker | Explorer | Reviewer | Scope Targeter | Readiness Reviewer | Causal Coverage Reviewer>
  signal: <렌즈가 포착한 핵심 신호>
  why_it_matters: <이 신호가 판단에 중요한 이유>
  impact_on_verdict: <verdict, scope, readiness, followup 에 준 영향>

Synthesis
- verdict: <[PROCEED] | [PROCEED WITH CHANGES] | [PAUSE] | [STOP]>
- decisive_reasons: <최종 판정을 결정한 이유, 최대 5개>
- preserved_dissent: <치명도 기준 또는 렌즈 간 충돌 기준으로 보존해야 하는 반론>
- required_followups: <진행 전 또는 진행 중 닫아야 할 입력, 증거, 수정사항>
```

`preserved_dissent`는 아래 둘 중 하나라도 해당하면 남깁니다.

- 최종 결론과 달라도, 맞으면 비용이 큰 반론
- 렌즈 간 판단이 실질적으로 충돌한 경우

반론의 출처만으로 `preserved_dissent`에 남기지는 않습니다.
보존할 반론이 없으면 생략하지 말고 `preserved_dissent: none`으로 명시합니다.

필요하면 마지막에 `Open questions`를 붙이되, 질문은 정말 방향을 바꾸는 것만 남깁니다.

## Companion Agents

이 저장소에는 아래 보조 에이전트를 둘 수 있습니다.

- `decision-brake-thinker`
- `decision-brake-explorer`
- `decision-brake-reviewer`
- `decision-brake-scope-targeter`
- `decision-brake-causal-coverage-reviewer`
- `decision-brake-readiness-reviewer`

사용 시 원칙은 다음과 같습니다.

- thinker 는 심층 사고를 맡습니다.
- explorer 는 현재안 밖의 근본 대안 탐색을 맡습니다.
- reviewer 는 메인 판단과 thinker / explorer 결과를 검토합니다.
- scope-targeter 는 스코프의 too small / too large / right-sized / winnable target 을 검토합니다.
- causal-coverage-reviewer 는 현재안의 문제-개입-결과 causal chain 과 weakest link 를 검토합니다.
- readiness-reviewer 는 handoff 가능성과 missing execution input 을 검토합니다.
- 메인 에이전트는 보조 에이전트 결과를 그대로 복붙하지 말고, 현재안과 대안의 충돌 지점, 공통 결론, 더 높은 수준의 문제 정의를 종합해 최종 권고문으로 압축합니다.

코드가 이미 작성된 뒤 구현 수준의 허점을 찾는 요청은 이 스킬보다 `implementation-brake`에 더 가깝습니다.

## Constraints

- 기본 목적은 리뷰와 권고이지, 구현이나 스캐폴딩이 아닙니다.
- 대상이 문서가 아니어도 사용할 수 있어야 합니다.
- 기본 모드를 과도하게 무겁게 만들지 않습니다.
- 렌즈가 많아져도 모든 렌즈를 의무 적용하지 않습니다.
- thinker 는 reviewer 를 대체하지 않습니다.
- explorer 는 thinker 나 reviewer 를 대체하지 않습니다.
- reviewer 는 thinker 를 대체하지 않습니다.
- scope-targeter, readiness-reviewer, causal-coverage-reviewer 는 최종 verdict 를 대체하지 않습니다.
- 범위 축소, 보류, 제거를 기본 권고로 쓰지 않습니다. 해당 권고에는 구체적 evidence 가 필요합니다.
- 방향성이 맞으면 같은 방향 안에서 디테일, acceptance, 검증, sequencing, guardrail 을 강화하는 결론을 우선 고려합니다.
- 비판만 하고 끝내지 말고, 항상 더 나은 대안 또는 더 나은 질문을 남깁니다.
- decision-brake 기록은 generated review artifact 입니다. canonical 실행 입력으로 승격하지 말고, 필요한 경우 별도 spec / requirement / task 문서로 변환합니다.
