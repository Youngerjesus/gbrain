# Current GBrain Source Path Patterns

This reference records the user's current GBrain page path patterns. Use it to
choose a target source and slug prefix before writing.

Verify live state with `sources_list`, `gbrain sources list`, and, when needed,
`gbrain list --source <source-id>`. This snapshot is a routing aid, not an
authoritative inventory.

## `default`

Use for general concepts and Wealth OS pages unless the user names a more
specific source.

Observed paths:

- `concepts/*` - general concepts and playbooks.
- `concepts/ai-agents/*` - AI agent concepts and harness notes.
- `concepts/ai-blogs/*` - AI blog-derived concept pages.
- `concepts/ai-safety/*` - AI safety, evaluation, scheming, and CoT pages.
- `projects/*` - project Task Cards and compact working memory for long-running
  agent work.
- `wealth-os/00-index/*` - Wealth OS indexes and protocols.
- `wealth-os/10-principles/*` - wealth principles.
- `wealth-os/20-mental-models/*` - wealth mental models.
- `wealth-os/30-people/*` - people and lens pages.
- `wealth-os/40-decision-checklists/*` - decision checklists.
- `wealth-os/50-my-context/*` - user's current context, projects, routines,
  patterns, and vision.
- `wealth-os/60-daily-journal/*` - journal and check-in templates.
- `wealth-os/80-patterns/*` - observed or failure patterns.
- `wealth-os/90-raw-sources/*` - raw user notes feeding Wealth OS.

## `ai-notes`

Use only when the user says AI Notes or the material clearly belongs in the AI
notes collection.

Observed paths:

- `concepts/*` - AI concepts, frameworks, guides, and synthesized notes.
- `concepts/ai/*` - nested AI concept pages.
- `sources/articles/*` - article, blog, and source captures.
- `sources/youtube/ed-1in-entrepreneur/*` - YouTube-derived AI, business, or
  agent source notes from the existing collection.

Observed types:

- `concept`
- `article`
- `source`
- `youtube_video_source`
- `youtube_channel_ingest_manifest`

## `business-notes`

Use when the user asks for business notes, founder/business/entrepreneurship
video notes, or source material that belongs to that business note collection.

Observed paths:

- `sources/youtube/ed-1in-entrepreneur/*` - YouTube-derived business source
  notes.

## `mindset-notes`

Use when the user asks for mindset notes, personal growth/mental-model video
notes, or source material that belongs to that mindset collection.

Observed paths:

- `sources/youtube/ed-1in-entrepreneur/*` - YouTube-derived mindset source
  notes.

## Write Heuristics

- User says "AI Notes" -> source `ai-notes`.
- User says "business notes" or material is clearly business/entrepreneurship
  from the existing YouTube collection -> source `business-notes`.
- User says "mindset notes" or material is clearly mindset/personal growth from
  the existing YouTube collection -> source `mindset-notes`.
- Wealth OS, personal wealth principles, decision checklists, and user's wealth
  context -> source `default`, under `wealth-os/...`.
- General concepts not clearly tied to AI, business, or mindset can start in
  `default`, but verify current source and ask if ambiguous.
