# Pretext Patterns

This skill always uses the vendored runtime at `../vendor/pretext.js`.

## Default Runtime Rule

For standalone HTML artifacts:

- read `vendor/pretext.js`
- embed it directly or load it from a relative local path
- treat CDN use as fallback only if the vendored file is missing

## Pattern Selection

Choose the simplest pattern that satisfies the page.

### 1. `basic-layout`

Use for:

- standard landing sections
- app surfaces
- cards, forms, dashboards

Use these exports:

- `prepare`
- `layout`

Behavior:

- prepare text after fonts load
- relayout on resize
- recompute heights for measured text blocks

### 2. `segmented-tight-fit`

Use for:

- chat bubbles
- shrink-wrapped labels
- typography that must fit tightly without visual slack

Use these exports:

- `prepareWithSegments`
- `walkLineRanges`
- `layoutNextLine` when needed

### 3. `obstacle-flow`

Use for:

- text that wraps around visual blocks
- editorial compositions with interruptions in text width

Use these exports:

- `prepareWithSegments`
- `layoutNextLine`

### 4. `full-lines`

Use only when necessary for:

- highly controlled editorial layouts
- custom line-by-line rendering

Use these exports:

- `prepareWithSegments`
- `layoutWithLines`

## Minimum Behavior Contract

Every generated artifact should:

- wait for fonts before first prepare call
- relayout on resize
- keep text blocks from clipping or collapsing
- use the chosen pattern consistently across the page
