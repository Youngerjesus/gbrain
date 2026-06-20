---
name: browse
description: Use gstack's persistent browser daemon for fast page QA, screenshots, interaction checks, local HTML rendering, and browser evidence when the user asks to browse, test, screenshot, dogfood, or verify a web flow.
---

# Browse

Use this skill when a task needs browser evidence through the gstack browse daemon. Do not run the Claude-generated gstack preamble. In Codex, use the terminal tools directly and ask the user in normal chat only when human browser handoff is required.

## Resolve The Binary

Resolve `B` before any command:

```bash
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
B=""
[ -n "${BROWSE_BIN:-}" ] && [ -x "$BROWSE_BIN" ] && B="$BROWSE_BIN"
[ -z "$B" ] && command -v browse >/dev/null 2>&1 && B="$(command -v browse)"
[ -z "$B" ] && [ -x "$ROOT/.codex/skills/gstack/browse/dist/browse" ] && B="$ROOT/.codex/skills/gstack/browse/dist/browse"
[ -z "$B" ] && [ -n "${GSTACK_HOME:-}" ] && [ -x "$GSTACK_HOME/browse/dist/browse" ] && B="$GSTACK_HOME/browse/dist/browse"
[ -z "$B" ] && [ -x "$HOME/.codex/skills/gstack/browse/dist/browse" ] && B="$HOME/.codex/skills/gstack/browse/dist/browse"
[ -n "$B" ] && echo "$B" || echo "NEEDS_SETUP"
```

If `NEEDS_SETUP`, tell the user the gstack browse binary is not built. If `GSTACK_HOME` points to a local gstack checkout, run `cd "$GSTACK_HOME" && ./setup` when setup is appropriate for the task.

## Core Workflow

Use `$B goto <url>` to navigate, `$B snapshot -i` to find interactable refs, `$B click @eN` and `$B fill @eN "value"` to act, `$B snapshot -D` to verify changes, `$B console` for JavaScript errors, and `$B network` for failed requests.

For screenshots, use `$B screenshot /tmp/file.png` or `$B snapshot -i -a -o /tmp/annotated.png`. When working inside Codex, show local PNG evidence with a Markdown image link in the final response when it helps the user.

For responsive checks, use `$B responsive /tmp/layout` or set exact viewports with `$B viewport 375x812`, `$B viewport 768x1024`, and `$B viewport 1440x900`.

For local HTML, prefer `$B goto file://<absolute-path>` when the file exists on disk. Use `$B load-html <file>` for generated HTML snippets.

## Rules

- Keep browser tests evidence-driven: screenshot, snapshot, console, network, or explicit state assertion.
- Re-run `snapshot` after navigation because `@e` refs become stale.
- For CAPTCHA, MFA, or complex auth after a few attempts, use `$B handoff "reason"`, tell the user what needs to be done, then resume with `$B resume` after they confirm.
- Do not install Puppeteer or another Chromium just to render HTML. Use browse when the daemon is available.
- If a Codex-native browser tool is already the task's chosen route, prefer the native tool and use this skill only when the user explicitly asks for gstack browse or the daemon capability matters.
