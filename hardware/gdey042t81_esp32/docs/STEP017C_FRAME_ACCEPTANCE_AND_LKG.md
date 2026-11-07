# STEP017C — Frame Acceptance and Last Known Good

Status: DESIGN FROZEN; receiver/identity/runtime tests NOT RUN.
Wire dependency: [STEP017A HTTP contract](STEP017A_FRAME_HTTP_CONTRACT.md).
Execution dependency: [state machine](STEP017C_NETWORK_STATE_MACHINE.md).

## 1. Restricted HTTP profile

Send one HTTP/1.1 GET `/api/panels/progress/frame`, Host IPv4:port,
Connection: close, Accept: application/octet-stream and Accept-Encoding: identity.
Send If-None-Match only as the single last accepted quoted strong identity.
No request body, authentication, cookies, redirects, pipelining, proxy or discovery.

Response status line accepts HTTP/1.0 or HTTP/1.1 with a three-digit status and
valid syntax; only 200 and conditional 304 are acceptable. Other statuses,
including informational responses, immediately reject/close, not recursively parse
another response. Header names are ASCII tokens and case-insensitive, values trim
outer SP/HTAB, line endings must be CRLF. Reject folding, invalid controls,
whitespace before colon and malformed lines. Ignore bounded unknown headers.

Header/status section maximum is 4096 wire bytes including CRLF and final blank
line; each status/header line is at most 512 bytes including CRLF. Parse
incrementally with a bounded line buffer; do not allocate a growing header String.
Reject any duplicate Content-Type, Content-Length, ETag, X-Frame-Format,
Cache-Control or Connection, even if identical. Any Content-Encoding or
Transfer-Encoding occurrence rejects the response. Do not overwrite conflicting
values or interpret a comma-joined framing value as an integer.

## 2. Status-specific rules

| Field / property | 200 | 304 |
| --- | --- | --- |
| Content-Type | application/octet-stream; media type case-insensitive, no parameters | Not required; does not describe a body |
| Content-Length | Exactly decimal 15000; digits only, checked numeric parse, no sign/comma | Must be absent |
| X-Frame-Format | Exact epd-t-400x300-mono1-msb-v1 | Same required value |
| ETag | Exactly double quotes around 64 lowercase hex digits, no W/ | Same syntax and exact identity sent by this request |
| Cache-Control | no-cache and no-transform directives, order/case/OWS normalized; no other directives in this profile | Same |
| Body | Exactly 15000 T bytes, matching SHA-256 | No body; requires an existing sent accepted identity |

No local identity plus 304, or mismatched 304, is a protocol anomaly. No identity
advancement or display action follows. Errors/503 are not business JSON to parse.

## 3. Receive completeness and identity

T is 400x300 mono1, stride 50, row-major, MSB-first, 0 black / 1 white.
Never modify orientation, bit order or polarity. Receive only within remaining
buffer capacity; after byte 15000, use a separate one-byte overflow probe, never
write beyond the array. Reject EOF before completion, resets, receive error,
deadline expiry or any extra byte. No padding, truncation or partial display.

Connection: close requests make EOF verification possible. Require orderly EOF
within the response-end and whole-transaction budgets for both 200 and 304. Do
not accept merely because currently available()==0 or all declared bytes arrived.
Do not drain indefinite extra data. A Host/proxy that does not close in time fails
this device profile; deployment compatibility is a future E/F gate, not a current
Host implementation change. This strict EOF check is additional bounded defensive
validation, not a claim that Content-Length normally requires EOF in HTTP.

Close the socket before hashing/handoff. SHA-256 over all 15000 received bytes
must equal the response ETag; crypto API failure also rejects. The hash comparison
and final acceptance must still meet the whole HTTP deadline. Valid unchanged 200
is discarded without display. Hashes do not authenticate the sender or detect an
attacker who changes both bytes and ETag.

## 4. Single frame buffer

| Option | Safety / resources | Decision |
| --- | --- | --- |
| Candidate + display/old frame | 30000 bytes of frame RAM; useful for concurrency not required here | Not selected |
| One static 15000-byte buffer | Exclusive ownership prevents mutation; physical screen retained independently | Selected |
| Dynamic frame/stream directly into EPD | Heap lifetime or partial-write risks, no benefit | Not selected |

Ownership: idle -> receiver writable -> validator -> display const-readable -> idle.
No frame is placed on the stack. Metadata, a bounded header line and one overflow
probe are separate, not another full frame. An invalid partial download can overwrite
old RAM bytes safely because no display operation occurs. No persistent old-frame
RAM/Flash copy, no rollback rendering. Static RAM remains alive throughout session.

## 5. ETag advancement and LKG

Keep bounded RAM metadata for candidate identity, display-attempt identity and last
accepted identity plus validity flags. Identities are 66 wire characters plus NUL,
not unbounded strings. Boot clears validity; no NVS/Flash identity persistence.

| Advancement choice | Consequence | Decision |
| --- | --- | --- |
| Immediately after download validation | Could suppress retry via 304 even before display was attempted | Reject |
| Any refresh return | Ignores H1 true meaning and observable timeout | Reject |
| Return plus conservative elapsed/BUSY conditions | Defensible software acceptance, not physical proof | Select |
| Only independently verified physical success | Not available from existing API/runtime | Cannot claim |

Network validation sets candidate only. Changed validated identity becomes an
attempt identity when entering a session. Promote to last accepted only after the
[display contract](STEP017C_DISPLAY_LIFECYCLE.md) reports software conditions met.
Otherwise preserve the previous accepted metadata and enter FAULT_STOP: no next
request and no automatic retry of that candidate or any later candidate.

LKG means the last software-accepted identity plus no intentional screen writes
on network failure. It is not verified physical RAM/image state. A stuck-low BUSY
or unobservable hardware fault may still pass software conditions; a subsequent
304 will suppress display. Conversely, not advancing on ambiguous outcomes does
not trigger repeated 200/display attempts because FAULT_STOP is terminal.
Physical success can only be reported by separately collected evidence.
