# Consultation Flow

Use this detailed flow when the user wants full design consultation rather than a quick answer.

## 1. Inspect Before Advising

Check for:

- existing `DESIGN.md`
- active design-system specs
- frontend token, theme, or global CSS files
- major UI surfaces already in use

If the repo already has a mature system, start by naming what exists and whether the user is asking to preserve, refine, or replace it.

## 2. Frame the Design Problem

State the product context plainly:

- what the product is
- who it is for
- what user trust problem the interface must solve
- which surfaces matter most right now, for example onboarding, report reading, dashboard, payment, or chat

## 3. Research If Needed

Use current references only when they will materially improve the recommendation.

Useful research outputs:

- common patterns users already expect
- weak category habits worth avoiding
- a few concrete interaction or visual references worth borrowing

Do not turn research into a mood-board dump. Synthesize it into design decisions.

## 4. Propose One Coherent Direction First

Default to one strong recommendation, not a menu of disconnected styles.

The proposal should cover:

- visual thesis in one sentence
- typography pairings and roles
- palette and token logic
- spacing density and radius scale
- layout principles
- motion principles
- report/dashboard-specific component guidance

## 5. Call Out Safe Choices and Risks

Separate:

- category-literate choices users expect
- deliberate differentiators that give the product a face

Explain what each risk buys and what it costs.

## 6. Convert Decisions Into SSOT

Once the direction is stable, write or update `DESIGN.md` with exact values and rules.

The document should let another engineer:

- implement tokens without guessing
- build new UI without inventing visual rules ad hoc
- review future UI work for compliance
