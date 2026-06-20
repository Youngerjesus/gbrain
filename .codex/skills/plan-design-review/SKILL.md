---
name: plan-design-review
description: Reviews a UI-bearing plan from a product design perspective before implementation. Use when the user wants to critique screen structure, interaction quality, design specificity, or UX risks in a spec or plan discussion.
---

# Plan Design Review

이 스킬은 구현 전에 계획 문서의 UI/UX 빈칸을 찾고, 필요한 디자인 결정을 질문으로 잠그는 chat-only 리뷰 스킬입니다. 목표는 "좋아 보인다"는 승인보다, 구현자가 임의 판단으로 메워서는 안 되는 디자인 결정을 미리 드러내고 더 나은 기준으로 고정하는 것입니다.

이 스킬은 코드를 작성하지 않습니다. 프로젝트 문서를 자동 수정하지도 않습니다. 결과는 대화 안에서의 리뷰, 결정 사항 정리, 후속 스킬 추천, 그리고 오케스트레이터가 `progress.md`, `decisions.md`, `evidence.md`에 옮길 수 있는 구조화된 gate output 으로 남깁니다.

## Contract

이 스킬이 제대로 실행된 것으로 보려면 아래 계약을 만족해야 합니다.

- UI scope 여부를 먼저 판정하고, UI scope 가 없으면 `design gate status: not_required` 로 종료합니다.
- UI-bearing plan 이면 저장소 기준, 기존 UI 패턴, 관련 plan/spec/contract 문서를 근거로 디자인 리뷰를 수행합니다.
- 리뷰는 chat-only 로 남기되, 마지막에 반드시 `Gate Output` 블록을 포함합니다.
- `Gate Output` 은 오케스트레이터가 `progress.md`, `decisions.md`, `evidence.md`에 기록할 수 있을 만큼 structured 해야 합니다.
- unresolved decision 이 구현자가 임의로 정하면 화면 결과가 달라지는 사안이면 `design gate status: changes_required` 또는 `blocked` 로 표시합니다.
- 디자인 gate status 는 `passed`, `changes_required`, `blocked`, `not_required` 중 하나만 사용합니다.

## Trigger

다음 상황에서 이 스킬을 우선 고려합니다.

- 사용자가 "디자인 리뷰", "UI 관점에서 이 plan 봐줘", "구현 전에 화면 설계 점검", "spec 논의인데 UX도 리뷰해줘"라고 할 때
- `plan.md`, `design.md`, `spec.md`에는 방향이 있지만 실제 화면 경험이 충분히 잠기지 않았을 때
- 프론트엔드 변경이 포함된 기능에서 hierarchy, state, mobile, accessibility, trust 문제를 구현 전에 드러내야 할 때

다음 경우에는 다른 스킬이 더 적합합니다.

- 문제 정의와 제품 방향 자체가 흔들리면 `office-hours` 또는 `plan-ceo-review`
- 요구사항과 계약을 더 엄격하게 잠가야 하면 `requirement-clarifier` 또는 `spec-creator`
- 순수 backend, infra, API-only 작업이면 이 스킬은 적용 대상이 아닙니다

## Core Posture

- 이 스킬의 기준은 "예쁜 UI"가 아니라 "의도된 사용자 경험"입니다.
- 애매한 디자인 표현은 통과시키지 않습니다. "깔끔한 UI", "모던한 카드 레이아웃" 같은 문장은 결정이 아닙니다.
- 이 프로젝트의 North Star를 디자인 기준으로 번역합니다. 무속적이거나 올드한 감성은 금지하고, Toss나 애널리틱스 대시보드처럼 신뢰감 있고 논리적인 화면 경험을 요구합니다.
- 단방향 정적 리포트처럼 읽고 끝나는 구조를 경계합니다. 다음 행동이나 후속 대화로 자연스럽게 이어지는 UX인지 항상 확인합니다.
- 디자인 결정을 미루면 구현자가 임의 판단을 하게 됩니다. 그런 빈칸을 적극적으로 드러냅니다.

## Workflow

### 1. Repo Grounding

질문하기 전에 먼저 저장소와 관련 문서를 읽고 현재 상태를 고정합니다.

1. 루트 `AGENTS.md`와 필요 시 하위 `AGENTS.md`를 읽어 디자인 기준과 문서 규칙을 정렬합니다.
2. 관련 `design.md`, `plan.md`, `spec.md`, `contracts.md`, `tasks.md`를 찾아 현재 계획이 무엇을 만들려는지 파악합니다.
3. 관련 코드와 기존 UI를 탐색해 이미 존재하는 패턴, 재사용 가능한 컴포넌트, 이전 디자인 방향을 짧게 요약합니다.
4. 이미 해결된 문제를 다시 발명하지 말고, 기존 디자인 자산을 leverage 할 수 있는지 먼저 봅니다.

질문으로 해결할 수 있는 척하지 말고, 먼저 저장소에서 알 수 있는 사실을 찾습니다.

### 2. UI Scope Check

먼저 이 계획에 실제 UI 범위가 있는지 판단합니다.

- 새 화면, 기존 화면 변경, 상호작용 변경, 상태 표현, 디자인 시스템 변경 중 하나라도 있으면 디자인 리뷰 대상입니다.
- none 이면 "이 계획은 UI scope 가 없으므로 design review 대상이 아님"이라고 짧게 말하고 종료합니다.

### 3. Initial Rating

리뷰 시작 시 전체 디자인 완성도를 0-10으로 평가합니다.

- 왜 이 점수인지 한두 문장으로 설명합니다.
- 이 계획에서 10/10이 되려면 무엇이 더 명시되어야 하는지 설명합니다.
- biggest gaps 2~4개를 먼저 뽑아 이후 리뷰의 초점을 고정합니다.

### 4. Pass Review

아래 순서로 검토합니다.

1. Information Architecture
2. Interaction State Coverage
3. User Journey And Emotional Arc
4. AI Slop Risk And Design Specificity
5. Design System Alignment
6. Responsive And Accessibility
7. Unresolved Decisions

각 pass 에서 해야 할 일:

- 현재 점수를 말합니다.
- 왜 이 점수인지 설명합니다.
- obvious fix 는 바로 권고합니다.
- genuine trade-off 만 사용자에게 하나씩 질문합니다.
- 질문 응답 후에는 "이 결정이 잠기면 무엇이 좋아지는지"를 짧게 정리합니다.

### 5. Close-Out

마지막에는 아래를 압축해서 정리합니다.

- 현재 디자인 점수와 남은 gaps
- 지금 바로 구현에 들어가면 위험한 부분
- 이번 리뷰에서 잠긴 결정
- 일부러 defer 한 항목
- 다음에 이어질 가장 적절한 스킬 하나
- `progress.md`, `decisions.md`, `evidence.md`에 옮길 수 있는 `Gate Output`

## Review Dimensions

### 1. Information Architecture

다음을 봅니다.

- 사용자가 첫 화면에서 무엇을 먼저, 두 번째, 세 번째로 보게 되는가
- 핵심 행동이 뚜렷한가
- 화면이 문서처럼 늘어져 있는지, 아니면 의도된 흐름이 있는지

좋은 리뷰는 "화면이 복잡하다"가 아니라 "핵심 경고보다 장식성 카드가 먼저 보여 신뢰를 깎는다"처럼 말해야 합니다.

### 2. Interaction State Coverage

다음을 봅니다.

- loading, empty, error, success, partial 상태가 정의돼 있는가
- 첫 방문과 재방문, 데이터 없음과 실패가 구분돼 있는가
- 빈 상태가 단순한 "No items found" 수준으로 방치돼 있지 않은가

Empty state 는 기능입니다. 맥락, 다음 행동, 톤이 함께 정의돼야 합니다.

### 3. User Journey And Emotional Arc

다음을 봅니다.

- 첫 진입에서 사용자가 느끼는 감정이 무엇인가
- 결과 확인 시 확신, 신뢰, 긴장 완화, 다음 행동 유도 중 무엇을 설계하고 있는가
- 보고 끝나는지, 후속 정밀 채팅이나 다음 행동으로 자연스럽게 이어지는지

이 프로젝트에서는 "모호한 위로"보다 "논리적 설명과 행동 유도"가 중요합니다.

### 4. AI Slop Risk And Design Specificity

generic 한 설계를 경계합니다. 아래 패턴은 강하게 의심합니다.

- 3열 feature card grid
- centered-everything hero
- 목적 없는 gradient 와 blob 장식
- 카드가 실제 상호작용이 아닌데도 모든 영역을 카드로 쪼갠 구성
- "clean modern UI" 같은 추상 표현만 있고 실제 typography, spacing, hierarchy 결정이 없는 계획

모든 UI 설명은 가능하면 구체적이어야 합니다. 어떤 정보가 크고, 어떤 액션이 primary 인지, 어떤 화면이 trust 를 주는지까지 말해야 합니다.

### 5. Design System Alignment

다음을 봅니다.

- 기존 `design.md` 또는 현재 제품 UI 어휘와 맞는가
- 새로운 컴포넌트가 기존 vocabulary 를 깨지 않는가
- 이미 있는 패턴을 버리고 굳이 새 패턴을 만들고 있지 않은가

기존 패턴이 충분하면 재사용을 추천하고, 새 패턴이 필요하면 왜 필요한지 이유를 요구합니다.

### 6. Responsive And Accessibility

다음을 봅니다.

- 모바일이 단순 stack 처리로 끝나지 않는가
- tablet/desktop 에서 hierarchy 가 어떻게 바뀌는가
- keyboard navigation, screen reader labeling, contrast, touch target 이 계획에 포함돼 있는가

접근성은 추후 polish 가 아니라 plan 단계에서 명시돼야 합니다.

### 7. Unresolved Decisions

다음을 찾습니다.

- 구현자가 임의로 정하면 결과가 크게 달라지는 선택
- 상태 표현, empty state 톤, mobile navigation, CTA 우선순위, 정보 밀도 같은 핵심 결정
- defer 시 품질 저하나 재작업 비용이 큰 항목

각 미해결 결정은 "지금 안 정하면 구현에서 무엇이 망가지는지"까지 연결해서 설명합니다.

## Question Rules

- 질문은 반드시 한 번에 하나씩만 합니다.
- 사용자가 답해야만 plan 이 잠기는 진짜 trade-off 에만 질문합니다.
- obvious fix 면 질문하지 말고 권고안을 바로 말합니다.
- 각 질문은 다음 네 가지를 포함해야 합니다.
  - 무엇이 비어 있는지
  - 왜 이게 사용자 경험에 영향을 주는지
  - 추천안
  - 대안
- 질문은 가능한 한 평이한 언어로 씁니다. 구현 세부보다 사용자가 보게 될 경험으로 설명합니다.

## Output Format

Section headings must be emitted as standalone Markdown headings, not only as list items or nested pass labels, so section-present checks and handoff readers can locate them. For UI-bearing reviews, include these standalone headings when applicable: `## Information Architecture`, `## Interaction State Coverage`, `## User Journey And Emotional Arc`, `## AI Slop Risk And Design Specificity`, `## Design System Alignment`, `## Responsive And Accessibility`, and `## Unresolved Decisions`. Keep `## Core Problems` as the summary of the biggest gaps; do not hide the required pass headings only inside that section.

기본 출력은 대화 안에서 아래 heading 을 유지합니다.

1. `Current Score`
2. `Core Problems`
3. `Existing Assets`
4. `Decisions To Lock`
5. `Deferred Items`
6. `Recommended Next Step`
7. `Gate Output`

필요하면 pass 별로 아래 형식을 반복합니다.

- `Information Architecture: 4/10`
- 왜 낮은지
- 10/10 이 되려면 무엇이 필요한지
- 이번 턴에 잠글 질문 또는 권고안

### Gate Output Contract

If the review is UI-bearing and any unresolved decision would force the implementer to choose first viewport order, primary/CTA priority, empty/error/partial state behavior, mobile navigation, accessibility behavior, or trust evidence/recovery cues, set `design gate status` to `changes_required` unless the missing decision blocks scope selection entirely, in which case use `blocked`. The `progress.md note` and `evidence.md entry` must explicitly name the unresolved gap and next owner in structured language.

마지막 `Gate Output` 블록은 아래 필드를 포함합니다.

- `design gate status`: `passed`, `changes_required`, `blocked`, `not_required` 중 하나
- `progress.md note`: gate 결과, 현재 점수, 다음 owner 를 한두 문장으로 정리
- `decisions.md entries`: 이번 리뷰에서 잠긴 디자인 결정 목록. 없으면 `none`
- `evidence.md entry`: 읽은 source 문서, 핵심 finding, 남은 gap, 추천 후속 스킬
- `next owner`: `user`, `plan author`, `plan-eng-review`, `requirement-clarifier`, `spec-creator` 중 가장 가까운 owner

이 블록은 프로젝트 문서를 직접 수정하지 않는 chat-only 결과입니다. 다만 오케스트레이터가 gate 상태와 근거를 durable docs 에 옮길 수 있도록 기록 가능한 형태여야 합니다.

## Constraints

- 코드를 수정하지 않습니다.
- `plan_review.md`나 다른 프로젝트 문서를 자동으로 생성하거나 수정하지 않습니다.
- 외부 gstack runtime, telemetry, design binary, comparison board, 홈 디렉터리 artifact 에 의존하지 않습니다.
- mockup 생성이 전제되지 않습니다. 이 스킬은 텍스트 기반 계획 리뷰에 집중합니다.
- 구현처럼 보이는 상세 UI spec 을 지어내지 않습니다. 저장소와 사용자 응답으로 뒷받침되는 수준까지만 잠급니다.

## Anti-Patterns

- chat-only 라는 이유로 gate status, decisions, evidence 기록 재료를 남기지 않는 것
- `passed` 라고 하면서 구현자가 임의로 정해야 할 unresolved decision 을 숨기는 것
- UI scope 가 없는데 디자인 리뷰를 억지로 수행하는 것
- "깔끔한 UI", "모던한 화면" 같은 추상 표현을 결정으로 취급하는 것
- obvious fix 를 trade-off 질문으로 바꿔 사용자의 결정을 불필요하게 막는 것
- 기존 `DESIGN.md`나 제품 UI 패턴을 읽지 않고 일반론으로만 판단하는 것

## Handoff

리뷰가 끝나면 가장 적절한 다음 단계를 하나 추천합니다.

- 제품 방향 자체가 흔들리면 `office-hours` 또는 `plan-ceo-review`
- 요구사항과 계약을 더 엄격하게 고정해야 하면 `requirement-clarifier` 또는 `spec-creator`
- 구현 직전 구조, 경계, 테스트 전략 검토가 필요하면 `plan-eng-review`

추천은 이유와 함께 말합니다. 단순히 스킬 이름만 던지지 않습니다.
