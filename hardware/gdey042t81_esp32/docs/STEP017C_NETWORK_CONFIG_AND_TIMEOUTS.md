# STEP017C — Network Configuration and Timeouts

Status: DESIGN FROZEN; no private configuration created, APIs not executed.
C-R1 ownership/failure revision COMPLETE; see [amendment](STEP017C_R1_NETWORK_TRANSPORT_ASSUMPTION_AMENDMENT.md).
See [architecture](STEP017C_ESP32_NETWORK_FETCHER_DESIGN.md) and
[state machine](STEP017C_NETWORK_STATE_MACHINE.md).

## 1. Configuration boundary

Future private directory: `.build/network-progress-private/` relative to hardware
project. Only the new environment includes it. Use display_config.local.h for
unchanged H1 assertions plus NETWORK_PROGRESS_PRIVATE_PROFILE=1 and a separate
network_config.local.h for network fields. Missing/mismatched profiles are build
errors; malformed network values also fail closed before connection. Do not fall
back to examples. C creates neither templates nor credentials.

| Logical field | Frozen rule | Handling |
| --- | --- | --- |
| Wi-Fi SSID | Explicit, nonempty, at most 32 bytes; no embedded NUL | Private, no logs or commit |
| Wi-Fi password | Explicit configured value; use current framework-supported personal-network credentials, no enterprise/provisioning flow | Secret, no logs or commit; connection rejection is bounded failure |
| Host IPv4 | Explicit numeric intended LAN unicast address, no hostname/URL/scheme/path | Private topology, no routine logs/commit |
| Host port | Explicit integer 1..65535 | Non-secret parameter; stored with private endpoint configuration |
| Endpoint | Fixed /api/panels/progress/frame | Tracked protocol constant, not a configurable business/source selector |
| Poll interval seconds | Default 60; accepted integer 60..86400 | Non-secret product configuration; invalid value rejects, no clamping |

Credentials are not encrypted merely by being in ignored headers: future firmware
may contain them and must also remain local-only. Never publish credential-bearing
BIN/ELF, private compiler dumps or logs. Example configuration contains placeholders
only. Actual SSID/password/Host must not be pasted into documents or PROJECT_STATE.

Retain H1 GPIO BUSY/RST/DC/CS/SCK/MOSI = 13/12/14/27/18/23 and board/profile
guards. No network configuration unlocks default or historical environments.
No settings UI, NVS identity, discovery, TLS/auth, DHCP-server changes or routing setup.
Device can use framework DHCP for its own interface; Host target is explicit IPv4.
Trusted LAN/non-sensitive content only; [A security](STEP017A_NETWORK_SECURITY_BOUNDARY.md)
still forbids public exposure/port forwarding. ETag is not authentication.

## 2. Exact timer policy

| Timer | Milliseconds | Start / behavior |
| --- | --- | --- |
| Wi-Fi connect window | 15000 | Before one begin attempt; includes waiting for connection |
| TCP connect | 3000 | Before IPv4 connect; no DNS |
| Request send | 1000 | First send attempt; partial progress never restarts absolute timer |
| Complete response header | 5000 | Request fully sent |
| Body receive | 5000 | End of header section for 200 |
| Receive idle | 2000 | Start of receive state / last received byte |
| Response end | 2000 | After byte 15000 or 304 header completion; require EOF |
| Whole HTTP transaction | 15000 | Immediately before TCP connect, through final candidate validation |
| Poll/retry | configured seconds x 1000 | After complete success or failure cleanup; default 60000 |

Earliest applicable deadline wins. Response-end is a distinct bounded state, not
an extension allowing the whole budget to exceed 15 seconds. All expiry comparisons
use >= and wrap-safe unsigned elapsed; maximum configured interval is below half
the 32-bit millisecond range. No use of civil time, blocking delay for an entire
transaction, catch-up scheduling or current page timestamp generation.

Finite short delay/yield is allowed between no-progress checks. Frame hashing and
parsing have fixed input bounds. These are application software limits, not
preemptive hard-real-time guarantees for a hung driver/MCU. No timer can safely
abort synchronous GxEPD2 mid-command; display policy is separately frozen.

## 3. API choices and socket ownership

Use current WiFi persistent(false), setAutoReconnect(false), mode(WIFI_STA),
begin/status/disconnect. The flag disables ordinary automatic retry only; tolerate
the fixed framework's first_connect retry. Application attempts once per configured
interval after failure, without erasing AP storage. No event callback launches
HTTP, frame processing or EPD operations, ends a wait or resets deadlines.
Pure configuration validation and typed Wi-Fi initialization are distinct steps.
WIFI_INIT_FAILURE is retryable without assuming every driver failure will recover.

Use existing lwIP/BSD socket APIs, not WiFiClient. Immediately own each successful
socket() result; check fcntl nonblocking setup. Connect numeric IPv4 with EINPROGRESS
handled by zero-wait readiness polling and checked SO_ERROR; retain TCP 3000 ms and
whole HTTP 15000 ms deadlines. send/recv stay nonblocking. Interpret EAGAIN,
EWOULDBLOCK/EINTR as bounded no-progress; EOF only as specified by the frame contract.
No DNS, socket reuse, blocking Stream helpers, SO_SNDTIMEO/SO_RCVTIMEO-based timing,
linger or shutdown dependency. Uniform close on every owned exit; do not blindly
retry close. A failed close or ownership uncertainty stops further application
work/allocations. Successful close is required before frame handoff.
Do not claim immunity to lower-stack/MCU failure; source guarantees and E evidence
are separate. This is a small transport owner, not a new networking framework.

Use mbedtls_sha256_ret with is224=0 and check its return code. No downloaded crypto,
HTTP library or modified framework. D/E must verify exact signatures, error handling,
resource release and bounded behavior against the pinned package before release.
HTTPClient read/idle timeout and a post-GET elapsed check are not substitutes.

## 4. Retry, logging and fault parking

Network failure discards candidate/connection and preserves accepted metadata.
Retry only after the configured interval; no rapid loop, reset or error-page refresh.
Initialization, association, link, TCP, HTTP and candidate failures are retryable
after cleanup and the same interval. Invalid local configuration, internal safety
invariant failure, or display refusal/unknown enters terminal FAULT_STOP with
application delay only; no network or display retry until a separate manual reboot.

Minimal diagnostic logs may contain state, HTTP status, rejection category,
candidate acceptance, session invocation and software timing classification. Never
print passwords, SSID, full private config, raw HTTP payload/header dumps or Host
address. Logs cannot claim physical success or serve as a dependency for correctness.
No serial monitor is opened in C; future log collection needs separate authorization.
