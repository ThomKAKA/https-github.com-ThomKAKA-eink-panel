# STEP017C — ESP32 Network Fetcher Design

Status: DESIGN FREEZE COMPLETE; device implementation and execution NOT RUN.
Parent baseline: `9a23df88ed85466f52847c45c20933f942159979`.
Initial gate: HEAD matched, index empty, only `?? hardware/evidence/`.

## 1. Problem and preserved evidence

The problem is not merely HTTP GET: it is evolving a one-shot display client into
a bounded LAN client without allowing invalid frames, network failure or ambiguous
display results to cause uncontrolled EPD operations. REPEATED DISPLAY LIFECYCLE
is the principal gate.

[State](../../../PROJECT_STATE.md) records STEP017A/B COMPLETE, STEP016D-C offline
business display PASS (limited scope) and evidence closure COMPLETE. H0/H1 retain
their historical scope. Network product verification remains NO. BUSY fault
injection, Deep Sleep, Partial/Fast Refresh and long-duration operation remain
NOT TESTED; exact physical FULL invocation count is not independently verified.

## 2. Audited Host contract

Read-only audit of [A contract](STEP017A_FRAME_HTTP_CONTRACT.md),
[A policy](STEP017A_UPDATE_AND_FAILURE_POLICY.md), [B report](STEP017B_HOST_FRAME_ENDPOINT_REPORT.md),
[route](../../../server/main.py), [publisher](../../../services/progress_frame.py),
[store](../../../services/event_store.py) and [tests](../../../tests/test_progress_frame.py)
found no blocking contract conflict. B's 364 passed result is historical, not rerun.

- GET `/api/panels/progress/frame`, one Host-configured source; no device source selector.
- Final immutable 15000-byte T publication, quoted lowercase SHA-256 strong ETag.
- 200 carries exact bytes; matching conditional request returns bodyless 304.
- Failed rendering retains an old valid record; no record means 503.
- Publisher serializes renders; store `_if_current` rechecks and publishes under
  the ingestion lock. Stale candidates cannot overwrite current publication.
- Response headers/body use the same record. Actual TCP framing/close behavior
  remains untested; C does not silently change Host implementation.

## 3. Architecture and library decision

```text
Host business snapshot -> strict Renderer L -> one PC L-to-T transform -> HTTP
-> complete candidate T -> validation/change detection -> isolated display session
```

ESP32 owns configuration, Wi-Fi STA, bounded requests, protocol/body validation,
RAM ownership, identity and display scheduling. It does not parse business JSON,
contact an Agent, render fonts/UI, generate images or transform T. Polling is not
refreshing. No error/connecting/blank page is generated.

Use one application control flow, no new FreeRTOS task/callback display pipeline.
Framework Wi-Fi tasks remain framework internals; this is not a claim of a
single-threaded operating system. No HTTP/display overlap and no queued candidates.

| Candidate | Local audit / decision |
| --- | --- |
| Arduino HTTPClient GET | Not selected: `handleHeaderResponse` uses idle timing and readStringUntil, Content-Length toInt, and overwrites collected duplicate headers; setTimeout alone does not prove the strict deadline/header contract |
| WiFiClient-owned socket + restricted HTTP receiver | Selected; fixed GET/200/304 profile, bounded parser and nonblocking transfer; no general HTTP stack |
| Additional client library / custom TCP stack | Not needed; no new third-party dependency |

Pinned platform: espressif32 6.12.0; installed Arduino package
`3.20017.241212+sha.dcc1105b` (Arduino-ESP32 2.0.17); GxEPD2 1.6.9 pinned by
existing [PlatformIO configuration](../platformio.ini).
Local audit sources below are cache-relative, not repository-distributed files:

- `.venv-hw/pio-core/packages/framework-arduinoespressif32/libraries/WiFi/src/`:
  WiFiSTA begin/status/disconnect/setAutoReconnect, WiFiGeneric persistent,
  WiFiClient IPv4 connect(timeout), fd and stop.
- Same package `libraries/HTTPClient/src/HTTPClient.cpp`: header parsing limitations.
- Same package `tools/sdk/esp32/include/mbedtls/mbedtls/include/mbedtls/sha256.h`:
  mbedtls_sha256_ret and context APIs; check returned status, use SHA-256 not SHA-224.
- Existing lwIP socket APIs: nonblocking send/recv through the owned descriptor.

WiFiClient owns the connection and closes it with stop; do not independently close
its descriptor or mix native reads with its buffered Stream reads. Use IPv4 connect
with its explicit timeout, then nonblocking socket send/recv. No getString,
readStringUntil, readBytes or unbounded String accumulator. All transfer progress
is governed by the [state machine](STEP017C_NETWORK_STATE_MACHINE.md).

## 4. Isolation and later implementation

Future dedicated environment: `esp32-m1-network-progress`, extending esp32-m1,
compiling only `src/network_progress/main.cpp`. Preserve the four existing environments:
esp32dev, esp32-m1, esp32-m1-h1, esp32-m1-progress.
Retain EINK_H1_ATOMIC_TEST for unchanged H1 reuse and add a dedicated
EINK_NETWORK_PROGRESS macro. Only the new environment receives
`.build/network-progress-private/`; source guard leaves other environments unaffected.
Reuse H1 wiring assertions and add a distinct NETWORK_PROGRESS_PRIVATE_PROFILE guard.
No environment, source or private header is created in C.

Existing [FrameFetcher](../src/frame_fetcher.h) is a Disabled-only placeholder,
not an implemented HTTP receiver. Do not activate it in historical demo environments.
Future D adds only dedicated configuration, receiver/validator, single-buffer
state machine, identity and session orchestration. Do not add Partial/Fast,
Deep Sleep, OTA, discovery, provisioning, web UI, MQTT/WebSocket, cloud, multi-panel
or battery logic. H1 and the embedded Progress baseline remain unchanged.

Companion contracts: [acceptance/LKG](STEP017C_FRAME_ACCEPTANCE_AND_LKG.md),
[display lifecycle](STEP017C_DISPLAY_LIFECYCLE.md),
[configuration/timeouts](STEP017C_NETWORK_CONFIG_AND_TIMEOUTS.md),
[D/E/F gates](STEP017C_IMPLEMENTATION_TEST_PLAN.md).

C performs document/static checks only. Design approval does not prove runtime
boundedness, repeated controller initialization, network delivery or physical safety.
