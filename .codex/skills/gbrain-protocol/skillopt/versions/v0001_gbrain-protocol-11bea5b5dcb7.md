---
name: gbrain-protocol
description: "Use when Codex needs to operate GBrain memory: discover sources, search or read pages, write durable notes, verify saved memory, or teach another agent how to use GBrain memory safely."
---

# GBrain Protocol

Use GBrain as the user's durable memory system. This skill is for source-aware
memory work, not generic note taking.

## Contract

A GBrain task is complete only when:

- the target source is identified before source-sensitive reads or any write;
- memory answers are based on fetched GBrain content, not recall alone;
- named-source or user-supplied path lookups prove the source-local slug or
  source-root file inventory before summarizing results;
- writes use durable page shape with frontmatter and source citation;
- source-bound operations use a tool or CLI path that can actually target that
  source;
- every write is read back and checked with a distinctive phrase.

Do not assume AI Notes is the whole brain. Known source ids may include
`default`, `ai-notes`, `business-notes`, and `mindset-notes`, but live source
state is authoritative.

## Tool Selection

Prefer GBrain MCP tools when they are available and expose the source behavior
needed for the task. In this environment, commonly exposed tools include
`sources_list`, `sources_status`, `get_brain_identity`, `get_page`, `put_page`,
`recall`, and `extract_facts`.

Use CLI when MCP tools are missing, when the task needs keyword or semantic
search and MCP does not expose `search` or `query`, or when the operation must
be source-bound and the MCP call cannot select a source. MCP `put_page` may be
source-bound by the server context and may not expose `source_id`; if the user
named a specific source and the MCP surface cannot enforce it, use CLI with
`--source <source-id>`.

Use [CLI And MCP Usage](./references/cli-and-mcp.md) for exact commands and
tool selection details.

## Workflow

1. Discover sources with `sources_list` or `gbrain sources list`.
2. Resolve the target source from the user's wording, live source state, and
   current path patterns.
3. If the user names a source, path, slug, or exact document family, run the
   named-source lookup path below before using broad or federated results.
4. For topic discovery, use the broad-to-final retrieval path below: collect a
   wide candidate pool, filter and rerank it, open the strongest candidates,
   then return the final set, usually capped at 10 pages unless the user asks
   otherwise.
5. Treat semantic search ranking as recall assistance, not as proof that the
   relevant document set is complete.
6. Read relevant pages with `get_page` or `gbrain get`.
7. For writes, choose source, slug, type, and page shape before writing.
8. Write with `put_page` only when its source context is acceptable; otherwise
   write with `gbrain capture --file` or `gbrain put --source`.
9. Verify by reading the page back and searching for a distinctive phrase.

## Named Source And Path Lookup

Use this path whenever the user says "AI Notes", "business notes", names a
source id, provides a slug, provides a file path inside a source root, or says
you missed a specific document.

1. Confirm live source state with `gbrain sources list` or
   `gbrain sources current --source <source-id> --json`.
2. If the user supplied a source-root file path, derive the repo-like slug from
   that path and read it with `gbrain get <slug> --source <source-id>` before any broad summary.
3. Run source-bound candidate discovery, not only federated search:
   `gbrain search "<topic>" --source <source-id>`, `gbrain list --source
   <source-id>`, and when the source exposes a local root, `rg --files
   <source-root>` plus focused `rg -n` over markdown files.
4. Read every obvious title, slug, or path match before deciding the relevant
   set is complete. If semantic search and file inventory disagree, trust the
   source-bound `gbrain get` or source-root file inventory enough to inspect the
   candidate, then cite the page that was actually read.
   Use source-root `rg` only for candidate discovery; promote a result only
   after opening and inspecting the page or file.
5. In the answer, distinguish direct matches, related notes, and source or
   indexing gaps. Do not present broad/federated top hits as "the" result set
   for a named source.

## Broad-To-Final Retrieval

Use this path for "find documents about X", "look up notes on X", and cases
where the user expects recall rather than a single exact page.

1. Collect broadly from multiple signals: semantic search/query, source-bound
   search for named sources, `gbrain list --source <source-id>`, backlink-like
   references visible in fetched pages, and source-root filename/body inventory
   when a local source root is available.
2. Normalize candidates by source id and slug/path. Deduplicate aliases before
   ranking so one popular document does not crowd out adjacent notes.
3. Filter obvious non-matches using title, slug, tags/frontmatter, snippets, and
   user-specified source constraints. Keep borderline candidates for inspection
   when the user's wording is broad or ambiguous.
4. Rerank the remaining candidates by directness to the user's topic, source
   match, title/path evidence, snippet evidence, recency when relevant, and link
   proximity from already relevant pages.
5. Open and inspect enough top candidates with `gbrain get` or direct source
   file reads to confirm substance. Do not finalize a top result from title or snippet alone.
6. Return roughly the top 10 relevant pages by default. If fewer than 10 are actually relevant,
   say so; if more than 10 are strong matches, return the top 10 plus a short
   note about additional candidates.

## Source Selection

Use the source the user names after verifying it exists:

- "AI Notes" -> `ai-notes`
- "business notes" -> `business-notes`
- "mindset notes" -> `mindset-notes`
- Wealth OS, personal wealth context, decision checklists -> usually `default`

If the user asks a general memory question, start with the current/default or
federated behavior and narrow based on evidence. If multiple sources could be
right and the write target would matter, ask a concise clarification before
writing.

Use [Source Path Patterns](./references/source-path-patterns.md) before choosing
a slug prefix.

## Writing

Brain pages are durable compiled truth. They should have one primary subject,
concise frontmatter, dense useful content, deterministic links, and an explicit
source citation such as `[Source: User, 2026-06-24]`.

Preserve the user's original wording when the wording carries the insight. Do
not write assistant narration or raw chat dumps unless the user explicitly asks
for that artifact.

Use [Page Writing Rules](./references/page-writing.md) for frontmatter and page
quality requirements.

## Verification

After every write:

1. Read the saved page back.
2. Confirm the intended source id when the tool or CLI reports it.
3. Confirm slug, title, and type.
4. Search for a distinctive phrase from the saved content.
5. Fix write-result warnings about unresolved frontmatter, links, or timeline
   extraction before reporting success.

If source-specific verification cannot be performed with MCP, use CLI. If the
write succeeded but verification cannot run, report the verification gap.

## Output Format

When answering from GBrain, cite pages as `<source-id>:<slug>` when source id is
available. When saving memory, report the source, slug, and verification result
briefly.

## Anti-Patterns

- Writing to `ai-notes` just because the topic mentions AI.
- Treating source path snapshots as authoritative without live source discovery.
- Answering a named-source or exact-path lookup from federated search results
  without source-bound slug/path inventory and `gbrain get`.
- Using MCP `put_page` for a user-named source when the MCP call cannot enforce
  that source.
- Answering a memory question from model memory without GBrain retrieval.
- Claiming a write is complete without read-back plus distinctive phrase
  verification.
- Creating broad duplicate pages when an existing page should be updated.

## References

- [CLI And MCP Usage](./references/cli-and-mcp.md)
- [Page Writing Rules](./references/page-writing.md)
- [Source Path Patterns](./references/source-path-patterns.md)
