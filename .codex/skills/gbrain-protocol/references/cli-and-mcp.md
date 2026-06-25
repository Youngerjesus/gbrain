# GBrain CLI And MCP Usage

Use this reference when a task needs exact GBrain read/write commands or when
MCP tools are available but their source behavior must be kept explicit.

## Prefer MCP For Normal Brain Ops

When tools are available and their source behavior matches the task, prefer
GBrain MCP over shell commands:

- `sources_list`: list registered sources and page counts.
- `sources_status`: inspect clone/syncability state for a source.
- `get_brain_identity`: confirm the connected brain and counters.
- `get_page`: fetch a known slug.
- `put_page`: write a full markdown page when the MCP source context is right.
- `recall`: query hot-memory facts.
- `extract_facts`: extract personal-knowledge facts from a conversation turn.

Always inspect returned source metadata when present. Cite retrieved pages as
`<source-id>:<slug>` when possible.

## Source-Bound MCP Safety

MCP `put_page` does not expose `source_id` on every client surface. Treat it as
safe only when the server context is already the intended source or when the
write target is not source-sensitive.

Use CLI instead when the user names a source and MCP cannot enforce that source:

```bash
gbrain capture --file <file.md> --source <source-id> --slug <slug> --type <type>
gbrain put <slug> --source <source-id> < file.md
```

## Use CLI When MCP Is Missing

Source discovery:

```bash
gbrain sources list
gbrain sources current --json
gbrain sources current --source <source-id> --json
```

Reads:

```bash
gbrain search "keyword or entity"
gbrain query "natural language question"
gbrain get <slug>
gbrain list --type <type>
```

Reads with explicit source:

```bash
gbrain search "keyword or entity" --source <source-id>
gbrain query "natural language question" --source <source-id>
gbrain get <slug> --source <source-id>
gbrain list --source <source-id>
```

Named source or path lookup:

```bash
gbrain sources list
gbrain sources current --source <source-id> --json
gbrain get <slug-derived-from-source-root-path> --source <source-id>
gbrain search "keyword or entity" --source <source-id>
gbrain list --source <source-id>
rg --files <source-root>
rg -n --glob '*.md' -i "keyword|related phrase" <source-root>
```

If the user gives a file path inside a source root, derive the slug from the
path relative to that root and read it with source-bound `gbrain get` before
summarizing semantic search results. Use source-root `rg` only for candidate
discovery; promote a candidate to an answer by reading the GBrain page or the
source file directly and citing the page/source id.

Broad-to-final retrieval flow:

```bash
gbrain search "broad topic"
gbrain query "natural language version of broad topic"
gbrain search "broad topic" --source <source-id>
gbrain list --source <source-id>
rg --files <source-root>
rg -n --glob '*.md' -i "topic|synonym|related phrase" <source-root>
gbrain get <candidate-slug> --source <source-id>
```

Use the broad commands to build a candidate pool, then filter and rerank by
source, title/path, tags/frontmatter, snippets, links, and user constraints.
Open the strongest candidates before final ranking, then return the final top 10 relevant pages by default.

Writes:

```bash
gbrain capture --file <file.md> --source <source-id> --slug <slug> --type <type>
gbrain put <slug> --source <source-id> < file.md
```

Verification:

```bash
gbrain get <slug> --source <source-id>
gbrain search "<distinctive saved phrase>" --source <source-id>
```

## Source Selection

Use the source the user named. If the user did not name a source, start with the
resolved/default source or broad search. Do not force `ai-notes` unless the user
asked for AI Notes or the content clearly belongs in that collection.

Use `ai-notes` for the user's AI Notes collection after verifying it exists:

```bash
gbrain sources current --source ai-notes --json
```

## Local-Only/Admin Operations

Use CLI for operations that touch local files, embeddings, extraction,
maintenance, or setup:

```bash
gbrain sync --source <source-id>
gbrain embed --stale --source <source-id>
gbrain extract links
gbrain extract timeline
gbrain doctor
gbrain dream
gbrain autopilot
gbrain init
```

Do not route local-only/admin operations through remote MCP.

## PGLite Owner Safety

If `gbrain serve` already owns a PGLite brain, do not directly instantiate the
PGLite engine from custom code. Prefer MCP tools or normal CLI commands. Direct
engine opens can stall on the file lock.
