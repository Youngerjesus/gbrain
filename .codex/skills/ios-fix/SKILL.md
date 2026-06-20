---
name: ios-fix
description: Fix a bug found by iOS QA using a reproducing device snapshot, minimal Swift changes, rebuild, real-device verification, and a regression fixture.
---

# iOS Fix

Use this when an `ios-qa` finding should be fixed. The iron law is: no fix without a reproducing snapshot.

## Workflow

1. Read the QA finding, screenshot, accessibility node, and suspected state.
2. Reproduce the bug on the device through bridge actions or snapshot-eligible state changes.
3. Capture the pre-fix state to `test/fixtures/ios-fix/<bug-slug>-pre.json`.
4. Capture the pre-fix screenshot to `test/fixtures/ios-fix/<bug-slug>-pre.png`.
5. Write a one-line expected behavior statement near the fixture or in the report.
6. Trace Swift source from screen to view model to state mutation. Identify root cause before editing.
7. Apply the smallest Swift change that fixes the behavior.
8. Rebuild and reinstall with xcodebuild. Let the daemon reconnect.
9. Restore the pre-fix snapshot, re-screenshot, and compare.
10. Capture `<bug-slug>-post.png` and add a regression test gated by `GSTACK_HAS_IOS_DEVICE=1` when the repo supports device-gated tests.

## Rules

- If the bug still reproduces after three attempts, stop and report the best hypothesis and evidence.
- If `/state/restore` returns schema mismatch, regenerate accessors and re-capture fixtures.
- If the build fails, understand and repair the compile error before continuing.
- Keep the final diff minimal and include the fixture/test with the fix.
