---
name: make-pdf
description: Generate polished PDFs, self-contained HTML, or DOCX files from Markdown using gstack make-pdf when the user asks to export, render, or turn Markdown into a finished document.
---

# Make PDF

Use this skill for Markdown-to-PDF or document export requests. Do not run the Claude-generated gstack preamble. Resolve the binary, generate the artifact, and verify the output exists.

## Resolve The Binary

```bash
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
P=""
[ -n "$MAKE_PDF_BIN" ] && [ -x "$MAKE_PDF_BIN" ] && P="$MAKE_PDF_BIN"
[ -z "$P" ] && command -v make-pdf >/dev/null 2>&1 && P="$(command -v make-pdf)"
[ -z "$P" ] && [ -x "$ROOT/.codex/skills/gstack/make-pdf/dist/pdf" ] && P="$ROOT/.codex/skills/gstack/make-pdf/dist/pdf"
[ -z "$P" ] && [ -n "${GSTACK_HOME:-}" ] && [ -x "$GSTACK_HOME/make-pdf/dist/pdf" ] && P="$GSTACK_HOME/make-pdf/dist/pdf"
[ -z "$P" ] && [ -x "$HOME/.codex/skills/gstack/make-pdf/dist/pdf" ] && P="$HOME/.codex/skills/gstack/make-pdf/dist/pdf"
[ -n "$P" ] && echo "$P" || echo "MAKE_PDF_NOT_AVAILABLE"
```

If the binary is missing, tell the user it needs a one-time gstack build. If `GSTACK_HOME` points to a local gstack checkout, run `cd "$GSTACK_HOME" && ./setup` when setup is appropriate.

## Common Commands

- `"$P" generate input.md` writes a default PDF path to stdout.
- `"$P" generate input.md output.pdf` writes to an explicit path.
- `"$P" generate --cover --toc --author "Name" --title "Title" input.md output.pdf` creates publication layout.
- `"$P" generate --watermark DRAFT input.md output.pdf` adds a draft watermark.
- `"$P" generate input.md output.html --to html` creates a self-contained HTML file.
- `"$P" generate input.md output.docx --to docx` creates a Word document.
- `"$P" preview input.md` opens HTML preview for fast iteration.

## Output Contract

On success, stdout is only the output path. Stderr contains progress. Capture stdout into a variable, then verify the file exists:

```bash
OUT="$("$P" generate input.md output.pdf)"
test -f "$OUT"
```

## Rules

- Use `--strict` for CI or contract-sensitive document generation.
- Remote images are blocked by default; use `--allow-network` only when the user wants network image fetching.
- For diagrams, keep top-level `mermaid` and `excalidraw` fences unindented so they render as images.
- Report the final artifact path to the user and mention any skipped verification.
