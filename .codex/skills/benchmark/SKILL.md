---
name: benchmark
description: Measure web page performance, capture baselines, compare regressions, and produce performance reports when the user asks for benchmarks, page speed, Web Vitals, Lighthouse-style checks, bundle size, or load-time regression analysis.
---

# Benchmark

Use this skill as a source-code-read-only performance engineering workflow: it may write benchmark reports, but it must not change application code unless the user explicitly asks for fixes. Prefer the gstack browse daemon when available; otherwise use the best available browser/performance tooling and report the gap.

## Workflow

1. Create `.gstack/benchmark-reports/` and `.gstack/benchmark-reports/baselines/`.
2. Determine pages from the user, navigation discovery, or `--pages`. For `--diff`, inspect branch changes against the PR base or default branch.
3. For each page, use browser performance APIs:
   - navigation entry for TTFB, DOM interactive, DOM complete, and full load
   - paint entries or observer-backed values for FCP/LCP when available
   - resource entries for slowest resources, total transfer, JS bytes, CSS bytes, and request count
4. In baseline mode, write `.gstack/benchmark-reports/baselines/baseline.json`.
5. When a baseline exists, compare current metrics to it.
6. Save a Markdown report and JSON report under `.gstack/benchmark-reports/`.

## Regression Thresholds

- Timing metric regression: more than 50 percent increase or more than 500 ms absolute increase.
- Timing warning: more than 20 percent increase.
- Bundle size regression: more than 25 percent increase.
- Bundle size warning: more than 10 percent increase.
- Request count warning: more than 30 percent increase.

## Report Requirements

Include the tested URL, branch, pages, metric table, regression summary, slowest resources, performance budget check, and recommendations. Focus recommendations on first-party resources. Flag third-party scripts as context unless the user controls loading strategy.

## Rules

- Measure, do not guess.
- Without a baseline, report absolute numbers and recommend capturing one.
- Keep this read-only unless the user explicitly asks for fixes.
