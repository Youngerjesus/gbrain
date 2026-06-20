# Scenario Brake: PGLite Owner Broker

Created: 2026-06-20
Verdict: [SCENARIOS MISSING]
Plan under review: plans/001-pglite-owner-broker/plan.md

## Scenario Classes Reviewed

- Entry path: CLI command, second MCP stdio server, owner startup, no-owner fallback.
- Actor: owner process, competing CLI caller, competing MCP stdio caller, operator.
- State: no owner, owner ready, owner busy, live lock without broker, stale socket, dead/stale lock, unknown/corrupt lock, owner death by request phase.
- Dependency behavior: socket missing, refused, permission-denied, not-yet-bound, partial response, malformed response, timeout.
- Recovery and observability: direct-open fallback, lock-safety block, stale cleanup, ambiguous completion, privacy-safe diagnostics.

## Key Parameters Identified

- Operation type: `query`, `search`, `think`, `think --save`, `think --take`.
- Lock classifier state: absent, live, dead/stale recoverable, corrupt recoverable, unknown.
- Socket state: absent, live, stale, permission denied, not yet bound, partial response.
- Owner timing: before send, queued-not-started, handler-started, response-written-not-received.
- Caller context: CLI vs MCP stdio, source env, federated read, remote flag, private query string.
- Queue behavior: interactive quick request behind long `think`, maintenance-class synthetic request.

## Parameter Mutations Explored

- Live owner plus five callers.
- No owner plus one caller.
- No owner plus five simultaneous callers.
- Live lock plus broker unavailable.
- Live lock plus socket permission denied or not yet bound.
- Unknown/corrupt lock plus broker unreachable.
- Owner dies before send, while queued, while handler is running, or after response write.
- Broker returns partial/truncated/malformed response.
- Long `think` at the head of the interactive queue.

## Scenario Links And Separations

- `query` and `ask` alias are same path after alias normalization.
- No-owner single direct-open and no-owner thundering-herd are different paths.
- CLI pre-connect routing and second MCP stdio proxy startup are different paths.
- Owner death before send, queued-not-started, handler-started, and response-lost-after-completion are different recovery paths.
- Queued and served are successor states of owner-ready broker flow, not separate entry scenarios.
- Real `sync`/`embed`/`extract` command forwarding is deferred to the later scheduler requirement; queue priority seam must still be proven here.

## What The Plan Already Covers

- Live-owner forwarding for CLI and MCP stdio.
- No-owner direct-open fallback for single caller.
- Live lock without broker returning lock-safety diagnostics.
- Mandatory non-acquiring lock classifier.
- MCP stdio proxy path.
- Positive broker-routing evidence.
- Trust/source preservation and privacy sentinel tests.

## Missing Or Conflated Scenarios

- Missing: concurrent no-owner cold-start race. At least five eligible callers starting together must not all try direct-open and hit PGLite lock timeout.
- Missing/conflated: owner-death retry behavior by phase. The plan must distinguish not sent, queued-not-started, handler-started, and response-lost-after-handler.
- Missing: ambiguous completion status. `completion_unknown` must be distinct and privacy-safe.
- Missing: mutating local CLI `think --save/--take` must not auto-retry after ambiguous completion.
- Missing: unknown/corrupt lock classifier plus broker unreachable must not fall through to normal `connectEngine()` wait.
- Missing: partial/truncated broker responses and permission-denied/not-yet-bound sockets must be bounded, non-lock, privacy-safe paths.
- Missing: race-safe stale socket cleanup during concurrent owner restart/bind.
- Missing: long `think` at the head of the interactive queue must be bounded so it does not monopolize interactive capacity forever.

## Highest-Risk Blind Spots

- A test could pass by hiding timeout strings while callers direct-open or skip broker routing.
- A broker timeout could later mutate state after the caller reports failure.
- A cold-start thundering herd could recreate the lock contention problem even if live-owner forwarding works.
- Socket cleanup could unlink a newly-bound live broker socket during restart.

## Recommended Scenario Additions

- Unit: lock classifier unknown/corrupt/live/dead states; no wait/no steal.
- Unit: partial/truncated broker response and permission-denied/not-yet-bound socket diagnostics.
- Unit/integration: queue long `think` before quick interactive call and assert bounded non-monopoly behavior.
- Integration: no-owner five-caller cold-start race.
- Integration: owner death by phase with retry rules and `completion_unknown`.
- Integration: race-safe stale socket cleanup during concurrent bind/restart.
- E2E: second MCP stdio startup proves zero direct PGLite open attempt before proxy.

## Companion Review Synthesis

- Path separation reviewer: `[SCENARIOS MISSING]`; accepted findings on no-owner cold-start race, owner-death phase split, and second MCP proxy zero-direct-open evidence.
- Parameter mutation reviewer: `[SCENARIOS MISSING]`; accepted findings on unknown/corrupt lock fallback, partial response, socket permission/not-yet-bound, long `think`, and cold-start race.
- Recovery/observability reviewer: `[SCENARIOS MISSING]`; accepted findings on ambiguous completion, no auto-retry for mutating `think`, stale cleanup race safety, and privacy-safe operator signals.
- Rejected findings: none. Queue quota beyond five callers is deferred as non-blocking resilience follow-up.

## Overall Verdict

[SCENARIOS MISSING]

The plan was not implementation-ready before this review. The missing scenarios have now been reflected into `technical-design.md` and `plans/001-pglite-owner-broker/plan.md`; secondary-plan must preserve these additions before implementation starts.
