# Handoff: Route `gbrain think` Synthesis Through Codex CLI

## Goal

Explore and implement an option for `gbrain think` to use the local Codex CLI as its synthesis LLM instead of calling a provider API directly through the current GBrain AI gateway.

The motivating use case is cost and account routing: today `gbrain think` can call Anthropic through `ANTHROPIC_API_KEY`; the operator wants the ability to route the synthesis step through their existing Codex CLI session/account instead.

## Current Behavior Observed

`gbrain think "<question>" --json` currently:

1. Runs `runGather()`.
2. Retrieves page hits through `hybridSearch()`.
3. Retrieves takes through `engine.searchTakes()` and optionally vector takes.
4. Traverses graph only when an `anchor` is supplied.
5. Renders gathered evidence into `<pages>`, `<takes>`, and optional `<graph>` blocks.
6. Calls a `ThinkLLMClient.create(...)`.
7. Parses the LLM output as `ThinkResponse` JSON.
8. Resolves citations from the structured `citations` field, falling back to inline `[slug]` markers when needed.

Important code locations:

- `src/core/think/gather.ts`
  - `runGather()` runs the four retrieval streams.
  - `renderPagesBlock(pages, excerptLen = 600)` sends only up to 600 chars per page hit into the prompt.
- `src/core/think/prompt.ts`
  - `buildThinkSystemPrompt()` defines the JSON schema and citation rules.
  - `buildThinkUserMessage()` wraps evidence into `<pages>`, `<takes>`, and `<graph>`.
- `src/core/think/index.ts`
  - `runThink()` orchestrates gather, prompt assembly, LLM call, JSON parsing, and citation resolution.
  - `tryBuildGatewayClient()` adapts `gateway.chat()` into the Anthropic-shaped `ThinkLLMClient`.
- `src/core/think/cite-render.ts`
  - `resolveCitations()` prefers structured citations, then falls back to regex parsing.
- `src/core/model-config.ts`
  - `models.think` falls through to the `deep` tier and currently defaults to `anthropic:claude-opus-4-7`.

Recent observed output for `gbrain think "ED 1인 기업가 AI 시대 인간의 포지셔닝" --json`:

- `pagesGathered: 40`
- `takesGathered: 0`
- `graphHits: 0`
- `modelUsed: anthropic:claude-opus-4-7`
- warnings included `LLM_OUTPUT_NOT_JSON` and `CITATIONS_REGEX_FALLBACK`

The environment had `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` present as env vars, while `~/.gbrain/config.json` did not store those keys. Do not log or persist key values.

## Codex CLI Surface Observed

`codex` is available on PATH in this local environment.

Relevant non-interactive command:

```bash
codex exec [OPTIONS] [PROMPT]
```

Useful options from `codex exec --help`:

- `-m, --model <MODEL>`
- `--output-schema <FILE>`
- `-o, --output-last-message <FILE>`
- `--json`
- `--ephemeral`
- `--ignore-rules`
- `--sandbox read-only|workspace-write|danger-full-access`
- `--ask-for-approval never`
- `-C, --cd <DIR>`

For this use case, the Codex invocation should be constrained to synthesis only:

```bash
codex exec \
  --ephemeral \
  --sandbox read-only \
  --ask-for-approval never \
  --output-schema /tmp/gbrain-think-response.schema.json \
  --output-last-message /tmp/gbrain-think-response.json \
  -
```

The prompt should be supplied over stdin and should combine the current GBrain think system prompt and user message. The implementation should read the last-message file or parse JSONL events, not scrape colored terminal output.

## Recommended Implementation Approach

Start with a narrow, opt-in `think` adapter rather than adding a full gateway provider.

Reasoning:

- `think` already has a test seam: `ThinkLLMClient`.
- `tryBuildGatewayClient()` is the only production construction path for synthesis.
- A narrow adapter avoids touching embeddings, rerankers, subagents, extraction, and unrelated AI gateway consumers.
- If the experiment works, a later task can promote it into a first-class gateway provider.

Suggested config shape:

```bash
gbrain config set models.think codex-cli:gpt-5
```

or:

```bash
gbrain config set think.provider codex-cli
gbrain config set think.codex_model gpt-5
```

The first option is ergonomically closer to existing model routing, but `model-config` / `probeChatModel()` currently expects known gateway providers. The implementation likely needs a special-case before gateway probing:

```ts
if (modelStr.startsWith('codex-cli:')) {
  return buildCodexCliThinkClient(modelStr);
}
```

Place this in or near `tryBuildGatewayClient()` in `src/core/think/index.ts`, or extract a sibling module such as:

```txt
src/core/think/codex-cli-client.ts
```

The adapter should implement:

```ts
interface ThinkLLMClient {
  create(params: Anthropic.MessageCreateParamsNonStreaming): Promise<Anthropic.Message>;
}
```

It can convert the Anthropic-shaped request into a single Codex prompt:

```text
SYSTEM:
<params.system>

USER:
<params.messages rendered as text>

Return only JSON matching the supplied schema. No markdown fence.
```

Then convert Codex's final text back to the minimal Anthropic-message shape expected by `runThink()`:

```ts
{
  id: `codex-cli-${Date.now()}`,
  type: 'message',
  role: 'assistant',
  model: modelStr,
  content: [{ type: 'text', text: finalText }],
  stop_reason: 'end_turn',
  stop_sequence: null,
  usage: { input_tokens: 0, output_tokens: 0 },
}
```

## JSON Schema

Codex should be constrained with an output schema matching `ThinkResponse`:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["answer", "citations", "gaps"],
  "properties": {
    "answer": { "type": "string" },
    "citations": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["page_slug", "row_num"],
        "properties": {
          "page_slug": { "type": "string" },
          "row_num": { "type": ["integer", "null"] },
          "citation_index": { "type": "integer" }
        }
      }
    },
    "gaps": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

Implementation detail: write this schema to a temp file for the Codex CLI call, or check in a reusable schema if that matches project conventions.

## Risks And Design Questions

1. **Nested agent behavior**
   Codex CLI is an agent, not a raw chat completion endpoint. It may try to inspect files or run commands unless strongly constrained. Use `--sandbox read-only`, `--ask-for-approval never`, `--ephemeral`, and a prompt that forbids tool use for synthesis.

2. **Latency**
   `codex exec` process startup plus agent runtime will likely be slower than a direct provider call. Add a timeout and a clear error path.

3. **Output reliability**
   Direct Anthropic calls already produced one malformed JSON result in the observed run. Codex CLI should use `--output-schema` if possible, and the existing `tryParseJSON()` / citation fallback should remain in place.

4. **Cost is not necessarily zero**
   Codex CLI may use the operator's Codex/OpenAI account or local provider, depending on their Codex configuration. The implementation should document that this changes the billing surface; it does not guarantee free inference.

5. **Model config integration**
   The cleanest UX is `models.think=codex-cli:<model>`, but the current model probe path may reject unknown providers. Add a narrow special-case or extend the model registry intentionally.

6. **Security and privacy**
   The prompt includes retrieved brain excerpts. This is already true for provider calls, but routing through Codex changes the processor. Document it.

7. **MCP / remote behavior**
   Confirm whether remote `think` should allow `codex-cli` provider. It may only make sense for trusted local CLI callers, because it shells out to a local executable.

## Suggested Test Plan

Unit tests:

- Add a test for `buildCodexCliThinkClient()` using a fake `spawn`/runner.
- Verify it passes system + user message content to Codex.
- Verify it reads the final response and returns an Anthropic-shaped message.
- Verify non-zero exit, timeout, and invalid JSON behavior.

Integration-ish test:

- Stub `runThink()` with a fake Codex client and confirm citations resolve.
- Confirm `models.think=codex-cli:test-model` routes to the Codex adapter, not gateway probing.

Manual smoke:

```bash
gbrain config set models.think codex-cli:gpt-5
gbrain think "ED 1인 기업가 AI 시대 인간의 포지셔닝" --json
```

Expected:

- `modelUsed` is `codex-cli:gpt-5` or the chosen Codex model string.
- `pagesGathered` remains populated.
- `answer` is valid JSON-parsed synthesis.
- `citations` are present without needing `CITATIONS_REGEX_FALLBACK` ideally.

Rollback:

```bash
gbrain config set models.think opus
```

or delete the config key if the project has a config unset command.

## Non-Goals For First Pass

- Do not replace the whole GBrain AI gateway.
- Do not route embeddings through Codex CLI.
- Do not route `takes extract`, `dream`, `subagent`, or other LLM consumers through Codex.
- Do not remove Anthropic/OpenAI gateway support.
- Do not persist API keys or Codex credentials in repo files.

## Open Questions For The Implementer

- Should `codex-cli` be local-CLI-only, or also allowed from MCP trusted local calls?
- Which Codex model should be the default when the model suffix is omitted?
- Should the adapter use `--ignore-rules` to reduce prompt pollution, or should it allow Codex's normal instruction stack?
- Should `--output-schema` be required, or should the implementation tolerate older Codex CLI versions without it?
- Where should temp schema/output files live, and how should they be cleaned up on timeout?
