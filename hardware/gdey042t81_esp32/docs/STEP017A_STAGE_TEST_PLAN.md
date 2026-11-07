# STEP017A — Stage and Test Plan

Status: PLAN FROZEN. All new executable tests below: NOT RUN.
Parent baseline: `37f80a69470a91a921c7b8b8db4e29032ae14840`.
Documents: [architecture](STEP017A_LAN_PRODUCT_ARCHITECTURE.md), [HTTP contract](STEP017A_FRAME_HTTP_CONTRACT.md), [update/failure policy](STEP017A_UPDATE_AND_FAILURE_POLICY.md), [security](STEP017A_NETWORK_SECURITY_BOUNDARY.md).

## 1. Sequential stage gates

Each future stage needs its own authorization; this table is not permission to implement or operate hardware now.

| Stage | Input → output | Allowed work in that future stage | Forbidden / gate |
| --- | --- | --- | --- |
| A LAN PRODUCT ARCHITECTURE FREEZE | Current physical closure → five design docs and state | Repository audit and document checks | No runtime/test code, tests, build, server or hardware; self-consistent docs and six-file commit only |
| B HOST FRAME ENDPOINT IMPLEMENTATION | Frozen A → Host publisher/endpoint and Host tests | Existing server integration, Host mapping/publication/contract tests | No ESP32/H1/hardware work; gate: deterministic exact T, source isolation, conditional HTTP and atomic publication |
| C ESP32 NETWORK FETCHER DESIGN FREEZE | A contract and B results → fetcher plus display-lifecycle design | Read-only audit/design for timeouts, buffers, polling, acceptance and continuous FULL lifecycle | No implementation/build/hardware; must resolve H1 Finished limitation and fault stop, otherwise NO-GO for D |
| D ESP32 NETWORK FETCHER IMPLEMENTATION | Approved C → isolated network entry and tests | Only separately approved network/display integration scope | No upload/hardware, no unilateral changes to frozen H1 or dependencies; gate: complete candidates only, unchanged/error zero display |
| E SOFTWARE / COMPILE VERIFICATION | B/D code → regression/build/identity evidence | Authorized software and isolated compilation checks | No hardware; gate: config isolation, resource budgets, artifact hashes and safety review |
| F PHYSICAL LAN UPDATE VALIDATION | E gate and separate hardware authorization → observed LAN update evidence | Controlled upload/network/display observations | No automatic reflash/fix; gate: changed content updates, unchanged/errors retain page, direction/Chinese correct; record limits |
| G EVIDENCE CLOSURE | F observations/raw evidence → audit/state/local commit | Evidence hashes and scoped documentation | No new physical claims, unsolicited hardware reruns or raw-evidence commit; reconcile facts and remaining NOT TESTED |

STEP017C must not mistake refreshOnce=true for confirmed display success. It must specify accepted-identity advancement and safe terminal failure behavior, and separately approve any future lifecycle extension while preserving frozen H1 history. A does not select an implementation workaround.

## 2. Host contract and publication tests

| Test | Required evidence / expected behavior | Execution |
| --- | --- | --- |
| Official route and method | GET exact route; existing event/snapshot/render contracts unchanged | NOT RUN |
| Valid 200 | Exact type, length 15000, format ID, strong ETag and complete T body | NOT RUN |
| Byte identity/direction | Independent T unpacking; L→T→P; ETag hashes exact T, not PNG | NOT RUN |
| Determinism | Same snapshot/fonts/config yields identical bytes/ETag; polling time excluded | NOT RUN |
| Conditional GET | Match→304 no body; mismatch→200; standard conditional parsing | NOT RUN |
| Missing publication | 503, no synthetic waiting/error frame | NOT RUN |
| Invalid render/frame | Wrong length, font/layout failure, invalid publication never yields candidate 200 | NOT RUN |
| Atomic publication | Parallel read sees complete old or new record; body/ETag/format agree | NOT RUN |
| Out-of-order render completion | Older snapshot result cannot replace newer publication | NOT RUN |
| Failure retention | New render failure preserves last publication/identity | NOT RUN |
| Source isolation | Only configured source selected; absent setting/source no fallback | NOT RUN |
| Host restart | Process-local state lost; no frame until valid event, no persistence claim | NOT RUN |

## 3. Future device contract/failure tests

| Test | Required behavior | Execution |
| --- | --- | --- |
| Valid changed 200 | Complete validated candidate before display handoff | NOT RUN |
| Valid unchanged 200 / 304 | Zero display operations | NOT RUN |
| Unsolicited/mismatched 304 | Reject; do not advance identity or refresh | NOT RUN |
| Wrong type/length/format | Missing or incorrect headers rejected | NOT RUN |
| Truncated/missing/oversized body | No partial handoff; bounded receive | NOT RUN |
| Malformed ETag/SHA mismatch | Reject candidate; preserve accepted identity | NOT RUN |
| Compressed/chunked/conflicting framing | Reject unsupported/ambiguous representation | NOT RUN |
| 3xx/4xx/5xx/206 | No redirect following or display action | NOT RUN |
| Wi-Fi/DNS/Host/connection/HTTP failure | Retain physical image; no blank/error page or old-frame repaint | NOT RUN |
| Cold boot first valid frame | No persisted identity; first valid frame may FULL | NOT RUN |
| Cold boot without network | Keep physical image, no fallback clearing | NOT RUN |
| LKG vs candidate identity | Download alone does not advance accepted identity | NOT RUN |
| Display refusal/TIMEOUT_OR_UNKNOWN | No identity advancement/automatic display retry; display progression stopped | NOT RUN |
| Poll scheduling | No overlap, catch-up burst or unbounded fast retry; poll is not refresh | NOT RUN |
| Successive valid changed frames | Only under C-approved lifecycle, no bypass of one-shot H1 | NOT RUN |

Malformed HTTP tests may use controlled future fixtures; this stage starts no fixture/server and sends no requests.

## 4. Compile and physical validation

Future compile gate: NOT RUN. Verify dedicated environment isolation, private config exclusion, missing config rejection, bounded complete-frame RAM, unchanged historical H1, standard FULL/direction contract, accepted-frame lifecycle, BIN/ELF size and SHA-256. Software tests cannot establish actual RAM or controller state.

Future LAN physical validation: NOT RUN. After separate approval, use content distinct from the old page; preserve source/firmware/frame identities, before/after photos, FPC orientation anchor and process observations. Change business data without firmware rebuild/upload, observe page update and Chinese/field correctness. Observe unchanged polls and network failures without intentional screen clearing. Failure only records evidence; no automatic modification or reflash.
Single photos prove final visible content, not refresh invocation count, absence of BUSY timeout or internal commands. Visual waveform phases do not count firmware FULL calls. No claims of long-term reliability from a short run.

## 5. Persistent verification limits and A-only checks

BUSY timeout fault injection, Deep Sleep, Partial/Fast Refresh, long-duration operation remain NOT TESTED. Exact physical FULL invocation count remains NOT independently verified. Network physical/product functionality remains NOT RUN / NO until future evidence supports it.

A performs only repository audit, cross-document consistency, link/path, sensitive-information and Git checks. No pytest, generated frames, build, server, curl, Wi-Fi, serial or hardware operation.
Commit scope: five STEP017A documents plus PROJECT_STATE.md only. Raw evidence remains local-only/untracked. Commit message: `docs(network): freeze STEP017A LAN product architecture`. No push/tag; stop before B.
