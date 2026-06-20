# Provider Strategy

Choose the lightest provider that can prove the behavior under test.

## Echo Provider

Use `echo` when evaluating known or logged output without calling a model. It is useful for checking assertion logic, static output, generated text, or recorded responses.

## Exec Provider

Use `exec:` when promptfoo should call a local script. Good uses:

- read files under test and assert required/forbidden instruction text
- run a local prompt renderer
- call a deterministic CLI or harness
- validate generated artifacts without external APIs

The script must write the evaluated output to stdout and return non-zero only for provider execution errors. Assertion failures belong in promptfoo assertions, not provider exit codes.

## Real LLM Provider

Use a real provider when the requested feedback is about model behavior that cannot be mechanically inferred from prompt text. Examples:

- answer quality
- refusal quality
- instruction hierarchy behavior
- tone and completeness
- reasoning quality

For LLM judge assertions, read `judge-rubrics.md` first and write pass/fail criteria before running.

## Blocked Provider

If no provider is available and deterministic checks cannot answer the feedback, mark promptfoo execution as blocked. Do not claim promptfoo-backed evidence from static review alone.
