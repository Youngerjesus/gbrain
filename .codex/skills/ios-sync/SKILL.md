---
name: ios-sync
description: Regenerate or update an installed gstack iOS DebugBridge when the user asks to resync iOS debug bridge files, regenerate iOS accessors, pick up new @Observable state, or upgrade bridge templates.
---

# iOS Sync

Use this after `ios-qa` has been installed in an app and the bridge needs to be regenerated or updated.

## Workflow

1. Detect the installed bridge version from `<app>/DebugBridgeGenerated/.gstack-version`. If missing, treat it as an unknown older install.
2. Detect the upstream version from `$GSTACK_HOME/ios-qa/.gstack-version` when `GSTACK_HOME` points to a local gstack checkout.
3. Check whether new `@Observable` classes or `@Snapshotable` fields were added. If versions match and no accessor-affecting source changed, exit with "already up to date".
4. Regenerate accessors:
   ```bash
   : "${GSTACK_HOME:?Set GSTACK_HOME to the local gstack checkout before regenerating iOS QA accessors}"
   swift run --package-path "$GSTACK_HOME/ios-qa/scripts/gen-accessors-tool" \
     gen-accessors --input "$APP_SOURCE_DIR" --output "$APP_SOURCE_DIR/DebugBridgeGenerated"
   ```
5. Update templated Swift files from the `ios-qa` templates. Preserve user edits only when a documented marker such as `// GSTACK-EDIT-LINE` indicates an intentional editable line. Otherwise, replace generated/template-owned files.
6. Verify with Swift build, xcodebuild, app relaunch, daemon connection, token rotation, and `GET /state/snapshot` schema hash.

## Failure Handling

- If Swift compile fails after regeneration, stop and report the compile error. Do not keep layering fixes without understanding the failure.
- If schema hash is unchanged after adding state, confirm the state is actually marked snapshot-eligible.
- If source input includes fixtures or generated code that should not be scanned, rerun with an appropriate exclude path when the generator supports it.
