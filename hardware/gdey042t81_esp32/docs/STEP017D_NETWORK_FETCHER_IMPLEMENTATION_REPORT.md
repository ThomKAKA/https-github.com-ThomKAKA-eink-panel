# STEP017D — ESP32 Network Fetcher Implementation

Status: IMPLEMENTED, verification/release pending STEP017E. NOT BUILD VERIFIED.
Baseline: `5371460e01b38b9ec4f54438b74cf23d7691dc04`.
Pre-flight: matching HEAD, empty index, only raw evidence untracked.
No commit, upload, serial access, real network request or hardware operation.

## Implementation and ownership

The [frozen design](STEP017C_ESP32_NETWORK_FETCHER_DESIGN.md) remains unchanged.
New files live in `src/network_progress/`:

- `protocol.h`: bounded incremental CRLF/header parser, critical duplicate rejection,
  fixed T format, length, strong ETag and cache policy validation.
- `machine.h`: platform-independent single-owner state machine with injected ports,
  absolute/idle timers, one externally supplied static frame, accepted/candidate/
  attempt identities, EOF gate, spaced retries and terminal display fault.
- `config.h`: mandatory private profile, SSID/password byte validation, numeric IPv4,
  port and poll range validation. No default credentials or default Host.
- `main.cpp`: Wi-Fi STA, WiFiClient-owned fd, nonblocking send/recv, checked mbedTLS
  SHA-256 and fresh unchanged H1 adapter per display attempt.

Only `esp32-m1-network-progress` compiles the new entry. Historical four environment
definitions remain unchanged; default builds see no active network entry. The new
environment retains the H1 macro/profile checks and adds EINK_NETWORK_PROGRESS.
There is no new driver, dependency, Host, Renderer or conversion implementation.

Network exclusively writes the static 15000-byte T array until complete validation;
display reads it only after orderly EOF and owner close. The MCU does not transform
pixels. No second frame, stack frame, persisted identity or runtime JSON exists.
Header/request buffers are bounded metadata, not additional frame copies.

## Protocol and scheduling

[C acceptance](STEP017C_FRAME_ACCEPTANCE_AND_LKG.md) and
[timeouts](STEP017C_NETWORK_CONFIG_AND_TIMEOUTS.md) define the implemented profile.
200 requires complete 15000 bytes, the fixed type/format/cache headers and exact
SHA-256/ETag identity. 304 requires the sent accepted identity, matching headers,
no length and no body. Encoding headers, duplicate critical fields, unexpected
statuses, extra bytes, reset and missing EOF are rejected. This is deliberately
not a general HTTP client. Actual Host orderly-close compatibility is NOT RUN.

Wi-Fi: 15 s; TCP: 3 s; send: 1 s; headers/body: 5 s each; receive idle/EOF: 2 s;
HTTP total: 15 s including hash validation. Unsigned elapsed comparisons use >=.
Per-tick work is bounded; progress does not restart absolute deadlines. Poll/retry
starts after transaction/session cleanup, defaults to 60 s, range 60..86400 s.
No DNS, redirects, chunking, automatic reconnect or catch-up requests.

Network failures retain accepted metadata and never invoke EPD. A candidate is not
accepted until the display function returns its conservative software result.
Display refusal/unknown is terminal: later ticks make no port calls at all.
Logs contain numeric states/status and software result labels, not private fields.

## Display lifecycle

HTTP closed -> BUSY idle check -> fresh H1 object -> SPI setup -> coldInit ->
prepareColdStartFullFrame -> prepared BUSY check -> refreshOnce -> elapsed/BUSY
classification -> destruction without EPD cleanup -> accepted identity or FAULT_STOP.

H1 retains initial=true, fast-full disabled, full 0x26/0x24 writes, mirror_y=true
and pgm=false. No EPD operation follows refresh within that session. A later session
requires a successful prior software result, complete poll interval and changed
validated T frame. Repeated controller initialization is NEW and NOT physically
verified; object recreation does not power-cycle hardware. Software acceptance
does not prove a BUSY signal is truthful or a physical page succeeded.

## Private configuration (not created)

Only the new environment searches `.build/network-progress-private/`. Missing
headers deliberately prevent its build. Future authorized local configuration:

- `display_config.local.h`: unchanged H1 GPIO/profile confirmation plus
  `NETWORK_PROGRESS_PRIVATE_PROFILE=1` (BUSY/RST/DC/CS/SCK/MOSI 13/12/14/27/18/23).
- `network_config.local.h`: explicit string-literal NETWORK_SSID and
  NETWORK_PASSWORD, NETWORK_HOST_IPV4 as four numeric octets, NETWORK_HOST_PORT
  as integer; optional NETWORK_POLL_SECONDS (default 60).

No actual private headers or credentials were generated. Password accepts explicit
open-network empty string, 8..63 bytes or 64 hex digits for personal-network use.
Numeric address checks reject unspecified/loopback/multicast/reserved classes;
deployment must additionally confirm intended trusted LAN and subnet unicast.
Do not publish credential-bearing firmware or logs. No TLS/auth is claimed.

## Verification inventory and limits

Added [C++ harness](../../../tests/cpp/test_network_progress.cpp) tests production
headers through fake time/socket/Wi-Fi/display ports, not a Python reimplementation.
It covers acceptance/rejection examples, duplicate/oversized headers, body framing,
EOF, identity handoff, unchanged/304, repeated sessions, timeout, rollover and
permanent fault parking. Its hash port is intentionally mocked for orchestration:
it does NOT independently verify SHA-256 or real ESP32 HAL behavior.

- New C++ tests: NOT RUN. No g++, clang++ or cl found on PATH; none installed.
- Existing Python regression: NOT RUN here; historical 364 passed is not a D result.
- All five PlatformIO builds, negative configuration builds, ELF/RAM/Flash analysis:
  NOT RUN, deferred to E. No firmware hashes or build PASS claimed.
- Full C test matrix, independent real hash/byte checks, exact deadline boundaries,
  socket reset/partial I/O, display fault mocks and actual TCP EOF compatibility:
  STEP017E pending; current harness is initial coverage, not full gate closure.
- Wi-Fi/LAN, repeated physical updates, BUSY fault injection, sleep, partial/fast,
  long-duration behavior: NOT RUN / NOT TESTED as historically applicable.

Source/link/whitespace and protected-file checks are separate static checks. D is
implementation ready for review, not authorization to run E/F or proof of network
product function. NETWORK PRODUCT FUNCTION VERIFIED remains NO.

Protected baseline comparison: all 179 captured existing tracked/evidence file
hashes unchanged (state and permitted PlatformIO file excluded). No source file
outside the dedicated new entry was edited. Current configuration diff adds only
the ten-line dedicated environment. Git index remains empty; no commit created.
