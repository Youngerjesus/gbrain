---
name: agent-creator
description: Guide for creating effective custom subagents in Codex. Use when a user wants a new specialized agent role for a repeatable task, domain, or review workflow.
---

# Agent Creator

This skill provides guidance for creating effective custom subagents in Codex.

reference @./create_custom_subagent.md

## Core Principles

1. Focus the agent on one clear job.
2. Make the description specific enough that Codex knows when to route to it.
3. Give the agent only the tools and permissions it needs.
4. Prefer role-specific `developer_instructions` over long parent prompts.

## Workflow

1. Clarify the agent's role, boundaries, and expected outputs.
2. Choose whether it should be read-only, implementation-focused, or mixed.
3. Create a dedicated TOML role file under `.codex/agents/`.
4. Register the role in `.codex/config.toml`.
5. Explain when the role should be invoked and when it should not.
