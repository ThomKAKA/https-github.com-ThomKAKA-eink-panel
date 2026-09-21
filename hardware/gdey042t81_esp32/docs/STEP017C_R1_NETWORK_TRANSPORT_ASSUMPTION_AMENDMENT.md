# STEP017C-R1 Network Transport Assumption Amendment

Status: DESIGN AMENDMENT COMPLETE. Tests/compile/runtime/hardware: NOT RUN.
Initial baseline: `99b5e996edc9acd1a12587800954772b3c99651d`.
D implementation commit: `239411582893d05b70fbb5f0d571c078201f5216`.
Pre-flight matched; index empty; only `?? hardware/evidence/`.

## 1. Purpose and evidence

[State reconciliation](STEP017_STATE_RECONCILIATION.md) established that D is
committed but closure NO-GO and approval NO. This narrow amendment resolves the
design assumptions; it does not repair or approve old D code. Original C freeze
remains historical COMPLETE. [Current state](../../../PROJECT_STATE.md) distinguishes
design readiness from implementation and execution evidence.

Audited local package: `framework-arduinoespressif32`, version
`3.20017.241212+sha.dcc1105b` (Arduino-ESP32 2.0.17), espressif32 6.12.0.
Framework references below are relative to
`.venv-hw/pio-core/packages/framework-arduinoespressif32/`; they are local cached
source evidence, not new dependencies or files to submit.

| Finding | Actual source evidence | Consequence |
|---|---|---|
| Reconnect assumption mismatch | `libraries/WiFi/src/WiFiSTA.cpp:477-488` setter/getter only access _autoReconnect; `WiFiGeneric.cpp:1036,1077-1093` separately consumes first_connect and calls disconnect/begin | setAutoReconnect(false) does not establish ownership of every Wi-Fi attempt |
| Failure conflation | D `src/network_progress/main.cpp:20-24` combines validConfig and mode failure; `machine.h:46-48` maps false to fault | Separate deterministic input rejection from runtime initialization failure |
| Cleanup gap | `libraries/WiFi/src/WiFiClient.cpp:220-290` creates raw fd before setsockopt; ROE_WIFICLIENT returns without close; handle transfer occurs later | stop at lines 209-214 cannot release a descriptor it never owned |

The socket is an integer local before transfer, with no RAII owner on the failing
setsockopt branch. The IPv4 no-timeout overload delegates to this path; hostname
overloads resolve then delegate too. D calls the IPv4 explicit 3000 ms overload.
Existing close calls on other error branches do not repair the setsockopt branch.
This is a source-level leak path; runtime incidence is not measured.

WiFiGeneric::mode (lines 1249-1304) can fail during low-level initialization,
hostname/mode/protocol setup or driver start. These are not proof of invalid user
configuration. They are retryable runtime initialization failures; recovery is
permitted, not guaranteed. No framework reset/patch/upgrade is introduced.

## 2. Reconnect alternatives and selected contract

| Option | Assessment | Decision |
|---|---|---|
| A: application owns every physical connection attempt | No public switch for function-static first_connect found in fixed WiFi API/source; flag alone cannot implement the assertion | Not implementable/provable with selected fixed API, rejected |
| B: layered ownership | Framework link retry tolerated; application exclusively controls transactions and scheduling | Selected |
| C: other public control | reconnect() initiates another attempt; disconnect/mode controls are not a public disable switch for the hidden branch | No evidenced replacement selected |

first_connect is a function-local static initialized true. A qualifying disconnect
(not the voluntary ASSOC_LEAVE branch) consumes it once and sets DoReconnect even
with _autoReconnect false. It is not a per-application-attempt retry allowance.
Do not infer absence of lower driver retries or hard radio timing from this fact.
SmartConfig has another begin path (WiFiGeneric.cpp:1149 onward); do not enable
SmartConfig, provisioning or other connection managers.

Application owns poll scheduling, HTTP creation/lifetime, candidate RAM, validation,
display sessions, retry clocks and fault state. Framework events only affect link
state; application callbacks never start transactions or modify the state machine.
There is one application control flow and one frame owner, so a link event cannot
produce a concurrent HTTP request or display call. Recovery during FAILURE_WAIT
does not end the wait; recovery during FAULT_STOP never resumes application work.
Preserve setAutoReconnect(false) and persistent(false) with their honest meanings.
Application initiates at most one begin per connection window and one scheduled
retry per interval. Internal framework retry does not extend/reset that window.

## 3. Transport alternatives and selected ownership

| Option | Reliability, cost and testability | Decision |
|---|---|---|
| A: keep WiFiClient | Application stop can be tested, but known unowned-fd failure can accumulate under repeated polling; 60 s spacing does not bound lifetime exhaustion | Reject for long-running terminal; low probability is not a sufficient guarantee |
| B: application-owned nonblocking BSD/lwIP socket | Explicit acquisition/close seams, existing parser retained; small bounded owner plus connect progression; no new full-frame RAM | Selected minimal sufficient transport |
| C: existing HTTPClient/general client | Fixed HTTPClient convenience path does not establish strict duplicate-header/framing/whole-deadline requirements; no audited alternative with better ownership guarantee | Not selected |

Use fixed SDK `tools/sdk/esp32/include/lwip/lwip/src/include/lwip/sockets.h`:
socket/connect/send/recv/close, fcntl/O_NONBLOCK, select and getsockopt(SO_ERROR)
are already supplied. No third-party library, custom TCP stack, framework copy or
patch. Actual RAM/Flash delta is NOT RUN until E, not a fabricated estimate.

Resource contract:

1. One noncopyable owner, INVALID or OWNED. Successful socket() immediately acquires
   ownership, before setup can fail; creation failure owns nothing.
2. Check fcntl setup. Numeric IPv4 only. Nonblocking connect success proceeds;
   EINPROGRESS waits through zero-timeout readiness polling plus checked SO_ERROR.
   Other connect errors reject. Check deadlines before and after calls/progress.
3. send/recv remain nonblocking. EAGAIN/EWOULDBLOCK/EINTR during readiness/transfer
   mean bounded no-progress under the existing deadline, never a fresh deadline.
4. TCP cap remains 3000 ms and whole transaction 15000 ms from before connect,
   through validation. All existing header/body/idle/EOF budgets stay unchanged.
5. Every owned exit attempts close exactly once through one cleanup path and
   invalidates the local handle; destructors do not repeat explicit close. No
   blind close retry, linger, shutdown dependency, or socket reuse. No timeout
   socket options substitute for application clocks.
6. Failed close/uncertain ownership becomes an internal safety fault: no display,
   new socket or subsequent application transaction. Do not assert a failed close
   released the underlying resource; terminal parking bounds further allocation.
7. Successful cleanup precedes candidate handoff. Source-level ownership does not
   prove all lower-stack/driver/MCU failures leak-free or hard-real-time bounded.

## 4. Definitive failure routing

| Class | Definition | Route |
|---|---|---|
| CONFIG_INVALID | Deterministic malformed/missing private input, invalid IPv4/port/poll/profile or endpoint invariant | FAULT_STOP; no network/display |
| WIFI_INIT_FAILURE | Valid local inputs but subsystem initialization reports failure | FAILURE_WAIT; retry initialization at interval |
| WIFI_ASSOCIATION_FAILURE | Association rejection, no AP or connection window expiry | Cancel application attempt, FAILURE_WAIT |
| NETWORK_DISCONNECTED | Link absent/lost during network transaction | Cleanup/discard, FAILURE_WAIT |
| TCP_CONNECT_FAILURE | Socket allocation/setup/connect/readiness/SO_ERROR failure or timeout with successful cleanup | FAILURE_WAIT |
| HTTP_PROTOCOL_FAILURE | HTTP timeout, malformed response, unexpected status including 4xx/5xx, framing/EOF rejection | No display, cleanup/discard, FAILURE_WAIT |
| FRAME_VALIDATION_FAILURE | Wrong type/length/format, invalid ETag, incomplete/oversized body, SHA mismatch or crypto failure | No display, cleanup/discard, FAILURE_WAIT |
| DISPLAY_INVARIANT_FAILURE | Existing display refusal, BUSY/elapsed ambiguity, invalid display transition or unsafe buffer ownership | FAULT_STOP, accepted identity unchanged |
| INTERNAL_INVARIANT_FAILURE | Illegal state/ownership transition, failed or uncertain descriptor release | FAULT_STOP; no later application work |

FAULT_STOP is exactly deterministic configuration rejection or unsafe internal/
display continuation above, not a catch-all for ordinary network failures.
Preserve existing BUSY precheck, coldInit/prepare refusal, refresh-not-invoked,
post-BUSY HIGH and elapsed >=10000000 us terminal conditions. Lack of independent
physical success evidence alone is not a failure when software conditions are met.

FAILURE_WAIT discards candidate, preserves accepted metadata, performs no display,
and waits the existing interval from completed cleanup. Default 60 s, range
60..86400 s. Failed initialization leaves initialized=false; next checkpoint must
retry WIFI_INIT, never skip directly to association or HTTP. Pure CONFIG_VALIDATE
has no Wi-Fi side effects. Typed initialization outcomes replace the mixed bool.
No rapid retry, automatic reboot, reinitialization loop or network-driven fault exit.

Link loss during a display does not interrupt it or launch network handling;
the next scheduled application checkpoint handles link availability. Framework
radio activity may continue in fault state; this is application parking only.

## 5. D-R1 remediation contract

| Action | Required later change |
|---|---|
| REPLACE | bool configure() with pure config validation and typed Wi-Fi initialization result |
| REFACTOR | WIFI_INIT state, initialized gate and FAILURE_WAIT retry target; classify outcomes explicitly |
| REPLACE | WiFiClient member/connect/fd/stop usage with unique native socket ownership and bounded connect progression |
| DELETE | Claims that every underlying retry is application-owned or all framework-internal cleanup is proven |
| KEEP | Restricted parser, wire semantics, clocks, static T buffer, hash/identities, existing H1 session/direction/stop rules |

D-R1 must update fake-port seams/tests accordingly, without framework or H1 changes.
No production code or test is modified by this amendment. Old D remains PRESENT,
closure NO-GO and NOT APPROVED until remediation and the required later gates.

## 6. Unchanged contracts and verification boundary

[Frame acceptance/LKG](STEP017C_FRAME_ACCEPTANCE_AND_LKG.md) and
[display lifecycle](STEP017C_DISPLAY_LIFECYCLE.md) are UNCHANGED.
Keep endpoint, 200/304, strong T-byte identity, SHA validation, 400x300/15000-byte
single static buffer, serialization, orientation, cold boot and identity advancement.
Only a validated changed candidate is eligible for display; last accepted identity
advances after the unchanged software acceptance conditions, not before display.
Network failure preserves the physical image by issuing no EPD operation; an
already-started display has no rollback promise. Do not redefine physical LKG.
No Partial/Fast, Deep Sleep, Hibernate optimization, error page, push protocol,
cloud, multi-panel or new business semantics.

[Test plan](STEP017C_IMPLEMENTATION_TEST_PLAN.md) adds typed initialization/retries,
framework link recovery without application reentry/overlap, every owned socket
failure path, close-failure parking, repeated failures, rollover and display fault
permanence. All execution items: NOT RUN. E cannot start before D-R1 remediation.

H0/H1 and offline product PASS remain limited-scope history. BUSY fault injection,
Deep Sleep, Partial/Fast and long-duration operation remain NOT TESTED; exact FULL
count remains NOT independently verified. Physical LAN update NOT RUN; network
product verification NO. No compiler, tests, listener, Wi-Fi, HTTP or hardware run.

## 7. Delivery and stop

Only four revised C documents, this amendment and PROJECT_STATE are submitted.
D code/report, reconciliation report, acceptance/display documents, dependencies,
configuration and raw evidence remain unchanged. Static document/link/secret/scope
checks do not constitute runtime approval.
Local commit: `docs(network): amend STEP017C transport assumptions`.
Resolve commit SHA from history; no self-reference. No push/tag. Next stage is
STEP017D-R1 NETWORK FETCHER REMEDIATION, READY but not executed here. E NOT READY.
