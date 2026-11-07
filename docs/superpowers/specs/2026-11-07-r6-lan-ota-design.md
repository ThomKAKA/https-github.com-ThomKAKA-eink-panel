# R6 LAN OTA — Design Spec

Date: 2026-11-07 (Asia/Shanghai)
Status: design approved in conversation; implementation not started.
Base commit: `3cd014b` (R5).

## 1. Goal

Let the operator update the ESP32-M1 over the trusted LAN from the existing Host,
with explicit arming, bounded download, SHA-256/image validation, no display or NVS
credential changes, and a 120-second self-test before the new image is accepted.

The device remains a pull-only HTTP client. No inbound device server, no cloud, no
USB requirement after the first OTA-capable image is installed.

## 2. Verified facts

- Partition table of the current build (decoded from
  `D:/Codex/round2-r3c-fix-20261107/network-build/esp32-m1-network-progress/partitions.bin`):
  `nvs` 20 KiB, `otadata` 8 KiB, `app0` 1280 KiB at `0x10000`, `app1` 1280 KiB at
  `0x150000`, `spiffs` 1408 KiB, `coredump` 64 KiB. No factory partition.
- Current network firmware is 834,221 bytes (R3C build), well below one 1280 KiB app slot.
- The running firmware reports `round2-r1a-1` and has no OTA code. One USB flash of an
  OTA-capable baseline is required before any wireless update.
- Arduino-ESP32 2.0.17 SDK has `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y`. Arduino's
  `initArduino()` marks a pending image valid at boot (`verifyOta()` defaults true).
  Real rollback therefore requires `verifyRollbackLater()` to return true and an explicit
  `esp_ota_mark_app_valid_cancel_rollback()` after a self-test.
- R3C persisted Wi-Fi credentials are stored in NVS under `eink-wifi/validated` and take
  precedence over compiled configuration. The OTA image must not embed real credentials.
- No host C++ compiler is available on PATH. C++ harness runtime is NOT RUN in this
  environment; compile checking uses the project toolchain where possible.

## 3. Scope

In scope:

- Host firmware offer configured by a local file, with explicit arm/disarm and status.
- Host endpoints for a small manifest, the firmware image, and management status.
- Management-page firmware card (Android-first layout, same monochrome UI).
- Device manifest check, image download, SHA-256 + image validation, boot-partition set,
  reboot on success, 120-second self-test and bootloader rollback.
- An OTA build profile that does not embed Wi-Fi credentials.
- Automated Host/frontend tests, C++ harness updates, build checks, and a controlled
  real-device acceptance plan.

Out of scope:

- HTTPS, authentication, pairing, signed firmware, secure boot, delta OTA, upload from
  the browser, automatic/scheduled updates, OTA progress on the e-ink display, rollback
  button, multiple devices, or cloud.
- Partition-table changes, full-chip erase, NVS erase, display changes, frame contract
  changes, or credential rotation.
- Physical failure injection (deliberately flashing a bad image) or an automatic reset
  on self-test failure.

## 4. Host architecture

### 4.1 Firmware offer configuration

Committed example: `config/firmware.example.json`.

Gitignored local file: `config/firmware.json`.

```json
{"path": "D:/local/firmware-r6-2.bin", "version": "round2-r6-2"}
```

- `path` may be absolute or relative to the repository root. It must resolve to one
  regular file; directories and globs are rejected.
- `version` must match `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`.
- File size must be 1..1,200,000 bytes inclusive.
- At Host startup the file is read once into memory and its SHA-256 is computed. Later
  on-disk changes are ignored until the Host restarts; this removes TOCTOU between the
  status, manifest and image responses.
- Missing/invalid configuration disables OTA. It must not affect frame, management,
  PWA or status routes. The path must never appear in logs, API bodies or HTML.

### 4.2 Firmware offer state

`services/firmware_offer.py` owns a `FirmwareOffer` guarded by one `threading.Lock`:

- `configured`, `version`, `size`, `sha256`, `image` (bytes) from startup.
- `armed`, `expires_at`, `served_at`, `device_version`.
- `arm()` sets `armed=true`, `expires_at=now+600s`, clears `served_at`; idempotent.
- `disarm()` sets `armed=false`; idempotent.
- `manifest()` returns `{"armed": false}` when configured and not armed/expired.
  Unconfigured is handled by the endpoint as 503, not by this method.
- `take_image()` requires configured + armed + not expired; marks `armed=false`,
  `served_at=now`, returns the image bytes and metadata. Consumption happens when the
  response is created, even if the client disconnects mid-body.
- `observe_device_version(version)` records any valid device report. If it equals the
  configured target version, the offer is disarmed.
- `status()` exposes configured, armed, version, size, sha256, expires_at, served_at,
  device_version, but never the path.

Arm expiry is 600 seconds. An expired arm is treated as unarmed and cleared.

### 4.3 Host endpoints

All firmware endpoints send `Cache-Control: no-store`.

`GET /api/device/firmware/status` -> 200 always:

```json
{
  "configured": true,
  "armed": false,
  "version": "round2-r6-2",
  "size": 840800,
  "sha256": "<64 lowercase hex>",
  "expires_at": null,
  "served_at": null,
  "device_version": "round2-r6-1"
}
```

Unconfigured: `configured=false`, all other nullable fields null.

`GET /api/device/firmware/manifest`:

- Unconfigured -> 503, `{"detail": "Firmware offer unavailable"}`.
- Configured, unarmed/expired -> 200, exact body `{"armed":false}`.
- Configured, armed -> 200, exact body:
  `{"armed":true,"version":"<version>","size":<decimal>,"sha256":"<64 hex>"}`.
- `Content-Type: application/json`, `Connection: close`, body at most 512 bytes.

The exact key order is part of the device contract. The Host must not add fields.

`GET /api/device/firmware/image`:

- Unconfigured -> 503; configured but not armed/expired -> 409.
- Armed -> 200 with the exact bytes, `Content-Type: application/octet-stream`,
  `Content-Length: <size>`, `X-Firmware-Version: <version>`,
  `X-Firmware-SHA256: <64 hex>`, `Cache-Control: no-store`, `Connection: close`.
- No ETag, no 304, no transfer encoding, no content encoding.
- The arm is consumed at request start (one-shot).

`POST /api/device/firmware/arm` -> 200 with the status body; 503 if unconfigured.

`POST /api/device/firmware/disarm` -> 200 with the status body.

Arm/disarm are unauthenticated on the trusted LAN. They cannot select an arbitrary file;
the only image available is the configured one.

### 4.4 Device-report integration

After `frame_publisher.report(report)` accepts a report, call
`firmware_offer.observe_device_version(report.firmware_version)`. A rejected report
(stale frame, invalid stage) must not change the offer. A valid communication-only report
is enough to record the running version and auto-disarm on a target match.

### 4.5 Management page

Add one `固件升级` card to `/manage`:

- Shows configured, target version, size in KiB, SHA-256 first 12 characters, device
  current version, armed/expiry/served state.
- `准备升级` is disabled when unconfigured, already armed, target is missing, or
  `device_version == target version`. Clicking it requires an explicit browser
  `confirm()` that names the target version and states the device will reboot.
- `取消升级` calls disarm while armed.
- The card never exposes the local path and never publishes a frame.
- Existing 10-second status polling also refreshes firmware status; a failed firmware
  status request shows UNKNOWN for firmware fields without blocking frame management.

## 5. Firmware build profiles

### 5.1 OTA build without credentials

New PlatformIO environment `esp32-m1-network-progress-ota`, extending
`esp32-m1-network-progress` with `-DEINK_OTA_BUILD=1`.

`config.h` under `EINK_OTA_BUILD`:

```cpp
constexpr char kSsid[] = "eink-ota-placeholder";
constexpr char kPassword[] = "";
constexpr unsigned kHost[] = {192, 0, 2, 1};
constexpr unsigned kPort = 8000;
```

The non-OTA branch keeps `#include "network_config.local.h"` and the private-profile
static assertion unchanged. The OTA branch does not include the private header, so the
image contains no real SSID or password. NVS credentials from R3C are used at runtime;
the placeholder fallback is only for a device with no persisted credentials, in which
case provisioning remains available through the existing button/AP.

### 5.2 Version macro

`report.h`:

```cpp
#ifndef EINK_FIRMWARE_VERSION
#define EINK_FIRMWARE_VERSION "round2-r6-1"
#endif
constexpr const char* kFirmwareVersion = EINK_FIRMWARE_VERSION;
```

- USB baseline: `esp32-m1-network-progress-ota`, `round2-r6-1`.
- Controlled target: same environment with
  `-DEINK_FIRMWARE_VERSION=\"round2-r6-2\"`.
- The target image has identical code except the version token; this proves the full
  download/flash/reboot path without adding unrelated behavior.

## 6. Device architecture

### 6.1 States and errors

Append, preserving all existing numeric values:

- `State::FirmwareCheck = 18`
- `State::FirmwareUpdate = 19`
- `Failure::FirmwareUpdateFailure` (appended)

Normal flow becomes:

`HostResolve -> FirmwareCheck -> (HttpConnect | FirmwareUpdate)`.

`FirmwareCheck` runs once per poll before the frame transaction. A manifest failure,
503, malformed body, or version match silently proceeds to `HttpConnect`; it must not
change `failure_`, enter `FailureWait`, or skip the frame poll.

`FirmwareUpdate` failure closes its socket, aborts the OTA handle, keeps the running
firmware, and enters `FailureWait` with `FirmwareUpdateFailure`. It calls no display
function and does not retry.

### 6.2 Port additions

```cpp
enum class FirmwareCheckResult { Pending, NoUpdate, UpdateAvailable, Failed, InvariantFailure };
enum class FirmwareUpdateResult { Pending, ReadyToReboot, Failed, InvariantFailure };

const char* firmwareVersion();
FirmwareCheckResult beginFirmwareCheck();
FirmwareCheckResult pollFirmwareCheck();
FirmwareUpdateResult beginFirmwareUpdate();
FirmwareUpdateResult pollFirmwareUpdate();
void rebootForFirmware();
```

The manifest offer (version/size/SHA) is retained inside the OTA adapter. The Machine
only sees the result. `rebootForFirmware()` never returns on hardware; the harness
records the call.

### 6.3 OtaUpdater

New `hardware/gdey042t81_esp32/src/network_progress/ota.h`:

- Reuses `SocketOwner` and `Port` socket methods; owns no second socket.
- Manifest request: `GET /api/device/firmware/manifest`, `Connection: close`,
  `Accept: application/json`.
- Manifest parser: bounded 512 bytes, exact key order, accepts only:
  - `{"armed":false}`
  - `{"armed":true,"version":"...","size":N,"sha256":"<64 hex>"}`
  Rejects unknown/trailing fields, duplicate keys, non-decimal size, bad version, bad
  SHA, size 0 or greater than the next OTA partition size.
- Image request: `GET /api/device/firmware/image`, `Accept: application/octet-stream`,
  `Accept-Encoding: identity`, `Connection: close`.
- Image headers are parsed by a new bounded parser (not the frame `Headers` class).
  Require HTTP 200, `Content-Type: application/octet-stream`, exact `Content-Length`,
  `X-Firmware-Version` equal to the manifest, `X-Firmware-SHA256` equal to the manifest,
  `Cache-Control: no-store`, `Connection: close`; reject transfer/content encoding.
- Body is streamed in chunks of at most 4096 bytes from one static 4096-byte buffer
  (not the 15000-byte frame buffer) into `esp_ota_get_next_update_partition(nullptr)`.
- SHA-256 is computed incrementally with mbedTLS over the exact body bytes.
- On body end: require EOF, close the socket, `esp_ota_end(handle)` (image validation),
  then compare the computed SHA with the manifest/header SHA, then
  `esp_ota_set_boot_partition(partition)`, then log
  `NETWORK_OTA_READY version=<version>` and `ESP.restart()`.
- Any failure: `esp_ota_abort(handle)` while active, close the socket, return `Failed`.
  A failure after `esp_ota_end` but before setting boot leaves the old boot partition.
- Budgets: TCP connect 3 s, response headers 5 s, body idle 10 s, total 120 s. No retry,
  no second attempt in the same poll.
- No display call, no frame-buffer write, no NVS credential write.

### 6.4 Self-test and rollback

- Define in the network entry:
  ```cpp
  bool verifyRollbackLater() { return true; }
  ```
  so Arduino does not auto-accept a pending image at boot.
- `EspPort::maintainFirmwareValidity()` runs every `loop()`:
  - Query the running partition; only act when its state is
    `ESP_OTA_IMG_PENDING_VERIFY`.
  - Accumulate continuous `WL_CONNECTED` time. Reset the accumulator on disconnect.
  - After 120,000 ms continuous connection, call
    `esp_ota_mark_app_valid_cancel_rollback()` once and log
    `NETWORK_OTA_VALIDATED`.
  - Never reset or reboot the device on its own.
- The accumulator lives in a small header-only helper with an injected clock, so the
  120-second rule is exercised by the C++ harness without hardware.
- If the new image never reaches the criterion, the next manual reset lets the
  bootloader roll back to the previous valid OTA slot. No automatic reset, retry or
  rollback is added.
- The initial USB-flashed baseline is not pending and is not subject to rollback.

## 7. Security and privacy

- The image served over LAN must be the `EINK_OTA_BUILD` artifact, which contains no
  real SSID/password. The operator must confirm this before configuring the Host:
  a strings check for the real SSID/password must find no match. The check is recorded
  only as PASS/FAIL; credentials are never printed into evidence or Git.
- The Host never exposes the configured path, raw exceptions or image bytes through
  status/manifest/HTML. Logs contain only version, size and SHA prefix.
- The image endpoint is one-shot and only available while armed; it returns the
  configured file only. There is no upload or arbitrary-file endpoint.
- Trusted-LAN model: no authentication, no signatures. An attacker on the LAN can
  arm/disarm or fetch the armed credential-free image and cause a reboot into the
  operator's configured image; this is a documented limit, not a claimed secure boot.
- No caching: firmware endpoints use `no-store`; the PWA service worker does not cache
  `/api/*`.

## 8. Tests

### Host (pytest)

- Exact manifest body for unarmed and armed (key order and no extra fields).
- Status unconfigured/configured; no path or credential string in any body.
- Arm, re-arm, disarm, expiry with an injected clock, one-shot image consumption.
- Image bytes, SHA-256, Content-Length and version headers; second image -> 409.
- Unconfigured manifest/image -> 503; not armed -> 409.
- Invalid config (missing file, directory, bad version, size 0, size limit) disables
  OTA without affecting `/manage`, frame or PWA routes.
- Valid device report with target version disarms; rejected report does not.
- Example config file parses; local config remains gitignored.

### Frontend (Node)

- `web/firmware_logic.mjs`: configured/armed/expiry/served/version-match states,
  button enablement, confirmation text, size and SHA formatting, UNKNOWN on failed poll.
- No publish side effects from arm/disarm.

### C++ harness

- Manifest unarmed and version match proceed to frame with no display.
- Manifest failure/503 proceeds to frame without changing failure state.
- Version differs -> update starts; success calls reboot exactly once and no display.
- Header/size/SHA/version mismatch, timeout, short body and socket failure -> abort,
  FailureWait, no display, no retry, old identity retained.
- State numeric values 0..17 remain unchanged; new states are 18/19.
- Self-test marker is called only after 120 s continuous connection.
- Runtime is NOT RUN if no host compiler is available; compile checking is recorded
  separately and is not runtime evidence.

### Real device (separate confirmations)

1. Build baseline `round2-r6-1` and target `round2-r6-2` with the OTA environment.
2. USB flash the baseline once; do not erase NVS or perform a full erase. Confirm the
   device boots and reports `round2-r6-1`.
3. Configure the Host with the target image; restart Host. Verify `/manage` shows the
   intended version/size/SHA and that the image contains no real credentials.
4. Arm from `/manage` after confirmation. Wait for the next poll; observe the manifest
   and image GETs, OTA serial states, validation, reboot and the new
   `round2-r6-2` device report.
5. Confirm `NETWORK_OTA_VALIDATED` after 120 s, then manually power cycle and confirm
   the device stays on `round2-r6-2` (no rollback).
6. Confirm the frame display and persisted credentials are unchanged; no frame is
   published during the OTA steps.

Physical failure injection and a real rollback test are NOT RUN. The rollback path is
covered by code/harness and the bootloader configuration, not by intentionally bricking
the device.

## 9. Acceptance criteria

- A1: Baseline USB boot reports `round2-r6-1`; partition table unchanged.
- A2: Armed OTA downloads the exact image, verifies size/SHA/version, reboots and
  reports `round2-r6-2`.
- A3: The new image is marked valid only after 120 s of continuous Wi-Fi; a manual
  power cycle after validation does not roll back.
- A4: No real credential appears in the image, API responses, HTML or logs; NVS
  credentials survive; no NVS erase.
- A5: Manifest failure/not armed leaves the frame path unchanged; OTA failure leaves the
  old firmware running, calls no display and does not retry.
- A6: Arm is one-shot and expires after 10 minutes; a successful version report
  auto-disarms.
- A7: Existing Python, Node and PWA tests remain green; the frame/device contract and
  R4/R5 behavior are unchanged.
- A8: No frame publish, physical display change or partition-table migration is part of
  R6.

## 10. Limits

- Trusted LAN only; no TLS, authentication or signed images.
- Full-image OTA only; no compression or delta.
- No OTA progress on the e-ink display; serial/Host evidence only.
- One device and one configured image per Host process; state is in memory and cleared
  on Host restart.
- OTA can delay a frame poll by up to 120 seconds and causes one reboot on success.
- A firmware that boots but has a logic defect is caught only if it fails the 120-second
  Wi-Fi self-test; deeper functional defects require a new OTA or USB recovery.
- First OTA-capable installation requires one USB flash; this stage will stop before
  uploading unless separately confirmed.
- The credential-free OTA build uses a TEST-NET-1 fallback Host and relies on mDNS
  discovery for the real Host. If mDNS is unavailable, the operator must build a variant
  with the deployment Host address (not a secret) or recover over USB.
