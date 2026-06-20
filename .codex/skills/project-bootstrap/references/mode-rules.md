# Bootstrap Modes

## Precedence

Determine the mode in this order:

1. If a bootstrap marker exists, use `upgrade-sync`.
2. Else if the repo already contains code, docs, `main/`, or a partial `.codex` setup, use `adopt-existing`.
3. Else use `fresh-init`.

Never skip this precedence order.

## Definitions

- **Bootstrap marker**: the version marker stored in `.codex/docs/template_customization.md`
- **Partial `.codex` setup**: `.codex/config.toml` exists, or one or more required bootstrap agent registrations or template-managed files exist
- **Incomplete `.codex/config.toml`**: one or more required bootstrap agent registrations are missing from the config

## `fresh-init`

Use when the repository has no bootstrap marker and no meaningful existing project structure.

Typical signals:
- no `.codex/config.toml`
- no `main/`
- no established code or docs

Behavior:
- create the full default file set from the manifest
- prefer template defaults

## `adopt-existing`

Use when the repository has no bootstrap marker but already contains meaningful project material or a partial Codex setup.

Typical signals:
- source code exists
- top-level docs exist
- `main/` exists
- `.codex/config.toml` exists but is incomplete
- one or more template-managed files already exist without a bootstrap marker

Behavior:
- create missing files only
- preserve user-owned files by default
- report conflicts as `needs-merge`
- do not infer `upgrade-sync` without a marker

## `upgrade-sync`

Use when the repository was already bootstrapped and needs template updates.

Typical signals:
- bootstrap marker exists
- template-managed files already exist

Behavior:
- update template-managed files only
- never silently overwrite user-customized strategic docs
- keep a precise report of what changed

## Ambiguous Repo States

- If `main/` exists but no marker exists: `adopt-existing`
- If `.codex/config.toml` exists but the marker does not: `adopt-existing`
- If the marker exists but some required files are missing: `upgrade-sync`
- If strategic docs already exist in any mode: preserve them under `conflict-policy.md`
