# Bootstrap Mode Examples

Use these dry-run examples as the expected behavior reference when the repository state is not obvious.

## Example 1: `fresh-init`

### Input State

- empty repository
- no `.codex/`
- no `main/`
- no bootstrap marker

### Expected Mode

- `fresh-init`

### Expected Result Labels

- `created`: all required manifest files
- `skipped`: none
- `needs-merge`: none
- `template-updated`: none

### `DESIGN.md`

- not created unless the user explicitly asks for a UI-bearing project

## Example 2: `adopt-existing` with code and docs

### Input State

- existing source code or docs
- no bootstrap marker
- no template-managed `.codex` files

### Expected Mode

- `adopt-existing`

### Expected Result Labels

- `created`: missing bootstrap files only
- `skipped`: existing non-conflicting docs and code
- `needs-merge`: existing strategic docs that differ from template expectations
- `template-updated`: none

### `DESIGN.md`

- create only if UI signals exist or the user explicitly wants it

## Example 3: `adopt-existing` with partial `.codex`

### Input State

- `.codex/config.toml` exists
- one or more required bootstrap agents are missing
- no bootstrap marker

### Expected Mode

- `adopt-existing`

### Expected Result Labels

- `created`: missing template-managed bootstrap files
- `skipped`: preserved strategic docs
- `needs-merge`: conflicting strategic docs or config-related ambiguity surfaced for manual review
- `template-updated`: none

## Example 4: `upgrade-sync`

### Input State

- bootstrap marker exists
- template-managed files exist
- some template-managed files are behind the current template version

### Expected Mode

- `upgrade-sync`

### Expected Result Labels

- `created`: newly introduced template-managed files
- `skipped`: preserved strategic docs
- `needs-merge`: strategic docs that require user review
- `template-updated`: template-managed files eligible for safe update

### `DESIGN.md`

- preserve existing `DESIGN.md`
- do not auto-create it during upgrade unless the repository already opted into that doc
