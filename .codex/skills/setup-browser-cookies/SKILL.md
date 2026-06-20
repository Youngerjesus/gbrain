---
name: setup-browser-cookies
description: Import logged-in Chromium browser cookies into the gstack browse daemon when the user asks to reuse an authenticated browser session or set up browser cookies for browse.
---

# Setup Browser Cookies

Use this skill to make the gstack browse daemon share selected logged-in sessions from a real Chromium browser. Do not expose cookie values.

## Resolve Browse

Resolve `B` the same way as the `browse` skill:

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

If the binary is missing and `GSTACK_HOME` points to a local gstack checkout, run `cd "$GSTACK_HOME" && ./setup` when setup is appropriate.

## Workflow

1. Check whether browse is already attached to the user's real browser:
   ```bash
   "$B" status 2>/dev/null | rg "Mode: cdp" && echo "CDP_MODE=true" || echo "CDP_MODE=false"
   ```
   If true, tell the user cookie import is unnecessary.
2. Open the picker with `"$B" cookie-import-browser`.
3. Tell the user the picker is open and ask them to choose the domains to import, then report back.
4. If the user gave a domain directly, skip the picker and run `"$B" cookie-import-browser comet --domain <domain>` unless they specify another browser.
5. Verify with `"$B" cookies` and summarize domains/counts only.

## Notes

- macOS may show a Keychain prompt on first import for a browser.
- The picker UI displays domains and counts, not cookie values.
- Imported cookies persist in the browse session immediately.
