# Creating a Custom Codex Agent

## File Layout

Create two pieces:

1. `.codex/agents/<agent-name>.toml`
2. `.codex/config.toml` registration under `[agents.<agent-name>]`

## Naming

- Use lowercase hyphenated ids such as `security-reviewer` or `docs-editor`.
- Keep the name tied to one responsibility.

## Minimal TOML Template

```toml
model = "gpt-5.4"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = '''
You are a focused reviewer for <domain>.

Responsibilities:
- ...

Constraints:
- ...
'''
```

## Registration Template

```toml
[agents.<agent-name>]
description = "One-sentence routing hint that says what this agent does and when to use it."
config_file = "agents/<agent-name>.toml"
```

## Design Checklist

- The description says when to use the role, not just what it is.
- The instructions define what the agent must avoid.
- The sandbox mode matches the job.
- The output format is explicit when reviews or reports are expected.
- The role does not duplicate an existing built-in or project role without a clear reason.
