# Refresh System

`RefreshManager` owns fetching, source status, and Last Known Good data. The browser never
contacts configured HTTP sources directly.

## Refresh behavior

1. Browser requests a configured source refresh.
2. RefreshManager creates the appropriate adapter and fetches data.
3. Successful data becomes the in-memory Last Known Good value.
4. The panel renders the returned data.
5. On failure, cached data is returned with `stale=true`; without cache, the panel receives an
   empty object and renders its waiting state.

STATUS is `ONLINE` after success, `OFFLINE` for an unavailable HTTP source, and `ERROR` for
local or Mock configuration/file failures.

Automatic refresh is opt-in and defaults to OFF. Supported intervals are 5 seconds (development
only), 30 seconds, 1 minute, 5 minutes, 15 minutes, and 30 minutes. The browser schedules calls;
the server reports `LAST SUCCESS` and `NEXT REFRESH`.

The cache is intentionally in memory for Phase 3. Restarting the simulator clears it. No database,
Redis, worker, or background scheduler is used.

## Failure states

- `ONLINE`: the adapter succeeded and the payload normalized to a usable Panel state.
- `OFFLINE`: an HTTP connection, timeout, response-status, or JSON transport failure occurred.
- `ERROR`: a payload was readable but incomplete or invalid for its Panel, or a local/Mock source
  failed.

On `OFFLINE` or `ERROR`, Last Known Good is returned with `stale=true` when available. An invalid
payload never replaces the cached value. A later valid refresh replaces the cache and returns to
`ONLINE`.

## Refresh concurrency

Refreshes for the same source are serialized across adapter fetch, semantic validation, and state
commit. Different sources use independent locks and may refresh concurrently. In the browser,
duplicate requests for the same active context share one promise, and a generation token prevents
responses from an earlier panel, sample, or source selection from updating the current UI.
