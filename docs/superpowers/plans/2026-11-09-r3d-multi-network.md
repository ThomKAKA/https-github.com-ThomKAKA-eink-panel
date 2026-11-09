# R3D Multi-Network Wi-Fi Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let one device store three validated Wi-Fi networks, join the last successful one first, fall back within a 45 s budget, and manage the list from the existing setup AP without ever overwriting another network.

**Architecture:** A fixed 301-byte `WifiNetworkStore` lives in the existing `eink-wifi` NVS namespace under a new `networks` key. `WifiProvisioning` owns selection and persistence; the `Machine` owns timing and asks the port for `nextWifi()` after a failed 15 s association. The setup page gains a list, add/update and forget routes; the legacy `validated` key is dual-written so an old image still boots after a rollback.

**Tech Stack:** ESP32 Arduino (espressif32 6.12.0, C++17), GxEPD2 1.6.9 (unchanged), `Preferences`, `WebServer`, `WiFi`; PlatformIO builds; compile-time `static_assert` harness under `tests/cpp`; Python 3 / Node for the unchanged Host regression.

**Spec:** `docs/superpowers/specs/2026-11-09-r3d-multi-network-design.md`

## Global Constraints

- Store exactly 3 networks; one active link at a time; no AP+STA concurrency outside provisioning.
- Per-attempt timeout 15 s (`kCandidateWifiTimeoutMs`); at most 3 attempts per `WifiConnect` cycle (≤45 s).
- Selection order: `lastOk`, then stored order; skip empty or invalid slots; never repeat a tried slot.
- The setup page adds or updates one network; it never overwrites another; full store rejects (409).
- Never write a password into HTML, serial output, logs, committed files or evidence; SSIDs are masked in evidence.
- Never erase NVS, change the partition table, or commit private headers / `config/firmware.json`.
- Keep `validated` dual-written on every successful candidate; `forget` leaves it untouched.
- No Host change; frame contract, 200/304, ETag, display and OTA stay untouched.
- The store/selection path uses fixed arrays only, no allocation; the setup page keeps the
  pre-existing Arduino `String` usage from the current `GET /` handler.
- Do not flash, upload, reset or power-cycle the device without a separate explicit authorization.
- The out-of-repo PlatformIO config and private headers stay outside the repo; never commit them.

## File Structure

| File | Responsibility |
| --- | --- |
| `hardware/gdey042t81_esp32/src/network_progress/wifi_provisioning.h` | store model, validation, selection, migration, provisioning state (pure, `constexpr`) |
| `hardware/gdey042t81_esp32/src/network_progress/wifi_esp32.h` | NVS read/write, setup page, `/configure`, `/forget` |
| `hardware/gdey042t81_esp32/src/network_progress/machine.h` | `nextWifi()` port hook, 3-attempt cap, `WifiConnect` advance |
| `hardware/gdey042t81_esp32/src/network_progress/main.cpp` | `EspPort::nextWifi()` delegation, store/heap/NVS boot log |
| `tests/cpp/test_wifi_provisioning.cpp` | compile-time store/selection/migration/provisioning tests |
| `tests/cpp/test_network_progress.cpp` | compile-time cap assert; runtime harness stays unrun until a host compiler exists |

**Test runner fact:** there is no host C++ compiler, so the existing runtime harness cannot run.
`test_wifi_provisioning.cpp` is pure `static_assert`; compiling it with the xtensa compiler runs
it. Command (validated working):

```bash
TC="D:/Codex/eink-panel/.venv-hw/pio-core/packages/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-g++.exe"
"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_wifi_provisioning.cpp
```

The runtime Machine harness is compile-checked only; its behaviour is verified by the device
acceptance in Task 8. Do not claim it "ran".

---

### Task 1: Three-slot store and helpers

**Files:**
- Modify: `hardware/gdey042t81_esp32/src/network_progress/wifi_provisioning.h`
- Test: `tests/cpp/test_wifi_provisioning.cpp`

**Interfaces:**
- Produces: `kMaxWifiNetworks`, `kNoWifiSlot`, `WifiNetworkSlot`, `WifiNetworkStore`,
  `sameSsid`, `findNetwork`, `storeConsistent`, `addNetwork`, `forgetNetwork`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/cpp/test_wifi_provisioning.cpp` before the existing `static_assert` block:

```cpp
constexpr WifiCredentials cred(const char* ssid, const char* password) {
  return wifiCredentials(ssid, password);
}
constexpr bool storeAddUpdate() {
  WifiNetworkStore store{};
  return addNetwork(store, cred("net-a", "password1")) &&
    addNetwork(store, cred("net-b", "password2")) &&
    addNetwork(store, cred("net-c", "password3")) &&
    store.count == 3 &&
    !addNetwork(store, cred("net-d", "password4")) &&
    addNetwork(store, cred("net-b", "newpass99")) &&
    store.count == 3 && findNetwork(store, "net-b") == 1 &&
    sameSsid(store.slots[1].value.password, "newpass99");
}
constexpr bool storeForget() {
  WifiNetworkStore store{};
  addNetwork(store, cred("net-a", "password1"));
  addNetwork(store, cred("net-b", "password2"));
  addNetwork(store, cred("net-c", "password3"));
  store.lastOk = 2;
  if (!forgetNetwork(store, 1)) return false;
  if (store.count != 2 || !sameSsid(store.slots[1].value.ssid, "net-c") || store.lastOk != 1) return false;
  if (!forgetNetwork(store, 1)) return false;
  if (store.count != 1 || store.lastOk != 0 || !sameSsid(store.slots[0].value.ssid, "net-a")) return false;
  return !forgetNetwork(store, 2);
}
constexpr bool storeRejectsMismatch() {
  WifiNetworkStore store{};
  addNetwork(store, cred("net-a", "password1"));
  store.count = 2;
  return !storeConsistent(store);
}
constexpr bool rejectsInvalidEntry() {
  WifiNetworkStore store{};
  return !addNetwork(store, cred("", "password1")) && store.count == 0;
}
constexpr bool rejectsBadLastOk() {
  WifiNetworkStore store{};
  addNetwork(store, cred("net-a", "password1"));
  store.lastOk = 1;
  return !storeConsistent(store);
}

static_assert(kMaxWifiNetworks == 3, "store holds three networks");
static_assert(sizeof(WifiNetworkSlot) == 99, "slot layout changed");
static_assert(sizeof(WifiNetworkStore) == 301, "store layout changed");
static_assert(storeAddUpdate(), "add, update in place, reject when full");
static_assert(storeForget(), "forget compacts and fixes lastOk");
static_assert(storeRejectsMismatch(), "count must match used flags");
static_assert(rejectsInvalidEntry(), "invalid credentials never enter the store");
static_assert(rejectsBadLastOk(), "lastOk must point at a used slot");
```

- [ ] **Step 2: Run to verify it fails**

```bash
TC="D:/Codex/eink-panel/.venv-hw/pio-core/packages/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-g++.exe"
"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_wifi_provisioning.cpp
```

Expected: `error: 'kMaxWifiNetworks' was not declared in this scope`.

- [ ] **Step 3: Implement the store and helpers**

Insert after `WifiCredentials`/`validWifiCredentials` in `wifi_provisioning.h`:

```cpp
constexpr size_t kMaxWifiNetworks = 3;
constexpr uint8_t kNoWifiSlot = 0xFF;

struct WifiNetworkSlot {
  WifiCredentials value{};
  uint8_t used = 0;
};

struct WifiNetworkStore {
  uint8_t version = 1;
  uint8_t count = 0;
  uint8_t lastOk = 0;
  uint8_t reserved = 0;
  WifiNetworkSlot slots[kMaxWifiNetworks]{};
};

static_assert(sizeof(WifiNetworkSlot) == 99, "slot layout changed");
static_assert(sizeof(WifiNetworkStore) == 301, "store layout changed");

constexpr bool sameSsid(const char* a, const char* b) {
  size_t i = 0;
  while (a[i] && b[i] && a[i] == b[i]) ++i;
  return a[i] == b[i];
}

constexpr int8_t findNetwork(const WifiNetworkStore& store, const char* ssid) {
  for (size_t i = 0; i < kMaxWifiNetworks; ++i)
    if (store.slots[i].used && sameSsid(store.slots[i].value.ssid, ssid)) return int8_t(i);
  return -1;
}

constexpr bool storeConsistent(const WifiNetworkStore& store) {
  if (store.version != 1) return false;
  uint8_t used = 0;
  for (size_t i = 0; i < kMaxWifiNetworks; ++i) {
    if (!store.slots[i].used) continue;
    ++used;
    if (!validWifiCredentials(store.slots[i].value)) return false;
  }
  if (used != store.count) return false;
  if (store.count == 0) return store.lastOk == 0;
  return store.lastOk < kMaxWifiNetworks && store.slots[store.lastOk].used;
}

constexpr bool addNetwork(WifiNetworkStore& store, const WifiCredentials& value) {
  if (!validWifiCredentials(value)) return false;
  const int8_t existing = findNetwork(store, value.ssid);
  if (existing >= 0) { store.slots[existing].value = value; return true; }
  if (store.count >= kMaxWifiNetworks) return false;
  for (size_t i = 0; i < kMaxWifiNetworks; ++i) {
    if (store.slots[i].used) continue;
    store.slots[i].value = value;
    store.slots[i].used = 1;
    ++store.count;
    return true;
  }
  return false;
}

constexpr bool forgetNetwork(WifiNetworkStore& store, uint8_t index) {
  if (index >= kMaxWifiNetworks || !store.slots[index].used) return false;
  for (size_t i = index; i + 1 < kMaxWifiNetworks; ++i) store.slots[i] = store.slots[i + 1];
  store.slots[kMaxWifiNetworks - 1] = {};
  --store.count;
  if (store.count == 0) store.lastOk = 0;
  else if (index == store.lastOk) store.lastOk = 0;
  else if (index < store.lastOk) --store.lastOk;
  return true;
}
```

- [ ] **Step 4: Run to verify it passes**

```bash
"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_wifi_provisioning.cpp
```

Expected: exit 0, no output.

- [ ] **Step 5: Commit**

```bash
git add hardware/gdey042t81_esp32/src/network_progress/wifi_provisioning.h tests/cpp/test_wifi_provisioning.cpp
git commit -m "feat(wifi): add the three-slot network store"
```

---

### Task 2: Selection order and per-cycle attempts

**Files:**
- Modify: `wifi_provisioning.h`, `tests/cpp/test_wifi_provisioning.cpp`

**Interfaces:**
- Consumes: Task 1 store helpers.
- Produces: `nextNetworkIndex(store, triedMask)`, `WifiProvisioning::nextAttempt()`,
  `WifiProvisioning::store()`.

- [ ] **Step 1: Write the failing tests**

Extend `FakeWifi` with store support and add tests:

```cpp
Inside the existing `FakeWifi` struct, add these members; every existing field stays unchanged:

```cpp
WifiNetworkStore store{};
bool storePresent = false, storeSaveOK = true;
unsigned storeLoads = 0, storeSaves = 0;
constexpr bool loadStore(WifiNetworkStore& out) {
  ++storeLoads;
  if (!storePresent) return false;
  out = store;
  return true;
}
constexpr bool saveStore(const WifiNetworkStore& value) {
  ++storeSaves;
  if (!storeSaveOK) return false;
  store = value; storePresent = true; return true;
}
```

constexpr bool selectionOrder() {
  WifiNetworkStore store{};
  addNetwork(store, cred("net-a", "password1"));
  addNetwork(store, cred("net-b", "password2"));
  addNetwork(store, cred("net-c", "password3"));
  store.lastOk = 1;
  return nextNetworkIndex(store, 0) == 1 &&
    nextNetworkIndex(store, 0x02) == 0 &&
    nextNetworkIndex(store, 0x03) == 2 &&
    nextNetworkIndex(store, 0x07) == kNoWifiSlot;
}
constexpr bool fallsBackInOrder() {
  FakeWifi port;
  port.present = false; port.storePresent = true;
  addNetwork(port.store, cred("net-a", "password1"));
  addNetwork(port.store, cred("net-b", "password2"));
  addNetwork(port.store, cred("net-c", "password3"));
  port.store.lastOk = 1;
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load(); wifi.beginNormal();
  if (!sameSsid(port.connectedWith.ssid, "net-b")) return false;
  if (!wifi.nextAttempt() || !sameSsid(port.connectedWith.ssid, "net-a")) return false;
  if (!wifi.nextAttempt() || !sameSsid(port.connectedWith.ssid, "net-c")) return false;
  return !wifi.nextAttempt() && port.cancels == 2;
}
constexpr bool remembersSuccess() {
  FakeWifi port;
  port.present = false; port.storePresent = true;
  addNetwork(port.store, cred("net-a", "password1"));
  addNetwork(port.store, cred("net-b", "password2"));
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load(); wifi.beginNormal();
  if (!wifi.nextAttempt()) return false;
  wifi.normalConnected();
  return port.store.lastOk == 1 && port.storeSaves == 1;
}

static_assert(selectionOrder(), "lastOk first, then stored order");
static_assert(fallsBackInOrder(), "three attempts then exhaustion");
static_assert(remembersSuccess(), "success updates lastOk once");
```

- [ ] **Step 2: Run to verify it fails**

Expected: `error: 'nextNetworkIndex' was not declared` and `error: 'nextAttempt' was not declared`.

- [ ] **Step 3: Implement selection and attempts**

Add after `forgetNetwork`:

```cpp
constexpr uint8_t nextNetworkIndex(const WifiNetworkStore& store, uint8_t triedMask) {
  if (store.count == 0) return kNoWifiSlot;
  const auto eligible = [&](uint8_t index) {
    return !(triedMask & uint8_t(1u << index)) && store.slots[index].used &&
      validWifiCredentials(store.slots[index].value);
  };
  if (store.lastOk < kMaxWifiNetworks && eligible(store.lastOk)) return store.lastOk;
  for (uint8_t i = 0; i < kMaxWifiNetworks; ++i) if (eligible(i)) return i;
  return kNoWifiSlot;
}
```

In `WifiProvisioning`, add members and replace `load()`/`beginNormal()`:

```cpp
constexpr void load() {
  WifiNetworkStore stored{};
  if (port_.loadStore(stored) && storeConsistent(stored)) {
    store_ = stored;
  } else {
    WifiCredentials legacy{};
    if (port_.loadCredentials(legacy) && validWifiCredentials(legacy)) {
      store_ = {};
      addNetwork(store_, legacy);
    } else {
      store_ = {};
    }
  }
  mode_ = WifiMode::NormalConnect;
  selectInitial();
}
constexpr void beginNormal() {
  mode_ = WifiMode::NormalConnect;
  selectInitial();
  port_.connect(active_);
}
constexpr bool nextAttempt() {
  if (mode_ != WifiMode::NormalConnect && mode_ != WifiMode::Connected) return false;
  if (attempt_ != kNoWifiSlot) triedMask_ |= uint8_t(1u << attempt_);
  const uint8_t next = nextNetworkIndex(store_, triedMask_);
  if (next == kNoWifiSlot) return false;
  attempt_ = next;
  active_ = store_.slots[next].value;
  source_ = WifiSource::Persisted;
  mode_ = WifiMode::NormalConnect;
  port_.cancelConnect();
  port_.connect(active_);
  return true;
}
constexpr void normalConnected() {
  if (mode_ != WifiMode::NormalConnect) return;
  mode_ = WifiMode::Connected;
  if (attempt_ != kNoWifiSlot && store_.slots[attempt_].used && store_.lastOk != attempt_) {
    store_.lastOk = attempt_;
    port_.saveStore(store_);
  }
}
constexpr const WifiNetworkStore& store() const { return store_; }
```

Private helper and members:

Add this private helper next to the existing private methods:

```cpp
constexpr void selectInitial() {
  triedMask_ = 0;
  attempt_ = nextNetworkIndex(store_, 0);
  if (attempt_ == kNoWifiSlot) {
    active_ = configured_;
    source_ = WifiSource::Configured;
  } else {
    active_ = store_.slots[attempt_].value;
    source_ = WifiSource::Persisted;
  }
}
```

Add these private members next to the existing `active_`/`candidate_` members:

```cpp
WifiNetworkStore store_{};
uint8_t triedMask_ = 0;
uint8_t attempt_ = kNoWifiSlot;
```

Remove the old `normalConnected()` and the old body of `load()`.

- [ ] **Step 4: Run to verify it passes**

`"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_wifi_provisioning.cpp` → exit 0.

- [ ] **Step 5: Commit**

```bash
git add hardware/gdey042t81_esp32/src/network_progress/wifi_provisioning.h tests/cpp/test_wifi_provisioning.cpp
git commit -m "feat(wifi): select and fall back across stored networks"
```

---

### Task 3: Migration, persistence and the compiled fallback

**Files:**
- Modify: `wifi_provisioning.h`, `tests/cpp/test_wifi_provisioning.cpp`

**Interfaces:**
- Consumes: Task 1–2.
- Produces: the migration and fallback behaviour exercised below.

- [ ] **Step 1: Write the failing tests**

```cpp
constexpr bool migratesLegacy() {
  FakeWifi port;  // present = true, stored = previous
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load();
  return port.storeLoads == 1 && port.storeSaves == 1 && port.saves == 0 &&
    port.store.count == 1 && sameSsid(port.store.slots[0].value.ssid, "saved-lan") &&
    equal(wifi.selected(), previous) && wifi.source() == WifiSource::Persisted;
}
constexpr bool ignoresBrokenStore() {
  FakeWifi port;
  port.storePresent = true;
  port.store.count = 2;
  port.store.slots[0].value = previous;
  port.store.slots[0].used = 1;
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load();
  return equal(wifi.selected(), previous) && port.store.count == 1 && port.storeSaves == 1;
}
constexpr bool compiledFallback() {
  FakeWifi port;
  port.present = false; port.storePresent = false;
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load();
  return equal(wifi.selected(), configured) && wifi.source() == WifiSource::Configured &&
    port.storeSaves == 0;
}

static_assert(migratesLegacy(), "legacy validated migrates once and is not rewritten");
static_assert(ignoresBrokenStore(), "inconsistent store falls back to legacy");
static_assert(compiledFallback(), "empty store uses the compiled pair");
```

- [ ] **Step 2: Run to verify it fails**

Expected: both `migratesLegacy()` and `ignoresBrokenStore()` fail on `port.storeSaves == 1`,
because Task 2 loads the legacy pair into RAM but does not persist the migration.

- [ ] **Step 3: Implement the migration write**

In the legacy branch of `load()`, after `addNetwork(store_, legacy);`, add the one-time write:

```cpp
      store_.lastOk = 0;
      port_.saveStore(store_);  // migration; a failed write keeps legacy in RAM
```

The final function reads:

```cpp
constexpr void load() {
  WifiNetworkStore stored{};
  if (port_.loadStore(stored) && storeConsistent(stored)) {
    store_ = stored;
  } else {
    WifiCredentials legacy{};
    if (port_.loadCredentials(legacy) && validWifiCredentials(legacy)) {
      store_ = {};
      addNetwork(store_, legacy);
      store_.lastOk = 0;
      port_.saveStore(store_);
    } else {
      store_ = {};
    }
  }
  mode_ = WifiMode::NormalConnect;
  selectInitial();
}
```

- [ ] **Step 4: Run to verify it passes**

`"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_wifi_provisioning.cpp` → exit 0.

- [ ] **Step 5: Commit**

```bash
git add hardware/gdey042t81_esp32/src/network_progress/wifi_provisioning.h tests/cpp/test_wifi_provisioning.cpp
git commit -m "feat(wifi): migrate the validated pair into the store"
```

---

### Task 4: Add/update, forget and full-store rejection

**Files:**
- Modify: `wifi_provisioning.h`, `tests/cpp/test_wifi_provisioning.cpp`

**Interfaces:**
- Consumes: Task 1–3.
- Produces: `WifiResult::{StoreFull, StoreWriteFailed, Forgotten}`, `WifiProvisioning::forget()`,
  pre-candidate full-store check, dual write on success.

- [ ] **Step 1: Write the failing tests**

```cpp
constexpr bool rejectsWhenFull() {
  FakeWifi port;
  port.present = false; port.storePresent = true;
  addNetwork(port.store, cred("net-a", "password1"));
  addNetwork(port.store, cred("net-b", "password2"));
  addNetwork(port.store, cred("net-c", "password3"));
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load(); wifi.enterProvisioning();
  return !wifi.submit(cred("net-d", "password4"), 0) &&
    wifi.result() == WifiResult::StoreFull && port.connects == 0 && port.saves == 0;
}
constexpr bool addsOnSuccess() {
  FakeWifi port;
  port.present = false; port.storePresent = true;
  addNetwork(port.store, cred("net-a", "password1"));
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load(); wifi.enterProvisioning();
  wifi.submit(cred("net-b", "password2"), 0);
  wifi.poll(1); port.candidateReady = true;
  const bool ok = wifi.poll(2);
  return ok && port.store.count == 2 && port.store.lastOk == 1 &&
    sameSsid(port.store.slots[1].value.ssid, "net-b") &&
    sameSsid(port.stored.ssid, "net-b") && port.saves == 1;
}
constexpr bool forgetsAndPersists() {
  FakeWifi port;
  port.present = false; port.storePresent = true;
  addNetwork(port.store, cred("net-a", "password1"));
  addNetwork(port.store, cred("net-b", "password2"));
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load(); wifi.enterProvisioning();
  const bool ok = wifi.forget(0);
  return ok && wifi.result() == WifiResult::Forgotten && port.store.count == 1 &&
    sameSsid(port.store.slots[0].value.ssid, "net-b") && port.store.lastOk == 0 &&
    port.saves == 0;
}
constexpr bool forgetBlockedDuringCandidate() {
  FakeWifi port;
  port.present = false; port.storePresent = true;
  addNetwork(port.store, cred("net-a", "password1"));
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load(); wifi.enterProvisioning();
  wifi.submit(cred("net-b", "password2"), 0);
  return !wifi.forget(0) && wifi.result() == WifiResult::ForgetRejected && port.store.count == 1;
}
constexpr bool forgetWriteFailureKeepsStore() {
  FakeWifi port;
  port.present = false; port.storePresent = true;
  addNetwork(port.store, cred("net-a", "password1"));
  WifiProvisioning<FakeWifi> wifi(port, configured);
  wifi.load(); wifi.enterProvisioning();
  port.storeSaveOK = false;
  return !wifi.forget(0) && wifi.result() == WifiResult::StoreWriteFailed &&
    port.store.count == 1 && sameSsid(port.store.slots[0].value.ssid, "net-a");
}

static_assert(rejectsWhenFull(), "fourth network is rejected before the candidate");
static_assert(addsOnSuccess(), "success adds the slot and dual-writes validated");
static_assert(forgetsAndPersists(), "forget compacts without touching validated");
static_assert(forgetBlockedDuringCandidate(), "no forget while a candidate is pending");
static_assert(forgetWriteFailureKeepsStore(), "failed write leaves the store unchanged");
```

- [ ] **Step 2: Run to verify it fails**

Expected: `error: 'StoreFull' is not a member of 'WifiResult'`.

- [ ] **Step 3: Implement the provisioning changes**

Extend the enum:

```cpp
enum class WifiResult {
  None, Connecting, Saved, Timeout, ConnectFailed, SaveFailed, SoftApFailed,
  StoreFull, StoreWriteFailed, Forgotten, ForgetRejected
};
```

In `submit()`, before starting the candidate:

```cpp
if (findNetwork(store_, candidate.ssid) < 0 && store_.count >= kMaxWifiNetworks) {
  result_ = WifiResult::StoreFull;
  return false;
}
```

Replace the success block inside `poll()`:

```cpp
if (port_.candidateConnected(candidate_)) {
  if (!port_.saveCredentials(candidate_)) { reject(WifiResult::SaveFailed); return false; }
  WifiNetworkStore next = store_;
  if (!addNetwork(next, candidate_)) { reject(WifiResult::StoreFull); return false; }
  next.lastOk = uint8_t(findNetwork(next, candidate_.ssid));
  if (!port_.saveStore(next)) { reject(WifiResult::StoreWriteFailed); return false; }
  store_ = next;
  active_ = candidate_;
  candidate_ = {};
  if (!port_.stopSoftAP()) {
    mode_ = WifiMode::Provisioning;
    result_ = WifiResult::SoftApFailed;
    return false;
  }
  source_ = WifiSource::Persisted;
  mode_ = WifiMode::Connected;
  result_ = WifiResult::Saved;
  return true;
}
```

Add the forget method:

```cpp
constexpr bool forget(uint8_t index) {
  if (mode_ != WifiMode::Provisioning) { result_ = WifiResult::ForgetRejected; return false; }
  WifiNetworkStore next = store_;
  if (!forgetNetwork(next, index)) { result_ = WifiResult::ForgetRejected; return false; }
  if (!port_.saveStore(next)) { result_ = WifiResult::StoreWriteFailed; return false; }
  store_ = next;
  result_ = WifiResult::Forgotten;
  return true;
}
```

- [ ] **Step 4: Run to verify it passes**

`"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_wifi_provisioning.cpp` → exit 0.

- [ ] **Step 5: Commit**

```bash
git add hardware/gdey042t81_esp32/src/network_progress/wifi_provisioning.h tests/cpp/test_wifi_provisioning.cpp
git commit -m "feat(wifi): add, update and forget stored networks"
```

---

### Task 5: Machine fallback wiring

**Files:**
- Modify: `machine.h`, `tests/cpp/test_network_progress.cpp`

**Interfaces:**
- Consumes: `WifiProvisioning::nextAttempt()` through the port.
- Produces: `Port::nextWifi()` (default false), `kMaxWifiAttempts = 3`,
  `wifiAttemptAllowed()`, `Machine::advanceWifi()`.

- [ ] **Step 1: Write the failing compile-time cap test**

Add near the top of `tests/cpp/test_network_progress.cpp`:

```cpp
static_assert(kMaxWifiAttempts == 3, "three association attempts per cycle");
static_assert(wifiAttemptAllowed(1) && wifiAttemptAllowed(2) && !wifiAttemptAllowed(3),
  "the third failure ends the cycle");
```

- [ ] **Step 2: Run to verify it fails**

```bash
TC="D:/Codex/eink-panel/.venv-hw/pio-core/packages/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-g++.exe"
"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_network_progress.cpp
```

Expected: `error: 'kMaxWifiAttempts' was not declared in this scope`.

- [ ] **Step 3: Implement the hook and the advance**

In `machine.h`, above `class Port`:

```cpp
constexpr uint8_t kMaxWifiAttempts = 3;
constexpr bool wifiAttemptAllowed(uint8_t attempts) { return attempts < kMaxWifiAttempts; }
```

Add to `Port`, next to `beginWifi()`:

```cpp
// Starts the next stored network; false when the list is exhausted.
virtual bool nextWifi() { return false; }
```

In `Machine`, replace the `WifiConnect` case:

```cpp
case State::WifiConnect:
  if (expired(n, segment_, 15000)) {
    cancelAssociation();
    if (advanceWifi()) return;
    fail(Failure::WifiAssociationFailure); return;
  }
  if (port_.connected()) { associating_ = false; state_ = State::HostResolve; }
  else if (port_.associationFailed()) {
    cancelAssociation();
    if (!advanceWifi()) fail(Failure::WifiAssociationFailure);
  }
  return;
```

Add this private helper:

```cpp
bool advanceWifi() {
  if (!wifiAttemptAllowed(wifiAttempts_) || !port_.nextWifi()) return false;
  ++wifiAttempts_;
  segment_ = port_.now();
  associating_ = true;
  return true;
}
```

Add this private member next to the existing `bool httpActive_`/`bool tcpStarted_` members:

```cpp
uint8_t wifiAttempts_ = 0;
```

Set `wifiAttempts_ = 1;` inside `startWifi()` before `port_.beginWifi()`.

- [ ] **Step 4: Verify compile**

```bash
"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_network_progress.cpp
```

Expected: exit 0. The runtime harness is compile-checked only; do not run it.

- [ ] **Step 5: Commit**

```bash
git add hardware/gdey042t81_esp32/src/network_progress/machine.h tests/cpp/test_network_progress.cpp
git commit -m "feat(wifi): advance through stored networks in WifiConnect"
```

---

### Task 6: Device port, setup page and routes

**Files:**
- Modify: `wifi_esp32.h`, `main.cpp`

**Interfaces:**
- Consumes: `WifiNetworkStore`, `WifiProvisioning::store()/forget()`, `WifiResult` additions.
- Produces: `EspWifiPort::loadStore/saveStore`, `EspPort::nextWifi()`,
  `GET /` list, `POST /forget`, 409 on a full store, boot log line.

- [ ] **Step 1: Add the NVS store methods**

In `EspWifiPort`, after `saveCredentials`:

```cpp
bool loadStore(WifiNetworkStore& out) {
  Preferences storage;
  if (!storage.begin("eink-wifi", true)) return false;
  const bool loaded = storage.getBytesLength("networks") == sizeof(out) &&
    storage.getBytes("networks", &out, sizeof(out)) == sizeof(out);
  storage.end();
  return loaded;
}
bool saveStore(const WifiNetworkStore& value) {
  Preferences storage;
  if (!storage.begin("eink-wifi")) return false;
  const bool saved = storage.putBytes("networks", &value, sizeof(value)) == sizeof(value);
  storage.end();
  return saved;
}
```

- [ ] **Step 2: Build the setup page and routes**

Replace `kProvisioningHtml` and the `GET /` lambda with:

```cpp
void appendEscaped(String& out, const char* text) {
  for (const char* p = text; *p; ++p) {
    switch (*p) {
      case '&': out += "&amp;"; break;
      case '<': out += "&lt;"; break;
      case '>': out += "&gt;"; break;
      case '"': out += "&quot;"; break;
      case '\'': out += "&#39;"; break;
      default: out += *p;
    }
  }
}

String provisioningPage(const WifiNetworkStore& store, const char* resultLine) {
  String page = "<!doctype html><html><head><meta charset=utf-8><title>Wi-Fi setup</title></head>"
    "<body><h1>Wi-Fi setup</h1>";
  page += resultLine;
  page += "<h2>Saved networks</h2><table>";
  for (uint8_t i = 0; i < kMaxWifiNetworks; ++i) {
    if (!store.slots[i].used) continue;
    page += "<tr><td>"; page += char('0' + i); page += "</td><td>";
    appendEscaped(page, store.slots[i].value.ssid);
    page += "</td><td><form method=post action=/forget style=display:inline>"
      "<input type=hidden name=index value=";
    page += char('0' + i);
    page += "><button>Forget</button></form></td></tr>";
  }
  page += "</table><p>";
  page += store.count ? "Stored networks are tried last-success first." : "No saved network yet.";
  page += "</p><h2>Add or update</h2><form method=post action=/configure>"
    "<label>SSID <input name=ssid required maxlength=32></label><br>"
    "<label>Password <input name=password type=password maxlength=64></label><br>"
    "<button>Connect and save</button></form><p>Credentials are saved only after connection. "
    "Reload this page to see the result.</p></body></html>";
  return page;
}
```

`GET /`:

```cpp
server_.on("/", HTTP_GET, [this] {
  server_.send(200, "text/html; charset=utf-8",
    provisioningPage(wifi_.store(), resultText()));
});
```

Replace the whole `/configure` registration with:

```cpp
server_.on("/configure", HTTP_POST, [this] {
  const String ssid = server_.arg("ssid"), password = server_.arg("password");
  if (!server_.hasArg("ssid") || !server_.hasArg("password") ||
      ssid.length() != std::strlen(ssid.c_str()) ||
      password.length() != std::strlen(password.c_str())) {
    server_.send(400, "text/plain", "Invalid credentials or connection already in progress.");
    return;
  }
  if (!wifi_.submit(wifiCredentials(ssid.c_str(), password.c_str()), millis())) {
    if (wifi_.result() == WifiResult::StoreFull) {
      server_.send(409, "text/plain", "Store full; forget one network first.");
    } else {
      server_.send(400, "text/plain", "Invalid credentials or connection already in progress.");
    }
    return;
  }
  server_.send(202, "text/plain",
    "Connecting. Save follows successful LAN connection. Reload / for result; setup AP closes on success.");
  // Close the AP listener before the candidate window (existing lwIP safety rule).
  server_.stop();
  serverStopped_ = true;
});
```

`POST /forget` — place this registration immediately after the `/configure` block and before
`routesInstalled_ = true;`:

```cpp
server_.on("/forget", HTTP_POST, [this] {
  const String raw = server_.arg("index");
  if (!server_.hasArg("index") || raw.length() != 1 || raw[0] < '0' || raw[0] > '2') {
    server_.send(400, "text/plain", "Invalid index.");
    return;
  }
  if (!wifi_.forget(uint8_t(raw[0] - '0'))) {
    server_.send(wifi_.result() == WifiResult::StoreWriteFailed ? 500 : 409,
      "text/plain", wifi_.result() == WifiResult::StoreWriteFailed
        ? "Store write failed; nothing changed."
        : "Cannot forget while a connection attempt is pending.");
    return;
  }
  server_.send(202, "text/plain", "Network forgotten. Reload / to see the list.");
});
```

Extend `resultText()`:

```cpp
case WifiResult::StoreFull: return "<p>Store full; forget one network first.</p>";
case WifiResult::StoreWriteFailed: return "<p>Store write failed; the previous list is unchanged.</p>";
case WifiResult::Forgotten: return "<p>Network forgotten.</p>";
case WifiResult::ForgetRejected: return "<p>Cannot forget now; finish or retry the connection first.</p>";
```

- [ ] **Step 3: Delegate and log**

In `main.cpp`, add to `EspPort`:

```cpp
bool nextWifi() override { return wifi_.nextAttempt(); }
```

In `setup()`, after the refresh-count line:

```cpp
Serial.printf("NETWORK_WIFI_STORE=%u HEAP=%u\n",
  unsigned(sizeof(WifiNetworkStore)), unsigned(ESP.getFreeHeap()));
nvs_stats_t nvsStats{};
if (nvs_get_stats(nullptr, &nvsStats) == ESP_OK) {
  Serial.printf("NETWORK_NVS used=%u free=%u total=%u\n",
    unsigned(nvsStats.used_entries), unsigned(nvsStats.free_entries),
    unsigned(nvsStats.total_entries));
}
```

Add `#include <nvs.h>` with the other includes.

- [ ] **Step 4: Build both environments**

Create the stage config (outside the repo):

```bash
mkdir -p D:/Codex/round2-r3d-20261109
cp D:/Codex/round2-r6-ota-20261107/platformio-round2-r6-ota.ini D:/Codex/round2-r3d-20261109/platformio-round2-r3d.ini
sed -i 's#round2-r6-ota-20261107/build#round2-r3d-20261109/build#; s#default_envs = esp32-m1-network-progress-ota#default_envs = esp32-m1-network-progress#' D:/Codex/round2-r3d-20261109/platformio-round2-r3d.ini
```

Then:

```bash
D:/Codex/eink-panel/.venv-hw/Scripts/python.exe -B -m platformio run \
  -d C:/Users/cslki/.codex/worktrees/a5b3/eink-panel/hardware/gdey042t81_esp32 \
  -c D:/Codex/round2-r3d-20261109/platformio-round2-r3d.ini \
  -e esp32-m1-network-progress --disable-auto-clean -j 4

D:/Codex/eink-panel/.venv-hw/Scripts/python.exe -B -m platformio run \
  -d C:/Users/cslki/.codex/worktrees/a5b3/eink-panel/hardware/gdey042t81_esp32 \
  -c D:/Codex/round2-r3d-20261109/platformio-round2-r3d.ini \
  -e esp32-m1-network-progress-ota --disable-auto-clean -j 4
```

Expected: both exit 0. Record the RAM, flash and the `NETWORK_WIFI_STORE` constant
(301) for the acceptance evidence. Do not upload.

- [ ] **Step 5: Commit**

```bash
git add hardware/gdey042t81_esp32/src/network_progress/wifi_esp32.h hardware/gdey042t81_esp32/src/network_progress/main.cpp
git commit -m "feat(wifi): list, add and forget networks on the setup page"
```

---

### Task 7: Regression and review

**Files:** none (verification only).

- [ ] **Step 1: Compile both C++ harnesses**

```bash
TC="D:/Codex/eink-panel/.venv-hw/pio-core/packages/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-g++.exe"
"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_wifi_provisioning.cpp
"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_network_progress.cpp
"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_provisioning_button.cpp
"$TC" -std=gnu++17 -Wall -Wextra -fsyntax-only tests/cpp/test_ota_protocol.cpp
```

Expected: all exit 0. `test_wifi_provisioning.cpp` is the only one whose assertions actually run.

- [ ] **Step 2: Run the Host suites**

```bash
PYTHONPATH="D:/Codex/round2-multipage-20261108/host-deps" "C:/Users/cslki/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe" -m pytest -q
node --test tests/frontend
```

Expected: 697 passed; 57 pass, 0 fail.

- [ ] **Step 3: Credential scan**

```bash
git diff --stat HEAD~6..HEAD
grep -rn "password" hardware/gdey042t81_esp32/src/network_progress/wifi_esp32.h | head
```

Expected: no literal SSID/password in the diff; the only `password` occurrences are form field
names. Do not print any stored credential.

- [ ] **Step 4: Request a code review**

Use `superpowers:requesting-code-review` with the diff range and the spec path. Fix Critical and
Important findings before Task 8. Minor findings go to the ledger.

- [ ] **Step 5: Commit any review fixes**

```bash
git add hardware/gdey042t81_esp32/src/network_progress tests/cpp/test_wifi_provisioning.cpp
git commit -m "fix(wifi): address the multi-network review"
```

Skip this commit when the review is clean.

---

### Task 8: Physical acceptance and documentation

**Files:**
- Modify: `PROJECT_STATE.md`, `docs/GOAL.md`, `docs/R3D-MULTI-NETWORK.md` (new runbook)
- Evidence: `D:/Codex/round2-r3d-20261109/acceptance/` (outside the repo)

**Stop rule:** flashing needs explicit authorization. The plan stops here after the build; the
operator authorizes the upload separately.

- [ ] **Step 1: Prepare two networks**

Use the phone hotspot (already provisioned) and one second network the Host can join (home
router or a second hotspot). Keep the Host on a network the device can reach during the test.
Record both SSIDs in the local evidence only, masked as `net-a` / `net-b` in committed text.

- [ ] **Step 2: Flash and provision the second network**

After authorization: flash `esp32-m1-network-progress` to the device, hold S1 → AP
`eink-panel-setup` → `/` → add the second network. Expect the list to show 2 rows and the
device to keep its current frame (no refresh from provisioning alone).

- [ ] **Step 3: Verify boot preference and failover**

1. Reboot; the device joins the last successful network; `/api/pages/status` shows 200 then 304.
2. Turn that AP off. Within one poll plus the fallback (≤60 s + 45 s) the device joins the other
   network and fetches the current frame (200, 15000 B, ETag = SHA-256); the next poll is 304.
3. Record `refresh_count`; it increases only when the content changes.

- [ ] **Step 4: Verify forget and the full-store rejection**

1. From the setup AP, try adding a fourth network when three are stored: 409, list unchanged.
2. Forget the active network; the next retry joins the remaining one.
3. Confirm `validated` is untouched by forget: reflash the previous image (separate authorization)
   and verify it still joins one network after a rollback.

- [ ] **Step 5: Record evidence**

Create `D:/Codex/round2-r3d-20261109/acceptance/README.md` with: build exit codes, RAM/flash,
`NETWORK_WIFI_STORE=301`, `NETWORK_NVS` stats, the serial log excerpts (SSIDs masked), the
failover timeline, ETags, counts, and the rollback result. No password, no unmasked SSID, no
tailnet name.

- [ ] **Step 6: Documentation and commit**

Append an R3D section to `PROJECT_STATE.md` (results, limits, next stage), update `docs/GOAL.md`
(M2 closed or blocked with the exact evidence), add `docs/R3D-MULTI-NETWORK.md` with the operator
steps (add/forget/failover/rollback), then:

```bash
git add PROJECT_STATE.md docs/GOAL.md docs/R3D-MULTI-NETWORK.md
git commit -m "docs(r3d): record the multi-network acceptance"
```

Do not push, tag or open a PR.

---

## Verification Summary

| Claim | Evidence |
| --- | --- |
| Store layout is fixed | `static_assert` sizes in Task 1 compile |
| Add/update/full/forget semantics | Task 1 and Task 4 static_asserts |
| Selection and fallback order | Task 2 `selectionOrder`/`fallsBackInOrder` |
| Legacy migration and compiled fallback | Task 3 static_asserts |
| Three attempts, then FailureWait | `kMaxWifiAttempts` assert + device failover in Task 8 |
| Setup page lists/adds/forgets without overwriting | Task 6 build + Task 8 page checks |
| No credential leak | Task 7 scan + evidence review |
| Both firmware envs build | Task 6 PlatformIO runs, exit 0 |
| Host untouched | Task 7 pytest 697 / frontend 57 |
| Rollback still works | Task 8 Step 4 |

## Stop Rules

- Stop before flashing without explicit authorization.
- Stop if the store size assert fails or a build needs a private header that is not present.
- Stop if a test would need a host runtime compiler that does not exist; record compile-only and
  do not claim it ran.
- Never print, commit or screenshot a password or an unmasked SSID.
- Never erase NVS or change the partition table to make a test pass.
- Do not push, tag or start another stage in this plan.
