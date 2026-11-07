# STEP017A — Frame HTTP Contract

Status: DESIGN FROZEN; endpoint implementation and contract execution NOT RUN.
Parent baseline: `37f80a69470a91a921c7b8b8db4e29032ae14840`.
See [architecture audit](STEP017A_LAN_PRODUCT_ARCHITECTURE.md) and [failure policy](STEP017A_UPDATE_AND_FAILURE_POLICY.md).

## 1. Route selection

| Candidate | Consistency / meaning / minimality | Future coupling | Decision |
| --- | --- | --- | --- |
| `/api/panels/progress/frame` | Matches existing panels/render namespace; GET final frame rather than POST render input | Keeps panel namespace without implementing generic dispatch | Selected |
| `/api/display/progress/frame` | Clear but introduces a new resource namespace | No present benefit over panels | Rejected |

Official method/path: **GET `/api/panels/progress/frame`**. Host configuration selects one source; no source/panel query selector. Existing event/snapshot/render routes retain their contracts. This is a new route specification, not a currently available endpoint.

## 2. Exact 200 representation

| Item | Required value |
| --- | --- |
| Status | 200 OK |
| Content-Type | `application/octet-stream` (no media-type parameters) |
| Content-Length | `15000` |
| X-Frame-Format | `epd-t-400x300-mono1-msb-v1` |
| ETag | Double-quoted 64 lowercase hexadecimal SHA-256 of exact body bytes; no W/ prefix |
| Cache-Control | `no-cache, no-transform` |
| Body | Exactly 15000 complete T bytes |

The fixed format identifier means: T coordinates; width 400, height 300, 1-bit; row-major; stride 50; MSB-first; 0=black, 1=white; no header or padding. It identifies the existing pixel protocol, not a new orientation transformation. Missing/different identifier is rejected.
No Content-Encoding or Transfer-Encoding is used by this endpoint; no compression or chunked transfer. PNG, Base64, JSON wrapper, business JSON and multipart are prohibited. HTTP header names are case-insensitive; standard framing/whitespace parsing must not depend on header order.

Host may return 200 only from a complete validated publication record. Device must receive all bytes, verify framing and SHA-256 against ETag before display handoff. Validation never streams partial data into the controller.
An ETag identifies exact T content, not event ID, render time, PNG bytes or current clock. A changed snapshot can yield identical T bytes. It is neither authentication nor a signature/trust proof.

## 3. Conditional requests and 304

Device sends either no If-None-Match (no accepted identity after boot), or one previously accepted strong ETag verbatim. It must not send the identity of a merely downloaded/rejected candidate, a list or wildcard as its device request profile.
Host evaluates If-None-Match using HTTP GET conditional semantics against the current publication; this includes standards-compliant weak comparison/list/wildcard handling for other clients. The endpoint itself always emits the strong form above. Conditional evaluation and response must reference the same immutable publication.

Match: 304 Not Modified, no frame body, same current ETag, same X-Frame-Format and cache policy. Omit Content-Length on 304; the 200 exact-length requirement does not apply to 304.
Device accepts 304 only when it sent a known accepted identity and returned identity/format match it; no new frame and zero display commands. Unsolicited/mismatched/malformed 304 is rejected, never treated as a new valid frame.
No match: full 200 candidate. Valid 200 whose identity is already accepted causes zero display operations.

## 4. Errors and rejection

No published frame: 503 Service Unavailable, no frame ETag/format claim. Host may return a diagnostic error body but MCU never renders/parses it as business data. If a new render fails and an older valid publication exists, the old publication remains available with its original identity; it is not falsely labeled fresh.

Reject wrong/missing Content-Type, Content-Length or X-Frame-Format; malformed/weak response ETag; SHA mismatch; missing/truncated/oversized body; incomplete HTTP response; conflicting framing headers; compressed/chunked response; unexpected status including 206 and redirects. Do not follow redirects automatically. Only valid 200 and conditional valid 304 enter product success semantics.
Rejected candidates do not alter accepted identity, do not clear the screen and do not request a FULL. See [LKG policy](STEP017A_UPDATE_AND_FAILURE_POLICY.md). Request parsing libraries, limits/timeouts and buffer implementation remain STEP017C decisions.

## 5. Direction and verification limits

`T[50*y+b] = L[50*(299-y)+b]`; MCU transport/loading changes no bytes. Existing fixed H1 applies T-to-P mapping; `P=L`. See [orientation contract](STEP016D_ORIENTATION_RULE.md).
Hash equality proves byte identity, not origin trust, physical display success, controller acknowledgement or exact physical refresh count. Future contract/malformed-response tests are [planned](STEP017A_STAGE_TEST_PLAN.md), all NOT RUN here.
