# R3D Multi-Network Wi-Fi — Design Spec

Date: 2026-11-09 (Asia/Shanghai)
Status: proposed; implementation starts only after this spec is approved and a plan exists.
Supersedes: nothing. Frame contract, display path, OTA and Host code are unchanged.

## 1. Goal

Let one device remember up to three validated Wi-Fi networks and join one automatically, so a
network change no longer forces a physical re-provisioning. The device keeps one active link at
a time and keeps the existing provisioning flow (S1 → `eink-panel-setup` → `/configure`).

Approved parameters:

- store **3** networks;
- try the **last successful** network first, then the remaining stored order;
- **15 s** per attempt, total budget **≤45 s** (3 × 15 s);
- the setup page **adds or updates** one network and never overwrites the others.

Constraints:

- The device still pulls frames; no Host change, no frame/display/OTA change.
- One active network at a time; no AP+STA concurrency outside provisioning.
- No NVS erase, no partition-table change, no credentials in logs or evidence.
- The compiled credentials remain the last-resort fallback and are not added to the list.

## 2. Verified facts

- One credential blob today: `WifiCredentials{char ssid[33]; char password[65];}`,
  validated by `validWifiCredentials` (SSID 1–32, password 0 or 8–64, 64-char keys must be hex).
  `src/network_progress/wifi_provisioning.h:6-32`.
- NVS: namespace `eink-wifi`, key `validated`, `getBytes`/`putBytes` of the whole struct.
  `src/network_progress/wifi_esp32.h:20-34`. The NVS partition is 20 KiB (`0x9000`/`0x5000`),
  untouched since the baseline.
- One association attempt is bounded by `kCandidateWifiTimeoutMs = 15000`
  (`wifi_provisioning.h:37`). The Machine's `WifiConnect` uses the same 15 s and treats
  `WL_CONNECT_FAILED` / `WL_NO_SSID_AVAIL` as immediate failure (`machine.h:98-102`).
- After failure the Machine enters `FailureWait` and retries the same credentials every poll
  (60 s) (`machine.h:266-272`). There is no fallback list and no per-boot attempt cap.
- Provisioning is button-gated: `requestProvisioning()` is accepted only in `PollWait` /
  `FailureWait` (`machine.h:74-79`). The AP `eink-panel-setup` (192.168.4.1) serves `GET /` and
  `POST /configure` (`wifi_esp32.h:9-16`, `:69-94`).
- A candidate is saved only after a successful association; then the SoftAP is stopped
  (`wifi_provisioning.h:78-87`). The WebServer stops **before** the candidate window; disabling
  the AP while it still owns AP-side TCP PCBs previously corrupted lwIP TCP state
  (`wifi_esp32.h:83-89`). A failed candidate reopens the listener (`:95-108`).
- The compiled credentials are used only when no persisted blob exists
  (`wifi_provisioning.h:46-52`, `main.cpp:222`).
- Last recorded footprint on `round2-r6-3`: static RAM 64,568 B / 327,680 B, flash
  834,405 B / 1,310,720 B. These are baselines to compare, not re-measured here.

## 3. Scope

In scope:

- a fixed-size store of three networks with a last-success index;
- ordered fallback inside one `WifiConnect` cycle;
- provisioning list + add/update + forget, with candidate-then-save preserved;
- migration from the single `validated` blob, and a rollback-safe dual write;
- tests for the store, selection, migration and the Machine's fallback.

Out of scope:

- Host changes of any kind; frame, display, OTA or report changes;
- network scanning, signal strength, static IP, captive portal;
- more than three networks, per-network priority editing, cloud sync;
- an AP password or any new authentication;
- deep sleep or power-management work (separate stage).

## 4. Data model and storage

```cpp
constexpr size_t kMaxWifiNetworks = 3;

struct WifiNetworkSlot {
  char ssid[33]{};
  char password[65]{};
  uint8_t used = 0;      // 0 empty, 1 stored
};

struct WifiNetworkStore {
  uint8_t version = 1;
  uint8_t count = 0;     // number of used slots
  uint8_t lastOk = 0;    // index tried first; 0 when empty
  uint8_t reserved = 0;
  WifiNetworkSlot slots[kMaxWifiNetworks]{};
};
```

- `static_assert(sizeof(WifiNetworkSlot) == 99)` and
  `static_assert(sizeof(WifiNetworkStore) == 301)`; all members are byte-aligned. Any compiler
  padding change is a build error, not a silent on-flash format change.
- New key `networks` (blob, 301 B) in the existing `eink-wifi` namespace. Version 1 layout only.
  Estimated NVS use is one blob entry plus overhead, well under the 20 KiB partition; the
  implementation records the measured free entries and heap in the acceptance evidence.
- Entries are kept in user order; success only updates `lastOk`, it does not reorder entries.
  `lastOk` is meaningful only when `count > 0`.
- Empty slots are skipped by both selection and the count; `count` is derived and also stored
  for quick validation (mismatch with the used flags is a rejected store).
- Invalid entries (failed `validWifiCredentials`) are skipped, never rewritten.
- SSID identity for add/update is an exact, case-sensitive string match; there can be at most
  one slot per SSID.

## 5. Selection and fallback

Selection order for one connect cycle:

1. `slots[lastOk]` if used and valid;
2. then `slots[0..2]` in order, skipping the already-tried slot and empty/invalid slots;
3. if the store is empty, the compiled credentials (current behaviour).

Runtime rules:

- `WifiProvisioning` keeps `attemptIndex_` and a small tried-mask. `beginNormal()` resets both and
  starts at `lastOk`; `nextAttempt()` cancels the current association (`WiFi.disconnect(false,
  false)`), returns the next untried slot and calls `connect()`. It is only valid in
  `NormalConnect`/`Connected` mode, never during provisioning or a candidate.
- The Machine stays the sole owner of timing. In `WifiConnect`, on timeout or immediate
  association failure it calls a new port hook `bool nextWifi()`. If it returns true, the
  Machine resets `segment_`, stays in `WifiConnect` and starts the next 15 s attempt; after
  three attempts it enters `FailureWait` exactly as today.
- No extra global timer: each attempt reuses the existing 15 s segment, so the worst case is
  45 s. After exhaustion the existing 60 s retry loop starts again from `lastOk`.
- The 45 s budget covers association attempts only. A link that drops while idle is noticed at
  the next poll (`PollWait` checks `connected()` only when its 60 s timer expires), so recovery
  after a drop is bounded by one poll plus the fallback: ≤60 s + 45 s.
- A successful association sets `lastOk`, persists the store and leaves the rest of the flow
  (`HostResolve` → firmware check → HTTP) untouched.
- Provisioning success also sets `lastOk` and returns to `HostResolve` (unchanged).

Port surface added to `machine.h`:

```cpp
virtual bool nextWifi() { return false; }  // starts the next stored network; false when exhausted
```

`EspPort::nextWifi()` delegates to `EspWifiProvisioning::nextAttempt()`. The default keeps every
existing fake compiling and preserves the single-network 15 s failure path; the device overrides
it.

## 6. Provisioning UI and routes

`GET /` renders, in this order:

1. the existing result text;
2. a table of stored networks: index, SSID, one **Forget** button per row — no password cell;
3. the add/update form (`ssid`, `password`) with the existing "Connect and save" wording.

`POST /configure`:

- validates the pair with `validWifiCredentials` (unchanged);
- starts a 15 s candidate; nothing is written before success;
- on success: if the SSID exists, replace that slot's password; else append to the first empty
  slot; if all three are full, reject with **409** and a message that one must be forgotten;
- then set `lastOk` to that slot, persist `networks`, and dual-write the same pair to
  `validated` for old-firmware rollback;
- keeps `server_.stop()` before the candidate window and the reopen-on-failure path.

`POST /forget` with `index=0..2`:

- refuses while a candidate is pending;
- removes the entry, compacts the remaining slots while preserving order;
- adjusts `lastOk`: removed index < lastOk → lastOk−1; removed index == lastOk → 0;
- persists, and leaves `validated` untouched (the last validated pair remains as rollback data);
- does not auto-connect; the next retry or reboot uses the new store.

New failure results: `StoreFull`, `StoreWriteFailed`, `ForgetRejected`; the HTML adds one line
per case. Existing results keep their wording.

The setup AP stays open (no password), as today; the button-gated entry is the only access
control. Changing that is out of scope.

## 7. Migration and compatibility

Load order in `WifiProvisioning::load()`:

1. `networks` present, correct length, version 1, `count` matches the used flags → use it;
2. otherwise, legacy `validated` present and valid → build a one-slot store, set `lastOk = 0`,
   persist `networks` once, keep `validated` untouched;
3. otherwise → compiled credentials, empty store.

- A malformed or future-version `networks` blob is ignored (fall back to legacy/compiled) and is
  never erased or overwritten by the load path.
- Rollback: every successful candidate writes both `networks` and `validated`, so reflashing the
  previous firmware still finds one working pair. No NVS erase, no partition change.
- If the one-time migration write fails, the legacy pair stays active in RAM and the migration
  is retried on the next boot; the device does not lose connectivity over a failed write.
- `POST /forget` leaves `validated` untouched, so a rollback can resurrect the forgotten pair
  as the old firmware's only network. This is deliberate: `validated` is rollback data, not a
  mirror of the list. The new firmware never reads it again once `networks` is valid.
- The store survives page-data changes, Host moves and re-flashing; only a full NVS erase (not
  part of this stage) removes it.

## 8. Security and privacy

- Passwords never appear in the setup HTML, in any response body, in serial output or in
  evidence. The list shows SSIDs only, and acceptance evidence masks the SSID.
- No credential is added to the Host, the repo or `config/`.
- `POST /forget` takes an index, not a credential, so no secret is echoed in a URL.
- The store is read only by the Wi-Fi layer; no other module gets a reference to it.
- A failed write keeps the previous store (Preferences writes the whole blob per key); the
  device reports `StoreWriteFailed` and does not pretend the network was saved.

## 9. Failure handling

| Situation | Behaviour |
| --- | --- |
| Preferred network absent or wrong password | Move to the next slot immediately (association failure) or after 15 s (timeout); total ≤45 s |
| All stored networks fail | Keep the last frame (LKG), enter `FailureWait`, retry the same order every 60 s; do not auto-open the setup AP |
| `networks` missing or malformed | Legacy `validated`, then compiled fallback; no erase |
| Candidate fails in provisioning | AP listener reopens, nothing saved, previous store intact |
| Store full | 409, nothing written; operator forgets one entry |
| Forced reboot mid-write | Preferences blob write is per-key; a torn blob fails length/version checks and falls back, never half-applies |
| Wrong clock | Not used; selection is index-based only |

No new retry loop, no defensive branches beyond these contract paths.

## 10. Tests

C++ (pure logic, `tests/cpp/`):

- `test_wifi_provisioning.cpp` additions:
  - size asserts for slot/store (301 B) and `kMaxWifiNetworks = 3`;
  - selection: lastOk first, then stored order, skip empty/invalid, never repeat an SSID;
  - `nextAttempt()` exhaustion after three distinct attempts;
  - add: new SSID appends; existing SSID replaces its password in place; full store rejects;
  - forget: compaction and `lastOk` adjustment for all three index relations;
  - migration: legacy blob → one-slot store; malformed/oversized blob ignored;
  - dual write: success writes both keys;
  - invalid credentials never enter the store.
- `test_network_progress.cpp` additions:
  - `WifiConnect` tries the next slot on failure and only then enters `FailureWait`;
  - success on the second slot goes to `HostResolve` with no display change;
  - three failures take exactly three 15 s segments (fake clock), not 60 s;
  - provisioning success still returns to `HostResolve` and stops the AP.
- Static checks: no dynamic allocation in the new code paths (existing style), no credential in
  serial strings, both envs compile (`esp32-m1-network-progress`, `esp32-m1-network-progress-ota`).

Host regression: full pytest and frontend suites, unchanged, must stay green.

## 11. Acceptance criteria

1. Provision the phone hotspot and a second network; both appear in the list, count = 2, no
   password shown. Device still displays its current page; provisioning alone does not refresh.
2. Reboot: the device joins the last successful network and polls normally (200 → 304).
3. Turn that AP off: the next poll notices the drop, then the device joins the other stored
   network within the fallback budget (≤60 s + 45 s), fetches the current frame (200, 15000 B,
   ETag = SHA-256) and the next poll is 304; refresh count increases only for a content change.
4. Forget the active network: the next retry cycle joins the remaining one; count and page still
   correct.
5. Serial log and evidence contain no password and no unmasked SSID; NVS free entries, free heap
   and flash size are recorded; store size assert present.
6. Rollback: reflash the previous image (separate authorization); it boots with `validated` and
   polls. No NVS erase, no partition change.

## 12. Limits

- One network active at a time; the other stored networks are idle.
- Up to 45 s before the first frame poll when every network fails, once per 60 s retry cycle;
  after an idle link drop, recovery is up to one poll plus that budget (≤105 s).
- No scanning UI, no priority editing, no per-network IP; order is fixed by storage order.
- The setup AP remains open and must only be entered by the physical button.
- More than three networks, AP passwords, deep sleep and battery reporting are later stages.

## 13. Rollback

1. Keep `validated` dual-written on every success; the old firmware reads it unchanged.
2. Reflash the previous image (USB or a separately authorized OTA). `networks` is left in place
   and ignored by old firmware.
3. If the new firmware fails acceptance, stop after restoring the image and record it; do not
   erase NVS or the store to "clean up".

## 14. Decision log

| Decision | Reason |
| --- | --- |
| N = 3 | Covers hotspot + home + one spare; 301 B blob fits the 20 KiB NVS with room for the existing keys |
| Last-success first, then stored order | Zero UI work, deterministic, and the common case connects immediately |
| 15 s × 3 ≤45 s inside `WifiConnect` | Reuses the existing timeout and keeps the Machine as the only timer owner |
| Add/update, never overwrite | The operator's other networks survive a re-provisioning |
| Forget by index with compaction | No secret in a URL; deterministic `lastOk` adjustment |
| Dual write `validated` | Old firmware keeps working after a rollback |
| Compiled credentials only when the store is empty | Preserves today's fallback without exposing build-time secrets as a listed network |
| No auto-open setup AP on total failure | Preserves current behaviour and avoids an unattended open AP |
| No AP password in this stage | Out of scope; the button gate is the current control |
