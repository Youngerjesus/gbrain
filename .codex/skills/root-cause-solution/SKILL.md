---
name: root-cause-solution
description: Use after a root cause or strong causal model is identified and the user wants a real solution, alternative interventions, dialectical synthesis, and an execution-ready plan before implementation.
---

# Root Cause Solution

이 스킬은 근본 원인 조사 이후, 실제 해결책을 설계하는 전용 스킬입니다.
목적은 "무엇이 원인인가"를 다시 조사하는 것이 아니라, 밝혀진 원인을 어떤 개입 지점에서 어떻게 해결해야 가장 실제적인지 판단하는 것입니다.

핵심 역할은 아래입니다.

- 근본 원인과 증거 품질을 고정합니다.
- 여러 개입 지점과 해결 원리를 비교합니다.
- 제1원칙, 역발상, 시스템 사고, second-order 사고를 사용해 대안을 깊게 봅니다.
- 충돌하는 대안을 변증법적으로 종합합니다.
- 최종 해결책이 원인 메커니즘을 닫는지 리뷰합니다.
- 구현, spec 작성, 또는 운영 실행으로 넘길 수 있는 handoff 를 만듭니다.

## Trigger

다음 요청에서 사용합니다.

- "근본 원인을 바탕으로 해결책을 찾아줘"
- "원인은 알았는데 실제 솔루션을 설계해줘"
- "대안을 탐색하고 종합해서 해결책을 내줘"
- "이 문제를 근본적으로 해결하는 방법을 생각해줘"
- "증상 패치 말고 재발하지 않는 해결책을 찾아줘"
- "first principles / inversion / systems thinking 으로 해결안을 찾아줘"

다음 경우에는 다른 스킬이 우선입니다.

- 원인 자체가 아직 불명확하면 `systematic-debugging`
- 실행 전 방향성 자체를 압박 검토하려면 `decision-brake`
- 이미 작성된 구현을 ship 전에 검토하려면 `implementation-brake`
- 바로 테스트 주도 구현이 가능한 좁은 수정이면 `tdd-workflow`
- 요구사항/spec 으로 고정해야 하는 제품 기능이면 `spec-creator` 또는 `requirement-clarifier`

## Core Posture

- 해결책은 원인 메커니즘을 닫아야 합니다. 증상을 덮는 패치는 실패입니다.
- "더 큰 설계"보다 "가장 작은 durable intervention"을 우선합니다.
- 좋은 해결책은 무엇을 고칠지뿐 아니라 무엇을 고치지 않을지도 정합니다.
- root cause evidence 가 약하면 해결책을 꾸미지 말고 조사로 되돌립니다.
- 깊은 사고법은 목적이 아니라 도구입니다. 출력은 실행 가능해야 합니다.

## Evidence Gate

먼저 원인 증거를 판정합니다.

- `strong`: 재현, 로그, 비교, 테스트, trace, contract evidence 로 원인 메커니즘이 설명됨
- `medium`: 가장 유력한 causal model 이 있고 반대 가설 일부가 배제됨
- `weak`: 원인 후보는 있으나 증거가 부족하거나 경쟁 가설이 남아 있음

`weak`이면 기본 verdict 는 `[NEEDS MORE EVIDENCE]`입니다.
이 경우 해결책을 확정하지 말고 `systematic-debugging`으로 돌아갈 다음 관찰 또는 실험을 제시합니다.

## Workflow

### 1. Ground the causal model

아래를 짧게 고정합니다.

- symptom
- expected behavior
- root cause or causal model
- evidence quality
- affected users, systems, data, policies, or workflows
- constraints and non-negotiables

### 2. Map intervention points

최소 3개 이상의 개입 지점을 검토합니다.

- local patch
- invariant hardening
- boundary contract change
- state model or data model change
- data repair or migration
- workflow/process change
- observability or alerting change
- rollback, mitigation, or staged rollout
- larger architecture correction

모든 지점을 길게 설명하지 말고, 실제로 plausible 한 지점만 비교합니다.

### 3. Generate solution candidates

기본적으로 아래 후보를 만듭니다.

- **Minimal durable fix**: 가장 작은 변경으로 causal mechanism 을 닫는 해결책
- **Systemic fix**: 재발 경로와 유사 경로까지 줄이는 해결책
- **Subtraction fix**: 복잡성, 상태, feature, branch, process 를 제거하는 해결책
- **Divergent fix**: 현재 사고방식과 다른 개입 지점에서 출발하는 해결책

### 4. Deepen the candidates

필요한 사고법만 사용합니다.

- First principles: 반드시 지켜야 하는 원리, invariant, contract 는 무엇인가
- Inversion: 이 해결책이 실패하게 만들려면 무엇이 필요할까
- Systems thinking: 다른 컴포넌트, 사용자, 운영 흐름에 어떤 feedback 이 생기는가
- Second-order thinking: 단기 해결 뒤 장기 비용, 유지보수, 재발 패턴은 무엇인가

### 5. Synthesize dialectically

후보를 단순 투표하지 않습니다.

- 현재 가장 직관적인 해결책의 강점
- 반대 또는 divergent 해결책의 강점
- 둘이 충돌하는 지점
- 더 높은 수준에서 합칠 수 있는 해결 원리
- 최종 선택과 버린 선택

### 6. Review the solution

최종 해결책을 아래 기준으로 압박 검토합니다.

- 원인 메커니즘을 실제로 닫는가
- 증상 마스킹이 아닌가
- 과도한 범위 확장이 아닌가
- regression proof 가 가능한가
- failure, rollback, staged rollout 경로가 있는가
- 구현자가 임의 결정을 내려야 하는 빈칸이 남아 있지 않은가

### 7. Hand off

해결책을 직접 구현하지 않습니다.
다음 스킬 또는 작업으로 넘길 수 있게 handoff 를 만듭니다.

- 좁은 코드 수정: `tdd-workflow`
- 설계 영향이 큰 수정: `plan-eng-review`
- 상태 조합, 복구, edge path 가 복잡한 수정: `scenario-brake`
- 제품 요구사항 또는 계약 문서화: `spec-creator`
- 높은 위험, 정책, 보안, 데이터 손실 가능성: human escalation

## Companion Agents

기본 실행은 메인 에이전트가 수행합니다.
아래 조건에서는 보조 에이전트를 사용합니다.

### Root Cause Solution Thinker

사용 조건:

- causal model 이 복합적입니다.
- 여러 시스템의 상호작용이나 second-order cost 가 중요합니다.
- 사용자가 깊은 사고, 제1원칙, 역발상, 시스템 사고를 명시적으로 요청합니다.

역할:

- 원인과 해결 원리를 더 근본 단위로 재모델링합니다.
- 최종 결론이 아니라 synthesis 재료를 제공합니다.

### Root Cause Solution Explorer

사용 조건:

- 현재 해결책 후보가 너무 좁습니다.
- 사용자가 다른 대안, 다각도 탐색, 발산 사고를 명시적으로 요청합니다.
- 다른 개입 지점에서 더 나은 해결책이 나올 가능성이 있습니다.

역할:

- local patch 밖의 alternative intervention point 를 탐색합니다.
- subtraction, process, policy, data, architecture, observability 해결책을 비교합니다.

### Root Cause Solution Reviewer

사용 조건:

- 선택한 해결책의 비용, 위험, 되돌리기 어려움이 큽니다.
- 최종 해결책이 실제 root cause 를 닫는지 독립 검토가 필요합니다.
- thinker/explorer 를 사용한 뒤 synthesis 품질을 확인해야 합니다.

역할:

- 최종 해결책의 허점, 과신, symptom masking, test gap 을 압박 검토합니다.
- 더 작은 durable intervention 이 가능한지 확인합니다.

## Output Shape

응답은 아래 순서를 기본으로 합니다.

1. **Problem and causal model**
2. **Evidence quality**
3. **Solution candidates**
4. **Intervention point analysis**
5. **Dialectical synthesis**
6. **Recommended solution**
7. **Execution plan**
8. **Verification plan**
9. **Rejected alternatives**
10. **Residual risks**

판정은 반드시 아래 중 하나로 끝냅니다.

- `[IMPLEMENT]`: 해결책이 명확하고 바로 구현 가능한 상태
- `[IMPLEMENT WITH GUARDS]`: 구현하되 테스트, rollback, staged rollout, monitoring guard 가 필요함
- `[NEEDS MORE EVIDENCE]`: root cause 또는 제약 증거가 부족함
- `[ESCALATE]`: 높은 위험, 정책, 보안, 데이터 손실, irreversible decision 이 있음
- `[DO NOT IMPLEMENT]`: 제안된 해결책이 실제 원인을 닫지 못하거나 더 큰 실패를 만듦

## Constraints

- root cause discovery 를 대신하지 않습니다.
- 구현을 직접 수행하지 않습니다.
- 모든 문제를 architecture redesign 으로 키우지 않습니다.
- companion agents 를 routine fix 에 강제하지 않습니다.
- output 은 사고 과정 나열이 아니라 실행 가능한 해결책이어야 합니다.
