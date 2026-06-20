---
name: ios-qa
description: Drive live-device iOS QA through the gstack debug bridge when the user asks to test an iPhone app, find bugs on a device, run iOS QA, or verify real-device app behavior.
---

# iOS QA

Use this skill for real-device iOS QA with the gstack DebugBridge. It assumes macOS, Xcode, a paired USB iPhone, and Swift source on disk. No simulator, XCTest, or WebDriverAgent is the default path.

## References And Assets

- Tailscale example: `references/tailscale-acl-example.md`
- DebugBridge templates: `templates/*.template`

## Workflow

1. Warm-start from `~/.gstack/ios-qa-session.json` only if the cached daemon is healthy, the device is connected, and no `--cold` run is requested.
2. Read Swift source from the requested source directory. Identify `@Observable` classes and fields marked `@Snapshotable`.
3. Generate typed accessors through the gstack generator or SwiftPM tool:
   ```bash
   : "${GSTACK_HOME:?Set GSTACK_HOME to the local gstack checkout before generating iOS QA accessors}"
   swift run --package-path "$GSTACK_HOME/ios-qa/scripts/gen-accessors-tool" \
     gen-accessors --input "<source-dir>" --output "<source-dir>/DebugBridgeGenerated"
   ```
4. Ask before installing or modifying app package/debug bridge wiring unless the user already explicitly requested installation.
5. Add Debug-config-only bridge wiring from the templates, gated behind `#if DEBUG`.
6. Build and install to the device with `xcodebuild -scheme <scheme> -destination 'platform=iOS,id=<UDID>' build install`.
7. Launch with `devicectl`, start or connect to the Mac-side daemon, rotate the boot token, and acquire a session.
8. Run the observe-act-verify loop:
   - `GET /screenshot`
   - `GET /elements`
   - `GET /state/snapshot`
   - choose the next action
   - `POST /session/acquire`
   - `POST /tap`, `/swipe`, `/type`, or state mutation when allowed
   - re-screenshot and record findings
   - `POST /session/release`

## Modes

- Local USB mode is default and binds loopback only.
- Tailnet mode requires Tailscale and explicit identity/capability handling.
- Demo mode means visible UI actions only; never use state writes to skip steps.

## Safety Rules

- DebugBridge must be Debug-only. Verify Release builds cannot link it.
- Treat tokens and audit logs as sensitive local machine state; do not copy them into repo artifacts.
- For remote tailnet mode, fail closed when identity or capability checks are missing.
- Use `ios-clean` before release-oriented cleanup if the user wants the bridge removed.
