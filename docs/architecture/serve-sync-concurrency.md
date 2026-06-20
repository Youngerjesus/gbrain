# PGLite local concurrency: `serve`, interactive reads, and maintenance

**Short version:** on a PGLite brain, interactive `query`, `search`, and
`think` callers can use a live local owner broker. Maintenance commands
(`sync`, `embed`, `extract`) are not broker-executed; if another PGLite owner is
live, they return `maintenance_deferred` and should be rerun after the owner
exits.

## Why

PGLite is embedded Postgres in-process. One local process owns the PGLite data
directory at a time. A running CLI command or stdio MCP `gbrain serve` process
therefore holds the database connection for that brain.

GBrain handles this by separating interactive work from maintenance work:

- Interactive `query`, free-text `search`, and `think` route through the live
  local owner over `.gbrain-operation.sock` when a PGLite owner is already
  running.
- A second stdio MCP `gbrain serve` becomes a proxy and exposes only
  `query`, `search`, and `think`.
- CLI calls keep direct-open behavior when no owner is present.
- Maintenance commands (`sync`, `embed`, `extract`) are deferred under a live
  owner. They are not queued or executed through the operation broker.

This is distinct from the `gbrain-sync` advisory lock, which coordinates two
concurrent syncs inside the database. PGLite owner contention is the embedded
database ownership surface.

## What to do

### Interactive work

You can keep a local stdio MCP server running and still use:

```bash
gbrain query "what changed?"
gbrain search "acme pricing"
gbrain think "what should I know before this meeting?"
```

If the live owner broker is reachable, those calls route through it instead of
opening PGLite directly. If no owner exists, the CLI opens PGLite directly as
before.

### Maintenance work

For large maintenance work, stop the owner first if you want the command to run
immediately:

```bash
pkill -f 'gbrain serve'      # or stop your MCP client / Claude Desktop / Cursor
gbrain sync --no-pull --no-embed --yes
```

If you run maintenance while another PGLite owner is live, gbrain exits with a
deterministic `maintenance_deferred` status rather than waiting until PGLite
times out. Restart `gbrain serve` after the maintenance command completes.

This contention does **not** apply to the Postgres engine; Postgres tolerates
concurrent connections, so `serve` and `sync` can run simultaneously there.

## Status vocabulary

| Status | Owner | Meaning | Operator action |
| --- | --- | --- | --- |
| `served` | Broker / IPC | The live owner served the operation. | No action. |
| `owner_unreachable` | Broker / IPC | A live owner lock required broker routing, but the operation socket was not reachable. | Retry shortly, or stop stale local owners and rerun. |
| `completion_unknown` | Broker / IPC | The owner accepted the request but did not reply before the caller timeout. | Retry if idempotent; inspect the owner process if it repeats. |
| `lock_safety_blocked` | Broker / IPC or CLI preflight | The lock state was corrupt or unknown, so gbrain refused an unsafe direct open. | Do not delete live-looking locks blindly; inspect the owner process or run doctor tooling. |
| `stale_socket_recovered` | Broker / IPC startup diagnostic | A stale operation socket was removed and replaced by the new owner. | Usually no action. |
| `owner_starting` | CLI maintenance preflight | Another process appears to be starting as owner, so maintenance was not started. | Retry after the owner broker is reachable or the owner exits. |
| `maintenance_deferred` | CLI maintenance preflight | A live PGLite owner exists, so `sync`, `embed`, or `extract` did not start. | Stop the owner or wait for it to exit, then rerun maintenance. |

Broker diagnostics intentionally avoid echoing private query text, request
parameters, source scope, or MCP auth material. Local socket paths may appear in
explicit stale-socket recovery diagnostics because they identify the local file
that was repaired.

## Diagnosing a sync hang

If a sync wedges (no progress, high CPU), re-run with the per-file begin trace
so the stalling file is named:

```bash
GBRAIN_SYNC_TRACE=1 gbrain sync --no-pull --no-embed --yes
```

The last `[sync] begin import: <path>` line with no following completion is the
file being processed when the hang occurred. Under `--workers >1` / `--all`,
the stuck file is in the set of begin-lines without a matching completion.

If you suspect a schema-pack regex is the cause (a pack with a
catastrophic-backtracking `inference.regex`), complete the sync with the pack
disabled and re-run extraction afterward:

```bash
gbrain sync --no-schema-pack --no-pull --no-embed --yes
```

`gbrain schema lint` flags the classic nested-quantifier ReDoS shapes
(`(a+)+`, `(a*)*`, ...) in pack regexes as warnings.
