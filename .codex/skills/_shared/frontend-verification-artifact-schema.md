# Frontend Verification Artifact Schema

Use this schema whenever a skill claims rendered frontend verification, visual QA, design review, reference fidelity, or browser-based UI evidence. A screenshot alone is not enough; the artifact must bind the image to the current route, state, viewport, run, and reviewer decision.

## Required Record

Each reviewed surface should have one `frontend_verification_artifact` record:

```yaml
frontend_verification_artifact:
  schema_version: 1
  requirement_or_task: "<requirement id, issue id, or task scope>"
  run_id: "<same-run id or timestamp>"
  commit_or_diff_ref: "<git sha, branch diff, or changed files ref>"
  route_or_surface: "<URL, route, component story, or screen name>"
  browser_context:
    tool: "<Browser, Chrome, Playwright, or manual browser>"
    dev_server: "<command or stable URL>"
    authenticated: false
  evidence:
    desktop:
      viewport: "<width>x<height>"
      screenshot: "<path or artifact ref>"
      inspected_state: "<default/loading/error/etc.>"
    mobile:
      viewport: "<width>x<height>"
      screenshot: "<path or artifact ref>"
      inspected_state: "<default/loading/error/etc.>"
    stress_states:
      - state: "<long text, empty, dense list, loading, error, pending, failed, success, etc.>"
        viewport: "<width>x<height>"
        screenshot_or_trace: "<path or artifact ref>"
    interactions:
      - action: "<click, hover, focus, keyboard, open modal, submit form, etc.>"
        expected_result: "<observable result>"
        evidence_ref: "<screenshot, trace, DOM note, or log>"
    browser_inspection:
      console_errors: "<none or linked log>"
      network_errors: "<none or linked log>"
      overflow_or_clipping_check: "<pass/fail + evidence>"
      accessibility_or_contrast_check: "<pass/fail/not_run + evidence>"
      touch_target_or_focus_check: "<pass/fail/not_run + evidence>"
  reference:
    required: false
    reference_artifacts: []
    accepted_differences: []
    fidelity_reviewer_ref: "<reference-fidelity-reviewer output or not_required>"
  reviewers:
    visual_qa_reviewer_ref: "<agent id/output, fallback record, or not_required>"
    design_reviewer_ref: "<agent id/output, fallback record, or not_required>"
    main_reconciliation_ref: "<accepted/rejected/deferred/blocked findings>"
  four_axis_scores:
    design_quality: "<0-10 + one-sentence rationale>"
    originality: "<0-10 + one-sentence rationale>"
    craft: "<0-10 + one-sentence rationale>"
    functionality: "<0-10 + one-sentence rationale>"
  verdict: "<PASS/FIX_REQUIRED/BLOCKED or skill-specific verdict>"
  unresolved_risks: []
```

## Evidence Rules

- `desktop.screenshot` and `mobile.screenshot` must be same-run browser evidence for layout-bearing changes.
- Required stress states must match the requirement risk, not a generic placeholder.
- A screenshot path without route, viewport, state, and run identity is weak evidence.
- Static image review cannot prove interaction behavior; record interaction traces when functionality, affordance, or state transitions matter.
- A visual-diff score, SSIM score, or screenshot existence cannot be the final pass condition.
- Stale artifacts must be rejected unless their `commit_or_diff_ref`, route, state, and viewport match the current candidate.
- If a check cannot run, record `not_run` plus why it is weaker evidence.

## Four-Axis Rubric

Score every UI-bearing review on four axes. Use `0-10` with a concise rationale; the score is evidence, not the verdict by itself.

- `design_quality`: color, typography, layout, imagery, and interaction treatment form one trustworthy product identity.
- `originality`: the surface avoids template defaults, generic AI slop, decorative filler, and arbitrary component spam.
- `craft`: spacing, alignment, contrast, wrapping, density, responsive adaptation, and visual states are executed cleanly.
- `functionality`: users can understand the state, identify the primary action, complete the flow, and recover from loading/error/empty/disabled states.

When these scores disagree with the final verdict, explain why. Example: high craft can still fail if functionality is blocked, or high functionality can still need fixes when design quality undermines trust.
