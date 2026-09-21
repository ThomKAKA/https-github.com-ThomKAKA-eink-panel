# STEP017C — Implementation and Verification Gates

Status: PLAN FROZEN; every new execution item below is NOT RUN.
C-R1 additions are design requirements only; D-R1 remediation precedes E readiness.
This document grants no implementation, build, listener, serial or hardware permission.
Contracts: [design](STEP017C_ESP32_NETWORK_FETCHER_DESIGN.md),
[states](STEP017C_NETWORK_STATE_MACHINE.md), [acceptance](STEP017C_FRAME_ACCEPTANCE_AND_LKG.md),
[display](STEP017C_DISPLAY_LIFECYCLE.md), [timeouts](STEP017C_NETWORK_CONFIG_AND_TIMEOUTS.md).

## 1. STEP017D implementation gate

Input: approved six C documents, pinned framework and unchanged H1/Host baseline.
Output: dedicated network configuration, restricted receiver/validator, one static
frame buffer, identity/state-machine tests, isolated entry/environment and session
orchestration. No copied driver, changed historical H1, Host fix or new dependency.
Default and existing H1/Progress environments remain protected. If the frozen
API/timeout/destructor assumptions fail, stop and report instead of widening scope.
No upload/hardware, Partial/Fast, sleep, automatic reset, cloud, UI or provisioning.

## 2. STEP017E software and compile gate

Use deterministic fake clock/socket/Wi-Fi/display seams for state and parser tests;
keep real frame bytes and independent hash/orientation checks. Do not replace tests
of production C++ logic with a Python reimplementation and call it runtime verified.
Available host C++ compiler only; absent compiler means NOT RUN / BLOCKED, no install.
Controlled TCP fixtures and actual Host Connection: close compatibility need their
own authorized E test execution; B TestClient does not prove socket behavior.

| Case | Required evidence / expected outcome | Execution |
| --- | --- | --- |
| Boot/config absent or invalid | No fallback, no display; terminal config failure | NOT RUN |
| Boot without Wi-Fi | Bounded attempt, image untouched, spaced retries | NOT RUN |
| Connect/disconnect/reconnect | Application scheduling remains exclusive despite tolerated framework link retry | NOT RUN |
| Valid 200 | Exact type/format/length/cache/ETag, 15000 bytes and EOF before handoff | NOT RUN |
| Valid 304 | Existing sent identity matches, body absent, zero display | NOT RUN |
| Unsolicited/mismatched 304 | Reject, no identity advancement | NOT RUN |
| Wrong type/length/format/cache | Reject missing, conflicting or malformed headers | NOT RUN |
| Missing/weak/malformed ETag | Reject uppercase digest, wrong quotes/size/nonhex/W/ | NOT RUN |
| Duplicate critical headers | Reject identical or differing duplicates; never last-value-wins | NOT RUN |
| Header syntax/limits | Reject folding, invalid controls, >512-byte line or >4096 section | NOT RUN |
| Slow dribble headers/body | Absolute deadline wins despite continuing bytes | NOT RUN |
| Truncated/oversized body | Reject 14999/15001; no padding, truncation or out-of-bounds write | NOT RUN |
| End confirmation | EOF accepted; reset/extra byte/no-close past limit rejected | NOT RUN |
| Encoding/status | Reject chunked/compressed, 1xx/206/redirect/4xx/5xx, no follow | NOT RUN |
| SHA/API error | Body mismatch/crypto failure rejected, old identity retained | NOT RUN |
| Same pixels/new event | Unchanged 200 hash causes zero display | NOT RUN |
| Changed frame | One candidate/session, identity only after software acceptance | NOT RUN |
| Buffer ownership | No mutation during display, no second full buffer/stack frame | NOT RUN |
| Timing and wrap | All exact thresholds, uint32 rollover, partial progress, no catch-up | NOT RUN |
| HTTP resource ownership | Every branch closes once, no double-close/buffered/native mix | NOT RUN |
| Session sequence | Fresh object, guarded BUSY, cold init, dual RAM, one standard FULL | NOT RUN |
| Session end | Destruction emits no EPD/SPI shutdown; no post-refresh cleanup | NOT RUN |
| Display refusal/unknown | Identity unchanged; permanent FAULT_STOP including future requests | NOT RUN |
| Repeated changed frames | Separate sessions only after accepted prior session and interval | NOT RUN |
| Host unavailable/recovery | Failure retains image/identity; later valid changed frame eligible | NOT RUN |
| Cold reboot | No persisted ETag; first valid frame may refresh again | NOT RUN |
| Direction | T unchanged in receiver, independent L->T->P identity | NOT RUN |

Run full existing Python regression including Host endpoint tests; historical B
baseline is 364 passed, not a prefilled future result. Report actual totals/skips.
Compile all five environments: esp32dev, esp32-m1, esp32-m1-h1,
esp32-m1-progress, esp32-m1-network-progress. Use existing isolated toolchain/cache;
no install/upgrade. Record exit codes, versions, RAM/Flash, BIN/ELF paths/sizes/SHA-256.
Confirm static 15000-byte buffer and no forbidden code in old environments; negative
configuration builds use isolated ignored copies. Missing tool/compiler is BLOCKED.
Scan source/staging/artifact handling for secrets, while recognizing future private
credentials can be compiled into local firmware and must not be published.

## 3. STEP017F physical gate

Input: E evidence and separately authorized LAN deployment/upload/hardware session.
Output: observed end-to-end LAN business updates, not just successful GET or build.
Host listening/firewall scope must be reviewed first; C changes neither. Confirm
the actual Host honors close under the approved device transaction budget.

| Scenario | Observation and provenance | Execution |
| --- | --- | --- |
| Initial connection/frame | Specified LAN reached, accepted final T actually displayed | NOT RUN |
| Two subsequent business changes | New Host T/ETag delivered at next poll, new page without rebuild/upload | NOT RUN |
| Unchanged/304 cycles | Process observation of no refresh, diagnostic correlation | NOT RUN |
| Host loss and recovery | Image retained during outage, later valid changed page updates | NOT RUN |
| Direction/Chinese/content | FPC anchor, readable fields, final stable page/photo | NOT RUN |
| Session provenance | Firmware identity, frame identities, event/snapshot and observed process | NOT RUN |

Failures are recorded, not automatically fixed, reflashed or retried as display
recovery. After a display FAULT_STOP, network restoration must not restart display.
Hardware failure injection needs separate authorization; software mock faults do
not count as physical BUSY tests. Photos prove visible content only, not exact FULL
invocation count, BUSY success, Deep Sleep or electrical health. Short repeated
updates do not establish long-duration reliability/endurance.

## 4. C completion and remaining boundaries

This section preserves original C completion scope/message; current C-R1 delivery
scope is in the [amendment](STEP017C_R1_NETWORK_TRANSPORT_ASSUMPTION_AMENDMENT.md).

C checks document links, cross-contract consistency, sensitive patterns, protected
file/evidence hashes and Git diffs only. pytest, C++ tests, PlatformIO build,
HTTP runtime tests, Wi-Fi, LAN, serial and hardware operations are NOT RUN in C.
Only six new documents plus PROJECT_STATE may be staged. Raw evidence stays local.
Update C design status only after design checks; preserve B software evidence and
H0/H1/offline limited-scope PASS. NETWORK PRODUCT FUNCTION VERIFIED remains NO.

Commit: `docs(network): freeze STEP017C ESP32 fetcher design`.
No push/tag. Stop before D. This is a design acceptance, not an implemented Fetcher,
compiled firmware or physical repeated-update safety certificate.

## 5. C-R1 additions for D-R1 and E

D-R1 input is the amended design, not approval of commit 2394115. Preserve parser,
H1, single buffer, deadlines and identity semantics; change only typed initialization,
retry routing and transport ownership as specified in the amendment.

| Case | Required evidence / expected outcome | Execution |
|---|---|---|
| CONFIG_INVALID | No initialization/association/HTTP/display; FAULT_STOP | NOT RUN |
| WIFI_INIT_FAILURE then success | FAILURE_WAIT, full interval, retry WIFI_INIT before association/HTTP | NOT RUN |
| Repeated initialization/association failures | No tight retry, no display, no false initialization success | NOT RUN |
| Framework first-connect recovery during wait | No early request, reentry, parallel HTTP/display or timer reset | NOT RUN |
| Link loss during receive/display/fault | Candidate rejected in receive; existing display session not interrupted; fault never resumes | NOT RUN |
| socket creation failure | No owned fd and no close of invalid fd; scheduled retry | NOT RUN |
| fcntl/connect/readiness/SO_ERROR failure or timeout | Exactly one close for each owned fd, unchanged whole deadline | NOT RUN |
| Partial send/receive and EINTR/EAGAIN | Bounded progress checks, no restarted absolute timer | NOT RUN |
| Repeated TCP/protocol/frame failures | No leaked application-owned fd, no duplicate close or accepted-identity change | NOT RUN |
| close failure / ownership ambiguity | Terminal internal invariant fault, no retry-close or new allocation | NOT RUN |
| Display refusal/unknown | Unchanged session safety; no future application transaction | NOT RUN |
| Baseline isolation | Existing environments, H1, frame format and orientation unchanged | NOT RUN |

Mocks must exercise the production ownership wrapper, including failure before
and after ownership acquisition. They do not prove lower-stack cleanup under
arbitrary faults. Real fixed-target resource/timing checks remain separate E/F
evidence, with no long-duration PASS inferred from bounded tests.
