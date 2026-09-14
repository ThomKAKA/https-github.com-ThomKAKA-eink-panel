# STEP017B — Host Frame Endpoint Implementation Report

Status: HOST IMPLEMENTATION / IN-PROCESS SOFTWARE VERIFICATION COMPLETE.
Parent baseline: `4f5383dda1202f1e09ea48aefdac69e92f4e196d`.
Initial gate: expected HEAD matched, index empty, only `?? hardware/evidence/`.
This is not LAN/device/physical verification. Stop before STEP017C.

## 1. Files and preserved boundaries

- Added [publisher](../../../services/progress_frame.py) and [53 contract tests](../../../tests/test_progress_frame.py).
- Added one route to [server](../../../server/main.py).
- Added internal `_if_current` synchronization hook to [EventStateStore](../../../services/event_store.py); event ingestion, schema and responses remain unchanged.
- Added this report and updated [PROJECT_STATE](../../../PROJECT_STATE.md).

STEP017A documents, Renderer, B1 converter, Transport Adapter, ESP32/H1, PlatformIO, dependencies and original evidence are unchanged. No listener, curl, LAN traffic, firmware build, serial or hardware operation was performed. No new runtime frame/header files were written.

## 2. Configuration and invocation semantics

Future Host process must have `EINK_PROGRESS_SOURCE` set before importing/starting `server.main`. It selects exactly one event source, not a display label or credential. Valid syntax is `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. No default or trimming fallback; missing/invalid configuration logs a generic error and makes the frame route unavailable (503), while existing routes remain usable.
Configuration is captured when the server module initializes its publisher. Changing the environment afterward does not reconfigure it; restart is required. This report does not start a server or change its existing loopback binding. Single serving process only, as frozen in [A policy](STEP017A_UPDATE_AND_FAILURE_POLICY.md).

Future callers use the existing POST /api/events schema with `panel=progress`, matching event `source`, and existing Progress data fields (`title`, `current_step`, `progress`, `status`, etc.). STEP016 offline aliases are not a new event API. Existing event acceptance still acknowledges storage only, not frame publication or physical display.

GET `/api/panels/progress/frame` checks the selected snapshot on demand. It reuses an already published snapshot version, otherwise attempts one render. No background jobs or automatic retries/chasing. Failed unpublished versions may be attempted by a later GET; they never overwrite the published record. Host restart with a new EventStateStore has no snapshot/publication until an event is supplied again.

## 3. Mapping and existing rendering pipeline

`snapshot → map_snapshot → ProgressPanel strict eink render → in-memory PNG → png_to_logical_raw → logical_to_transport → validated PublishedFrame`

Mapping preserves business fields and uses valid explicit updated_at first; missing/None/blank falls back to occurred_at, never current time. Accepted time input is local `YYYY-MM-DD HH:mm` or timezone-aware ISO with T separator and Z/numeric offset. Output is minute precision at fixed UTC+08:00 (the product's Shanghai wall-clock convention); historical daylight-saving reconstruction is not implemented. Illegal explicit timestamps reject publication.
The original EventStateStore may already have supplied occurred_at as updated_at when absent; its behavior is unchanged.
Rendering is fixed 400x300, rotation 0, mode 1. Waiting/error normalized state, reserved WAITING DATA/UPDATE FAILED pages, font/layout failure and absent post-binarization text contrast reject publication. The existing conservative glyph check is reused, not a new exhaustive font proof.
Renderer/B1 retain L orientation, PC Transport Adapter reverses rows exactly once into T. No new pixel transform is implemented here.

In-memory sample verification used the existing [offline sample](../../../data/progress_offline.json), mapped into an event snapshot with unchanged business fields and Local JSON display label:

| Object | Result |
| --- | --- |
| T frame length | 15000 bytes |
| T SHA-256 | a243c5740472d3f2f3c09ca440446d2e50b5da0b32bcb00b6ddca533f6084f8d |
| Relationship | Equals the previously recorded STEP016 T byte identity |

This was an in-memory Host rendering check, not new frame files, firmware integration or physical verification. The test suite independently unpacks every T pixel against the rendered L image and checks Chinese text presence; it does not claim a new human visual or physical review.

## 4. Atomic publication

PublishedFrame stores immutable bytes, computed strong ETag, fixed format and `(source,event_id,occurred_at)` version. Its service construction rejects mutable/non-bytes or any size other than 15000.
A publisher lock serializes snapshot fetch/render/publication and deduplicates concurrent GET rendering. Rendering is outside the EventStateStore lock, so ingestion can proceed. The internal `_if_current` hook compares the captured snapshot with the current snapshot under the same store lock used by ingestion, then performs only a publication reference assignment. No render/I/O/reentrant store calls are allowed in its callback.
Lock order is publisher then store; ingestion never acquires publisher. Old render results are discarded if their snapshot ceased to be current. That GET returns the previous publication or 503; a later GET can render the new snapshot. It does not spin until current.
The route retains one immutable record for all response headers/body, so a later publication cannot mix versions in an in-flight response. This guarantees process-local software atomicity, not persistence or multi-worker consistency.

## 5. HTTP results

Implements [A HTTP contract](STEP017A_FRAME_HTTP_CONTRACT.md):

- 200: application/octet-stream, Content-Length 15000, complete T body, strong double-quoted lowercase SHA-256 ETag, X-Frame-Format `epd-t-400x300-mono1-msb-v1`, Cache-Control `no-cache, no-transform`.
- Conditional GET: parse entity tags including weak comparison, lists, quoted commas, empty list members and wildcard. A quoted `"*"` is an ordinary tag, not the wildcard. Repeated If-None-Match header fields are combined as a list.
- Match: 304, empty body, same ETag/format/cache policy, no Content-Length. Nonmatch: full 200.
- Malformed If-None-Match: 400 before rendering. A missing publication/config/source snapshot: 503. Error responses have no valid frame identity/format claim.
- New render failure with old publication: retain and serve its original 200/304 representation. Logs contain rejection category only, not snapshot/private exception content.

No PNG/JSON wrapper, compression or Transfer-Encoding is emitted by the in-process response path. Actual socket framing, proxies and transport truncation are NOT TESTED here. This Host code does not implement the future device rejection logic or Last Known Good display acceptance.

## 6. Verification results

Project `.venv` used with `python.exe -B -m pytest -q -p no:cacheprovider`; no dependencies installed/upgraded.

| Run | Result |
| --- | --- |
| Before changes, existing regression | 311 passed in 3.49s |
| New Host tests, final run | 53 passed in 1.09s |
| Complete final regression | 364 passed in 4.12s |

Coverage: source/config isolation; time mapping/rejection/fallback; real Chinese strict render and all-pixel T mapping; version reuse/content identity; 200/304/400/503 and headers; immutable/length-invalid candidates; exceptions retaining previous publication; event POST/snapshot compatibility; parallel requests; barrier-controlled stale render; atomic callback; process-local restart behavior.
Existing 311 tests include legacy event/store/render behavior. TestClient uses in-process ASGI only, without a listening HTTP server. Concurrency uses bounded synchronization events, not timing guesses.
Document links, sensitive patterns, protected-file hashes, syntax parsing and git diff checks are part of final submission verification. Only Host source/tests, this report and state are authorized for staging; evidence remains untracked.

## 7. Remaining gates and commit

STEP017C network Fetcher and continuous-display lifecycle design: NOT RUN. Current H1 remains one-shot; no polling wrapper or repeated-display safety claim is made.
ESP32 network implementation, firmware compilation, TCP truncation/device rejection tests, LAN physical delivery and hardware operations: NOT RUN.
NETWORK PRODUCT FUNCTION VERIFIED=NO. H0/H1 and Offline Progress Display limited-scope PASS unchanged. BUSY fault injection, Deep Sleep, Partial/Fast Refresh and long duration remain NOT TESTED; exact physical FULL count NOT independently verified.
Local commit message: `feat(network): publish progress transport frames over HTTP`. No push/tag. Stop before STEP017C.
