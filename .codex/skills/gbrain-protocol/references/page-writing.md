# GBrain Page Writing Rules

Use this reference when creating or updating GBrain pages.

## Page Shape

A good GBrain page is durable compiled truth:

- one primary subject;
- concise title;
- concrete facts or preserved original wording;
- short paragraphs;
- deterministic links;
- explicit source citation.

Do not write assistant narration. The page should not say "I created this" or
"Here is a summary."

## Frontmatter

Use frontmatter fields that are factual and useful for retrieval:

```yaml
---
type: concept
title: Example Title
date: 2026-06-24
tags:
  - ai-agents
source_note: User-provided text
captured_via: codex
---
```

Avoid ambiguous frontmatter keys that GBrain may treat as page references unless
the value is a real page reference. Prefer `source_note` for plain provenance
text.

## Source Citation

Use exact dates:

```markdown
[Source: User, 2026-06-24]
```

For external material, cite the actual URL or source metadata if available. Do
not invent URLs.

## Preserving User Material

When the user provides a guide, framework, essay, or original thinking:

- preserve the user's actual wording when the wording carries insight;
- remove surrounding assistant chatter if it is not part of the intended note;
- keep headings and structure when useful;
- do not over-summarize away the user's terminology.

## Verification

After writing:

1. Read the page back.
2. Confirm the source id when the tool or CLI reports it.
3. Confirm slug and title/type.
4. Search for a distinctive phrase.
5. Fix unresolved or incorrect frontmatter/link extraction if the write result
   reports it.
