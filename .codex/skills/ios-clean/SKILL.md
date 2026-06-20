---
name: ios-clean
description: Remove the gstack iOS DebugBridge from an app when the user asks to clean the bridge, remove DebugBridge, strip QA instrumentation, or prepare for a release/security cleanup.
---

# iOS Clean

Use this as a guided, reversible cleanup flow for gstack DebugBridge. It is not the primary safety mechanism; Debug-only package wiring and Release verification remain the safety-critical checks.

## Inventory

Find:

- `import DebugBridge`
- `#if DEBUG` blocks that start `DebugBridgeManager` or `StateServer`
- generated `StateAccessor.swift` files or auto-generated accessor headers
- `@Snapshotable` wrappers
- DebugBridge package entries and target dependencies in `Package.swift`

Show the user the file list and scope before removing anything unless they explicitly asked for automatic cleanup.

## Removal

Remove only approved DebugBridge-owned pieces:

1. DebugBridge package dependency and target references.
2. Debug-only app entry wiring.
3. `@Snapshotable` wrappers that exist only for the bridge.
4. Generated accessor files.
5. Device temp token best-effort if the device is connected.

Do not touch app business logic, view models, production code outside `#if DEBUG`, or unrelated test infrastructure.

## Verification

Run the repo-appropriate checks plus:

```bash
swift build -c release
```

Use `rg` for discovery only when preparing the cleanup inventory. Do not treat a string scan as authoritative release evidence. For cleanup verification, inspect `Package.swift` or the package graph to confirm DebugBridge package and target dependencies are absent, run `swift build -c release`, and when a built binary is available inspect symbols with `nm -j` to confirm DebugBridge symbols are absent.

## Rules

- Keep edits reversible through git.
- Never force push, amend, delete package caches, or remove unrelated QA tools.
- If Release build fails on a missing DebugBridge symbol, stop and report the incomplete removal.
