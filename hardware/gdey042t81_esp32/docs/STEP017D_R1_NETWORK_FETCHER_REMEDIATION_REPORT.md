# STEP017D-R1 Network Fetcher Remediation Report

Status: IMPLEMENTED; static remediation review PASS; executable verification NOT RUN.
This is not STEP017E, a compiled firmware release, or a network/physical PASS.

## 1. Baseline and scope

- Expected and actual initial HEAD: `0e2cc29f92c99c842759519624cf63ad1f20af6c`.
- C-R1 amendment commit: same baseline, `docs(network): amend STEP017C transport assumptions`.
- Initial D implementation: `239411582893d05b70fbb5f0d571c078201f5216`.
- Initial index empty; only `?? hardware/evidence/`. State: C-R1 COMPLETE, D-R1 READY.
- Authority: [C-R1 amendment](STEP017C_R1_NETWORK_TRANSPORT_ASSUMPTION_AMENDMENT.md).
- [Old D report](STEP017D_NETWORK_FETCHER_IMPLEMENTATION_REPORT.md) and
  [reconciliation](STEP017_STATE_RECONCILIATION.md) remain unchanged history.

Modified: `src/network_progress/main.cpp`, `machine.h`,
`tests/cpp/test_network_progress.cpp` (repository-root tests), and
[PROJECT_STATE](../../../PROJECT_STATE.md).
Created: `src/network_progress/transport.h`, repository-root
`tests/cpp/test_network_transport.cpp`, and this report.
The source paths are relative to this hardware project.

KEEP: config.h, protocol.h, PlatformIO, H1, Host/Python, Renderer, conversion,
frozen design documents, old report, dependencies and evidence. No private
configuration or credentials created. No environment/dependency/version change.

## 2. Three blockers and implementation decisions

| Old blocker | Remediation in source | Execution evidence |
|---|---|---|
| Ownership of all Wi-Fi attempts falsely assumed | Retain persistent(false)/setAutoReconnect(false), explicitly tolerate first_connect; only Machine schedules transactions; no application event handler | NOT RUN |
| bool configure conflates invalid input with runtime init | ConfigResult plus WifiInitResult, WifiInit state, initialized flag and initialization retry gate | NOT RUN |
| WiFiClient pre-ownership cleanup gap | Remove WiFiClient member/connect/fd/stop path; unique nonblocking SocketOwner with checked explicit release | NOT RUN |

These are REMEDIATED IN SOURCE, not VERIFIED FIXED. No C-R1 design conflict found.
Framework radio/link work can continue; fault parking stops application work only.
Link recovery during FAILURE_WAIT never shortens the interval or changes state
asynchronously. No application callback, task, concurrent HTTP or display work added.

## 3. Native transport and API audit

Pinned package: Arduino-ESP32 `3.20017.241212+sha.dcc1105b` (2.0.17).
Read-only SDK evidence, relative to `.venv-hw/pio-core/packages/framework-arduinoespressif32/`:

- `tools/sdk/esp32/include/lwip/lwip/src/include/lwip/sockets.h` declares
  lwip_socket, lwip_fcntl, lwip_connect, lwip_select, lwip_getsockopt,
  lwip_send, lwip_recv and lwip_close; SO_ERROR, F_GETFL/F_SETFL, O_NONBLOCK,
  MSG_DONTWAIT and fd_set range rules are present.
- `tools/sdk/esp32/include/lwip/port/esp32/include/lwipopts.h` defines the socket
  descriptor offset and ESP_SOCKET wrappers. Native readiness validates the SDK
  range before FD_SET, with fd+1 and zero timeval for select.
- `lwip/errno.h` supplies EINPROGRESS, EAGAIN/EWOULDBLOCK and EINTR semantics.
- `libraries/WiFi/src/WiFiGeneric.cpp:1077-1093` retains the separate first_connect
  retry; no framework edit or claim of exclusive low-level reconnect ownership.

NativeSockets is a thin borrowed-descriptor syscall seam. SocketOwner alone stores
the owned fd; INVALID is -1. Copy/move is disabled. Successful creation assigns
ownership before checked F_GETFL/F_SETFL. Numeric IPv4 is packed in network byte
order, no hostname resolver. Connect is immediate success, pending EINPROGRESS,
or failure. Pending progression uses zero-wait select and checked SO_ERROR;
writable alone is never accepted. No socket timeout options, linger, shutdown,
socket reuse, Stream convenience calls or generic HTTP client are introduced.

send/recv use MSG_DONTWAIT. Transfer/readiness transient errors mean bounded
no-progress; EOF remains distinct from pending/error. Each tick is bounded and
the main loop retains delay(1). The existing parser owns protocol validation,
not the transport. There is no new full-frame buffer or dynamic response storage.

## 4. Timing, failure routing and resource release

Machine starts the whole transaction clock once before beginTcp. Later pollTcp
calls do not restart it. TCP is 3000 ms, send 1000 ms, header/body 5000 ms,
idle/EOF 2000 ms, whole HTTP 15000 ms through final hash validation. Earliest
deadline wins, using unsigned elapsed >= budget before/after progress. Poll/retry
starts after cleanup or software display acceptance, default 60 s, range 60..86400 s.
These are cooperative software limits, not hard guarantees against a stalled stack.

| Failure | Route |
|---|---|
| CONFIG_INVALID | FAULT_STOP before Wi-Fi initialization |
| WIFI_INIT_FAILURE | FAILURE_WAIT; initialized=false; retry WifiInit, not HTTP |
| WIFI_ASSOCIATION_FAILURE | Cancel application attempt, FAILURE_WAIT |
| NETWORK_DISCONNECTED | Close candidate transaction, discard candidate, FAILURE_WAIT |
| TCP_CONNECT_FAILURE | Close if owned, FAILURE_WAIT |
| HTTP_PROTOCOL_FAILURE | Close, discard candidate, zero display, FAILURE_WAIT |
| FRAME_VALIDATION_FAILURE | Same; includes body/SHA/crypto rejection |
| DISPLAY_INVARIANT_FAILURE | Existing display refusal/unknown, FAULT_STOP without identity promotion |
| INTERNAL_INVARIANT_FAILURE | Invalid owner/state or failed release, FAULT_STOP |

Ordinary response metadata rejected by the unchanged parser is classified as
HTTP_PROTOCOL_FAILURE; body/hash failures as FRAME_VALIDATION_FAILURE. Both have
identical frozen candidate rejection, cleanup and retry behavior.

finish() is the single fd close path. Every owned exit calls releaseSocket once,
then invalidates the local handle; repeated finish does not call close again.
Setup/connect failures finish inside SocketOwner; later Machine cleanup is idempotent.
Machine timeouts/protocol failures finish through finishTcp. Failed release latches
the owner fault and parks Machine: no retry-close, allocation, request or display.
Failed close is NOT asserted to have freed a lower-stack resource. No destructor
performs deferred close. The production owner is static and explicit cleanup is
required before candidate handoff. Unknown ownership never resumes normal work.

### Descriptor path audit (static, not fault injection)

In the table, "close" means one explicit attempt for an owned descriptor followed
by local invalidation. A failed attempt overrides the normal route with FAULT_STOP.

| Path | Created / owned | Release and next state | Display reachable for candidate? |
|---|---|---|---|
| socket failure | No / no | No close; FAILURE_WAIT | No |
| F_GETFL or F_SETFL failure | Yes / yes | Owner close; FAILURE_WAIT | No |
| setsockopt failure | N/A, no setsockopt used | N/A | N/A |
| connect immediate failure | Yes / yes | Owner close; FAILURE_WAIT | No |
| connect timeout | Yes / yes | Machine close; FAILURE_WAIT | No |
| select or SO_ERROR failure | Yes / yes | Owner close; FAILURE_WAIT | No |
| connect pending | Yes / yes | Retain until bounded completion/failure | Not yet |
| partial send | Yes / yes | Retain within original deadline | Not yet |
| send error / timeout | Yes / yes | Machine close; FAILURE_WAIT | No |
| recv error / timeout | Yes / yes | Machine close; FAILURE_WAIT | No |
| malformed header | Yes / yes | Machine close; FAILURE_WAIT | No |
| oversized header | Yes / yes | Machine close; FAILURE_WAIT | No |
| rejected status | Yes / yes | Machine close; FAILURE_WAIT | No |
| short body | Yes / yes | Machine close; FAILURE_WAIT | No |
| oversized body | Yes / yes | One-byte probe; Machine close; FAILURE_WAIT | No |
| invalid ETag | Yes / yes | Parser rejection; Machine close; FAILURE_WAIT | No |
| SHA mismatch / crypto error | Previously closed / no | No second close; FAILURE_WAIT | No |
| missing EOF / extra byte | Yes / yes | Machine close; FAILURE_WAIT | No |
| valid 304 | Yes / yes until EOF | Machine close; POLL_WAIT | No |
| unchanged valid 200 | Closed before hash / no | POLL_WAIT, no second close | No |
| changed valid 200 | Closed before hash / no | DISPLAY_PENDING only after validation | Yes |
| failed close / illegal ownership | If owned, one release attempt | Local invalid, FAULT_STOP | No |

Source claim: every application-owned descriptor has an explicit close path before
ownership is relinquished. This does not prove all framework resources leak-free.

## 5. Preserved display and frame boundaries

The EspPort display function is unchanged. The request serialization and mbedTLS
SHA-256 implementation are unchanged. protocol.h and config.h are unchanged.
One static 15000-byte T array remains exclusive: receive -> validate -> display.
No MCU flip/rotation, business JSON, error page or second historical frame.
304/unchanged 200 never displays. Accepted identity advances only after the
existing conservative display return, not merely a validated download.

Fresh small H1 object -> SPI -> coldInit(initial=true, fast-full disabled) -> full
0x26/0x24 preparation -> guarded refreshOnce -> elapsed/BUSY -> no further session
EPD commands. No powerOff, hibernate, clear, partial/fast or automatic display retry.
Only a later accepted scheduling checkpoint may open another valid changed session.
FAULT_STOP makes later ticks return without even a Port clock/status query.
Link loss during display does not interrupt the synchronous existing session.
Physical rollback, exact FULL count and successful physical pixels are not claimed.

## 6. Verification inventory and remaining E gates

Updated [state harness](../../../tests/cpp/test_network_progress.cpp); new
[owner harness](../../../tests/cpp/test_network_transport.cpp). Tests exercise
production headers with fake ports/syscalls: initialization retries, wait checkpoints,
connect progression/deadlines/rollover, partial I/O, transport and protocol failures,
cleanup permanence, 304/unchanged/changed identity and display parking.
Owner tests cover setup/connect/readiness/error failures, repeated failures,
invalid access, no copying, explicit close and close-failure latching.
The native syscall seam itself still requires target/API verification in E;
fake setup failure does not independently execute native F_GETFL/F_SETFL.

- C++ tests written, NOT RUN. No compiler invoked or installed.
- Python regression NOT RUN; historical 364 is not a D-R1 test result.
- PlatformIO/compile/link/firmware hash: NOT RUN / NOT AVAILABLE.
- Wi-Fi, HTTP/LAN, upload, serial/COM and hardware: NOT RUN.
- Scope, C-R1 fidelity, source ownership, links, secrets and Git diff: static checks only.

E must execute the harnesses, verify fixed native errno/API behavior and all five
builds, resource sizes, firmware identities, negative configuration isolation and
the remaining frozen test matrix. TCP EOF compatibility and actual resource behavior
are not proved here. No test/build/physical PASS is inferred from this commit.
NETWORK PRODUCT FUNCTION VERIFIED: NO. H0/H1 and offline limited-scope PASS retained;
BUSY injection, Deep Sleep, Partial/Fast and long-duration behavior remain unverified.

## 7. State and delivery

D initial closure NO-GO remains history. D-R1 IMPLEMENTED; three blockers REMEDIATED
IN SOURCE, verification NOT RUN. Overall approval PENDING STEP017E VERIFICATION.
Next actionable stage E, separately authorized, not started by this task.
Only the seven source/test/report/state files listed above are committed; evidence
remains local-only/untracked. No push/tag or dependency/configuration change.
Commit message: `fix(network): remediate STEP017D fetcher ownership`.
Resolve the actual successor SHA from Git; no self-referential hash in this report.
