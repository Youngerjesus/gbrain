---
name: design-prompt-composer
description: Turn a user's rough mental image of a product screen into a complete prompt for a design-generation AI. Use when the user wants help prompting v0, Lovable, Framer, Figma AI, ChatGPT, Claude, or another AI that generates UI screens from text, especially when the user has a desired screen in mind but does not know how to express it.
---

# Design Prompt Composer

Convert an incomplete screen idea into a design-generation prompt that another AI can execute.

This skill is not a form for the user to fill out. The assistant should infer, organize, and fill the design prompt structure for the user. Ask only when a missing detail would materially change the screen.

## Core Job

Given a user's rough screen idea, produce:

1. A short interpretation of the intended screen.
2. Any critical assumptions made.
3. One polished final prompt ready to paste into a design-generation AI.

The final prompt should make the generated screen less likely to drift into a generic, decorative, or incorrectly structured UI.

## When To Ask Questions

Ask at most 1-2 short questions only if one of these is unknown and cannot be safely inferred:

- Who the primary user is.
- What the screen is for.
- What the user must judge or do on the screen.
- Whether the output target has a hard format, such as v0 React, Figma frame, mobile app, or web dashboard.

If the missing detail is not critical, assume a sensible default and state it briefly before the final prompt.

## Mental Canvas

Use this internal structure before writing the final prompt. Do not force the user to fill it manually.

```text
[User Raw Idea]
The user's rough description.

[Intent Interpretation]
What screen this is, who uses it, and in what situation.

[Core Judgment]
What the user must understand or decide first.

[Core Actions]
What the user must be able to do next.

[Information Hierarchy]
Primary information, secondary information, and low-priority information.

[Layout Contract]
Section order, column structure, fixed placement rules, and what must not be added.

[Component Contract]
Required navigation, filters, cards, charts, tables, lists, actions, status badges, forms, modals, and empty/error/loading states.

[Content Realism]
Realistic sample data, text length, status values, density, and edge-case content.

[Style Translation]
Translate references into concrete traits: density, spacing, typography, color behavior, component shape, motion, and interaction feel.

[Misinterpretations To Block]
Specific ways the design AI might produce the wrong thing.
```

## Prompt-Writing Rules

- Prefer product usefulness over visual spectacle.
- Define what the user needs to judge before listing components.
- Treat references as design traits, not names to imitate.
- Include realistic sample content when data density affects layout.
- Keep layout constraints explicit when the user has a clear mental structure.
- Let the design AI propose small usability improvements only when they do not violate the screen goal.
- Block common failure modes directly: generic dashboard, marketing page, arbitrary extra sections, card spam, fake placeholder content, decorative-only visuals, and low-density mockups.
- If the target AI is known, adapt the output wording to that tool. For example, v0 can receive component/layout instructions, while Figma AI may need clearer frame and visual-system language.

## Default Final Prompt Template

Use this as the base shape for most product screens.

```md
You are a senior product designer.
Design a polished, production-grade product screen. Prioritize user judgment and action over decoration.

[Goal]
Design {screen_name}.

[User And Situation]
The primary user is {user}.
They are using this screen in this situation: {situation}.
They need to complete these core tasks:
1. {task_1}
2. {task_2}
3. {task_3}

[Core Judgment]
The first thing the user must understand or decide is: {core_judgment}.
Make the visual hierarchy support this judgment before anything else.

[Information Hierarchy]
Primary information:
1. {primary_info_1}
2. {primary_info_2}
3. {primary_info_3}

Secondary information:
1. {secondary_info_1}
2. {secondary_info_2}

Low-priority information:
1. {low_priority_info_1}

[Layout Contract]
- {layout_rule_1}
- {layout_rule_2}
- {layout_rule_3}
- Do not add unrelated major sections.
- If you change the structure for usability, keep the same intent and explain the change briefly.

[Required Components]
- {component_1}
- {component_2}
- {component_3}

[Content And Data]
Use realistic product content, not lorem ipsum.
Representative data:
- {sample_data_1}
- {sample_data_2}
- {sample_data_3}

[States To Consider]
Design the default state first.
Also account for {important_state_1}, {important_state_2}, and {important_state_3} if relevant.

[Style Direction]
Follow {reference_a} for {specific_trait_a}.
Reference {reference_b} for {specific_trait_b}.
Avoid {style_to_avoid}.
Translate references into concrete UI traits: information density, spacing, typography, component shape, color behavior, and interaction feel.

[Constraints]
- Screen size: {screen_size}
- Responsive behavior: {responsive_behavior}
- Design system or components: {design_system}
- Accessibility: readable type, clear contrast, clear primary action, and non-color-only status meaning
- Must avoid: {forbidden_behavior}

[Success Criteria]
- The user can quickly make the core judgment.
- The primary actions are obvious and close to the relevant information.
- The information hierarchy and layout do not conflict.
- The screen feels like a real product surface with realistic content and density.

[Output]
Create one high-quality primary design.
Briefly explain the design intent.
Suggest at most 1-2 improvements only if they materially improve the screen.
```

## Dashboard Or Operations Screen Template

Use when the screen is a dashboard, admin tool, monitoring surface, analytics view, queue, control tower, or review console.

```md
Design a production-grade operations dashboard for {domain}.

The user is {operator_role}. Their job is to notice what needs attention, understand why, and take the next action.

Core judgment:
What requires attention right now, and how urgent is it?

Information priority:
1. Critical items requiring action
2. Current status and trend
3. Reason or contributing factors
4. Owner, timestamp, and next action
5. Historical or audit information

Layout contract:
- Top area: navigation, date range, scope selector, and primary filters.
- First section: 4 KPI/status cards summarizing the current operational state.
- Second section: 2-column layout.
  - Left 70%: main trend, funnel, or status chart.
  - Right 30%: action-required list sorted by urgency.
- Third section: full-width detailed table with filters, status badges, owner, timestamp, and row actions.
- Bottom area: logs, recent events, or secondary diagnostics.
- Do not turn this into a generic analytics dashboard. The screen must help the operator decide what to do next.

Use realistic dense data, including mixed statuses, long item names, timestamps, owners, and urgent/non-urgent examples.
```

## Form Or Workflow Screen Template

Use when the screen is for creating, editing, approving, onboarding, configuring, or completing a multi-step task.

```md
Design a product workflow screen for {workflow_name}.

The user is {user_role}. They need to complete {primary_action} with confidence and minimal backtracking.

Core judgment:
What information does the user need before they can safely submit, approve, or continue?

Information priority:
1. Current step and progress
2. Required inputs
3. Validation and risk warnings
4. Preview or consequence of the action
5. Secondary help or history

Layout contract:
- Keep the primary form or workflow path visually dominant.
- Place contextual guidance next to the fields or decisions it explains.
- Keep destructive or irreversible actions visually separated from normal progression.
- Show validation states with clear messages and not by color alone.
- Avoid decorative panels that compete with the form.

Use realistic field values, validation messages, disabled states, and at least one complex input example.
```

## Landing Or Marketing Screen Template

Use only when the user specifically asks for a landing page, website hero, or promotional product page.

```md
Design a focused landing page for {offer_or_product}.

The visitor is {audience}. They need to quickly understand what this is, why it matters, and what to do next.

Core judgment:
Is this product or offer relevant enough for me to take the primary action?

Information priority:
1. Product or offer identity
2. Concrete value proposition
3. Proof or credibility
4. Primary call to action
5. Supporting details

Layout contract:
- The first viewport must clearly show the product, offer, or brand.
- Use a real or generated image/media direction if the visual subject matters.
- Keep the primary CTA visible and specific.
- Avoid vague SaaS filler, generic gradient hero sections, and decorative-only feature cards.
```

## Output Format

For normal use, answer in this shape:

~~~md
**해석**
{one short paragraph}

**가정**
- {assumption_1}
- {assumption_2}

**최종 프롬프트**
```md
{ready_to_paste_prompt}
```
~~~

If the user asks only for the final prompt, omit the interpretation and assumptions unless needed to prevent misunderstanding.
