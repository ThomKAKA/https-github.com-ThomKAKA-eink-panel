# STEP017E Software / Compile Verification Report

**Final decision: NO-GO.** The required dedicated network environment was not
compiled. This is a verification-environment blocker, not an observed network
source compile failure. STEP017F is not authorized by this result.

## 1. Baseline, scope, and execution record

- Authorized mode: `VERIFY_ONLY`; no product source, test, dependency, or build
  configuration edits; no hardware, upload, serial, real Wi-Fi, or LAN operation.
- Baseline and pre-documentation HEAD:
  `6960515f3dca6c751c925d5fd127738735b9f486`.
- Initial and post-executor `git status --short`: only
  `?? hardware/evidence/`; index and tracked tree clean.
- Formal DeepSeek Harness run ID: `6cc77c084b5d415d9505c73683ebd079`;
  headless process exit code `0`; executor status `READY_FOR_REVIEW`.
- Contract, raw command logs, before/after snapshots, and the sole structured
  `RESULT.json` are under the local repository-external runtime directory
  `D:\Codex\dual-agent-handoff-runtime\eink-panel\step017e-6cc77c084b5d415d9505c73683ebd079\`.
  `RESULT.json` SHA-256:
  `0b68adf698e487a157197c3ad0a2e62a902a88266b80b5b91f100cd58a730521`.
- The result parses as one JSON object. All required top-level fields are present;
  `task_id=STEP017E`, run ID, baseline SHA, and `mode=VERIFY_ONLY` match the
  contract. Six recorded commands have readable logs and matching exit codes.
- Two earlier launch attempts were stopped while correcting Harness file-policy
  problems. The second exposed a Windows sandbox/pytest temporary-directory
  permission error. The formal run above used a corrected launch policy and the
  same unmodified repository; its full Python suite completed successfully.

The executor's `READY_FOR_REVIEW` is a handoff status, not a project PASS. Codex
reviewed the logs, file hashes, source and Git state independently.

## 2. Python and host C++

| Gate | Executor evidence | Codex review |
| --- | --- | --- |
| Full Python regression | `364 collected, 364 passed, 0 failed, 0 skipped, 0 errors`; `pytest -q` exit `0`; 4.01 s | Independent same-command rerun: `364 passed in 3.95s`, exit `0` |
| Host C++17 compiler | No `g++`, `clang++`, `cl`, or other usable host compiler on PATH/common local installations; no compiler installed | `Get-Command g++,clang++,cl` returned none |
| Existing `tests/cpp` harnesses | **BLOCKED / NOT RUN** for lack of host compiler | Not claimed PASS; the frozen plan permits this single host-tool blocker when target compilation supplies the required evidence |

The Python suite ran unchanged. The historical count of 364 was checked against
current collection, not used as a hard-coded acceptance threshold.

## 3. Audited PlatformIO environments and builds

`platformio.ini` currently defines exactly these five formal environments. Builds
used project-local Python with `-B -m platformio run -e <env>` from
`hardware/gdey042t81_esp32`, with `PLATFORMIO_CORE_DIR` set to
`D:\Codex\eink-panel\.venv-hw\pio-core`. No upload or clean command ran.

| Environment | Result / exit | RAM | Flash | BIN / ELF |
| --- | --- | --- | --- | --- |
| `esp32dev` | SUCCESS / 0 | 36,696 B, 11.2% | 285,241 B, 21.8% | both generated |
| `esp32-m1` | SUCCESS / 0 | 36,696 B, 11.2% | 285,241 B, 21.8% | both generated |
| `esp32-m1-h1` | SUCCESS / 0 | 21,616 B, 6.6% | 294,689 B, 22.5% | both generated |
| `esp32-m1-progress` | SUCCESS / 0 | 36,616 B, 11.2% | 294,725 B, 22.5% | both generated |
| `esp32-m1-network-progress` | **BLOCKED / NOT RUN**; no exit code | unavailable | unavailable | neither generated |

Each successful build's output ends in PlatformIO `SUCCESS`; Codex independently
checked the recorded BIN/ELF existence, size and SHA-256 against the files in
ignored `.pio/build/<env>/` directories:

| Environment | BIN size / SHA-256 | ELF size / SHA-256 |
| --- | --- | --- |
| `esp32dev` | 285600 / `603de0a11e8809f3697ac3e98516d04d406c13ebc996cb436114e518374e5574` | 7004404 / `b3c597ae5497494c86f5c91c091e89f844ff5cdc04246879457091a30c81e9e0` |
| `esp32-m1` | 285600 / `af37ef2757a3d2ffe9356eed217c41ec0c7f44f25a1cfe726d2a745fdd4ac6d6` | 7004692 / `142fd73b618aee85cb828b47744795b3442b1ca3953d9e7d07da4e6e1f092ffe` |
| `esp32-m1-h1` | 295056 / `4651616d92e03009b69eb260de11bcd548d4504504ee6931bdbbcafe7e2f8ed1` | 6735708 / `3cf68337ef9173615427f44b323cf1aac8367efaafeff5ab7d75f805cbb4fecd` |
| `esp32-m1-progress` | 295088 / `942f7eaa9a7ad6574ee36a05478d085d52440d0578c82ed0457a7c65ac241523` | 6721320 / `a5c170fe154e8a4df6b978342d274b48b270cf1dcbff34f23011b4ecc41302f1` |

The dedicated network environment deliberately requires
`.build/network-progress-private/network_config.local.h` and the H1 private
display header. That directory does not exist. Its per-environment
`.pio/libdeps/esp32-m1-network-progress/` directory is also absent. Starting
the build could install/download dependencies, which this stage forbids.
The executor therefore recorded **NOT RUN / BLOCKED** without changing
configuration or creating credentials. No network `firmware.bin` or
`firmware.elf` exists; their size and SHA-256 are **UNAVAILABLE**. Target lwIP
header/API integration is consequently **not compile verified**. No compile or
link error was observed for this environment because compilation did not start.

## 4. Static network contract review

The following are source-level conclusions, not executable or physical network
results. Codex checked the current `network_progress` source independently of
the executor's result.

| Contract | Source-level result |
| --- | --- |
| Transport and ownership | No `WiFiClient` transport path. `main.cpp` uses existing `lwip_socket`, `lwip_fcntl`, `lwip_connect`, `lwip_select`, `lwip_getsockopt`, `lwip_send`, `lwip_recv`, and `lwip_close`. `transport.h` holds one noncopyable `SocketOwner`; successful socket creation transfers ownership before fallible setup. Actual fixed-target integration remains uncompiled. |
| Reconnect ownership | `WiFi.persistent(false)` and `setAutoReconnect(false)` remain, without a claim of exclusive framework radio retry control. There is no application Wi-Fi callback or task that initiates HTTP/display. Only `Machine::tick()` in the main loop advances those actions. |
| Failure classification | `CONFIG_INVALID` enters permanent `FAULT_STOP` before Wi-Fi work. `WIFI_INIT_FAILURE` enters `FAILURE_WAIT`; the next interval retries `WifiInit`. Ordinary association, TCP, HTTP and frame failures wait/retry; unsafe ownership/display failures park in `FAULT_STOP`. |
| Frame and memory | One static 15,000-byte candidate/display T buffer; no second full frame or LKG image buffer. T remains 400×300, one bit, stride 50, row-major, MSB-first, 0 black/1 white. Network receive does no MCU software flip/rotation. |
| Identity | Restricted parser requires a quoted lowercase 64-hex strong ETag. The exact final 15,000 T bytes are SHA-256 checked before display eligibility. Valid 304 and unchanged 200 skip display; only valid changed 200 reaches `DISPLAY_PENDING`/`DISPLAY_UPDATE`. |
| Display boundary | Invalid response or network failure cannot reach display. A changed frame uses a fresh H1-compatible guarded FULL session. Software return/BUSY checks do not prove physical pixel success or repeated FULL operation. |

### Application-owned descriptor cleanup matrix

In this table `reset` means the local fd becomes invalid after one close attempt;
a failed close parks the application without claiming the lower stack released it.
The precise paths are in `transport.h::finish()` and `machine.h::closeConnection()`,
`fail()`, `fault()` and `ResponseEnd`.

| Path | fd created / owned on entry | Close / reset | Candidate display? |
| --- | --- | --- | --- |
| socket creation failure | no / no | no fd to close | no |
| nonblocking `F_GETFL`/`F_SETFL` failure | yes / yes | owner `failed()` → `finish()` / yes | no |
| socket option failure | N/A | no `setsockopt` used | no |
| connect immediate failure | yes / yes | owner `failed()` → `finish()` / yes | no |
| connect timeout | yes / yes | Machine `finishTcp()` / yes | no |
| connect completion or readiness/SO_ERROR failure | yes / yes | later Machine close or owner failure close / yes | no before validation |
| send failure or timeout | yes / yes | Machine `finishTcp()` / yes | no |
| recv failure or timeout, header/body | yes / yes | Machine `finishTcp()` / yes | no |
| header parser rejection | yes / yes | Machine `finishTcp()` / yes | no |
| short/oversized body or missing EOF | yes / yes | Machine `finishTcp()` / yes | no |
| invalid ETag | yes / yes | Machine `finishTcp()` / yes | no |
| SHA mismatch or crypto error | yes / already closed | no second close; fd already invalid | no |
| valid 304 | yes / yes until EOF | Machine close at `ResponseEnd` / yes | no |
| unchanged valid 200 | yes / already closed | no second close; fd already invalid | no |
| changed valid 200 | yes / already closed | no second close; fd already invalid | yes, after validation |
| failed close / illegal ownership | yes / possibly uncertain | one attempt, local invalid, `FAULT_STOP` | no |

This source audit covers application-owned descriptors only. It does not assert
framework-internal leak freedom or executed fault-injection coverage.

## 5. Dependencies, secrets, Git purity, and limits

- D-R1 changed no `platformio.ini`, framework, toolchain or dependency
  declaration relative to C-R1. Installed versions checked: PlatformIO 6.1.19,
  espressif32 6.12.0, Arduino-ESP32 2.0.17, Xtensa GCC 8.4.0,
  GxEPD2 1.6.9, Adafruit GFX 1.12.6 and BusIO 1.17.4. No new version or
  package was installed during this run.
- Executor secret scan found no literal credential in tracked source/templates
  or logs. Codex separately scanned tracked files for private-key headers,
  common key/token patterns and literal network SSID/password definitions:
  zero high-signal matches. This is a scoped pattern scan, not a proof about
  ignored private files; `hardware/evidence/` was not inspected for secrets.
- Full before/after filesystem snapshots: 154 tracked files have identical
  SHA-256; 42 pre-existing `hardware/evidence/` entries are identical. HEAD and
  Git status are unchanged. Changed snapshot entries are confined to ignored
  `.pio` build and pytest cache paths; no unexpected project file was created.
- **NOT RUN:** host C++ tests; network-environment build, target socket API
  compilation, network BIN/ELF hash, controlled TCP/Host Connection-close
  fixtures, negative private-configuration builds, actual Wi-Fi/HTTP/LAN
  runtime, upload, serial/COM, hardware display and physical repeated FULL.
  BUSY timeout fault injection, Deep Sleep, Partial/Fast Refresh and long-duration
  operation remain unverified; exact physical FULL invocation count remains
  not independently verified.

## 6. Decision and next action

Python regression, historical builds, static ownership/contract review,
dependency review, secret scan, artifact checks and Git purity passed their
stated scopes. The dedicated network build is a mandatory STEP017E gate and
is unresolved. **STEP017E = NO-GO; ESP32 network fetcher is not compile verified;
network product function verified = NO.** There is no executor/reviewer mismatch
on the facts above; Codex made a stricter final stage decision than the
executor's `READY_FOR_REVIEW` handoff label.

The next actionable work requires a separately authorized STEP017E verification
environment preparation: establish an approved local-only compile profile and
make the exact pinned dependencies available without changing product source.
Then rerun STEP017E as a new verification attempt. No STEP017D-R2 code remediation
is justified by the evidence presently available. Do not enter STEP017F, upload,
connect hardware, push or tag as part of this result.
