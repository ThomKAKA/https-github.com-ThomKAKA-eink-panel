// C++17 compile-time contract tests: static_assert evaluates the production
// controller with a fake Wi-Fi/storage port; no Arduino or hardware is involved.
#include "../../hardware/gdey042t81_esp32/src/network_progress/wifi_provisioning.h"
using namespace eink::network_progress;

constexpr auto configured = wifiCredentials("configured-lan", "configured-pass");
constexpr auto previous = wifiCredentials("saved-lan", "previous-pass");
constexpr auto candidate = wifiCredentials("new-lan", "candidate-pass");

constexpr bool equal(const WifiCredentials& a, const WifiCredentials& b) {
  for (unsigned i = 0; i < sizeof(a.ssid); ++i) if (a.ssid[i] != b.ssid[i]) return false;
  for (unsigned i = 0; i < sizeof(a.password); ++i) if (a.password[i] != b.password[i]) return false;
  return true;
}
struct FakeWifi {
  WifiCredentials stored = previous, connectedWith{};
  bool present = true, stationUp = false, candidateReady = false, failed = false;
  bool connectOK = true, saveOK = true, apStartOK = true, apStopOK = true;
  bool deferDisconnect = false;
  unsigned loads = 0, connects = 0, cancels = 0, apStarts = 0, apStops = 0;
  unsigned saveAttempts = 0, saves = 0;
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
  constexpr bool loadCredentials(WifiCredentials& out) { ++loads; out = stored; return present; }
  constexpr bool saveCredentials(const WifiCredentials& value) {
    ++saveAttempts;
    if (!saveOK || !candidateReady) return false;
    stored = value; present = true; ++saves; return true;
  }
  constexpr bool connect(const WifiCredentials& value) {
    ++connects; connectedWith = value; candidateReady = false; return connectOK;
  }
  constexpr void cancelConnect() { ++cancels; if (!deferDisconnect) stationUp = false; }
  constexpr bool stationConnected() { return stationUp; }
  constexpr bool candidateConnected(const WifiCredentials&) { return candidateReady; }
  constexpr bool connectionFailed() { return failed; }
  constexpr bool startSoftAP() { ++apStarts; return apStartOK; }
  constexpr bool stopSoftAP() { ++apStops; return apStopOK; }
};

constexpr bool selection(bool present) {
  FakeWifi port; port.present = present;
  WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.beginNormal();
  return equal(wifi.selected(), present ? previous : configured) &&
    equal(port.connectedWith, wifi.selected()) &&
    wifi.source() == (present ? WifiSource::Persisted : WifiSource::Configured) &&
    port.saves == 0 && port.apStarts == 0;
}
constexpr bool invalidStored() {
  FakeWifi port; port.stored = {};
  WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load();
  return equal(wifi.selected(), configured) && wifi.source() == WifiSource::Configured;
}
constexpr bool normalFailure() {
  FakeWifi port; port.failed = true;
  WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.beginNormal();
  wifi.poll(kCandidateWifiTimeoutMs);
  return wifi.mode() == WifiMode::NormalConnect && port.apStarts == 0 && port.saves == 0;
}
constexpr bool explicitEntry() {
  FakeWifi port; WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load();
  const bool entered = wifi.enterProvisioning();
  return entered && wifi.mode() == WifiMode::Provisioning && port.apStarts == 1 && port.apStops == 0;
}
constexpr bool candidatePath() {
  FakeWifi port; WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning();
  const bool submitted = wifi.submit(candidate, 100);
  wifi.poll(101);
  return submitted && wifi.mode() == WifiMode::CandidateConnect && port.cancels == 1 && port.connects == 1 &&
    equal(port.connectedWith, candidate) && port.saveAttempts == 0 && equal(port.stored, previous);
}
constexpr bool staleAssociation() {
  FakeWifi port; port.stationUp = true; port.candidateReady = true; port.deferDisconnect = true;
  WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning(); wifi.submit(candidate, 0);
  wifi.poll(1);
  return port.connects == 0 && port.saveAttempts == 0 && equal(port.stored, previous) && wifi.mode() == WifiMode::CandidateConnect;
}
constexpr bool candidateSuccess() {
  FakeWifi port; WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning(); wifi.submit(candidate, 0);
  wifi.poll(1); port.candidateReady = true;
  const bool handoff = wifi.poll(2);
  return handoff && port.saves == 1 && equal(port.stored, candidate) && equal(wifi.selected(), candidate) &&
    wifi.source() == WifiSource::Persisted && wifi.mode() == WifiMode::Connected && wifi.result() == WifiResult::Saved && port.apStops == 1;
}
constexpr bool candidateFailure(bool timeout) {
  FakeWifi port; WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning(); wifi.submit(candidate, 0);
  wifi.poll(1); port.failed = !timeout;
  const bool handoff = wifi.poll(timeout ? kCandidateWifiTimeoutMs : 2);
  return !handoff && port.saveAttempts == 0 && equal(port.stored, previous) && equal(wifi.selected(), previous) &&
    wifi.mode() == WifiMode::Provisioning && port.apStops == 0 &&
    wifi.result() == (timeout ? WifiResult::Timeout : WifiResult::ConnectFailed);
}
constexpr bool reboot() {
  FakeWifi port; WifiProvisioning<FakeWifi> first(port, configured); first.load(); first.enterProvisioning(); first.submit(candidate, 0);
  first.poll(1); port.candidateReady = true; first.poll(2);
  WifiProvisioning<FakeWifi> restarted(port, configured); restarted.load(); restarted.beginNormal();
  return restarted.source() == WifiSource::Persisted && equal(port.connectedWith, candidate) && port.apStarts == 1 && port.saves == 1;
}
constexpr bool normalHandoff() {
  FakeWifi port; WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.beginNormal(); wifi.normalConnected();
  return wifi.mode() == WifiMode::Connected && wifi.source() == WifiSource::Persisted && port.apStarts == 0 && port.saves == 0;
}
constexpr bool saveFailure() {
  FakeWifi port; port.saveOK = false;
  WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning(); wifi.submit(candidate, 0);
  wifi.poll(1); port.candidateReady = true;
  return !wifi.poll(2) && port.saveAttempts == 1 && port.saves == 0 && equal(port.stored, previous) &&
    wifi.mode() == WifiMode::Provisioning && wifi.result() == WifiResult::SaveFailed && port.apStops == 0;
}
constexpr bool busySubmission() {
  FakeWifi port; WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning(); wifi.submit(candidate, 0);
  return !wifi.submit(configured, 1) && port.cancels == 1 && port.saves == 0;
}
constexpr bool timeoutRollover() {
  FakeWifi port; WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning(); wifi.submit(candidate, 0xfffffff0u);
  wifi.poll(0xfffffff1u); wifi.poll(uint32_t(0xfffffff0u + kCandidateWifiTimeoutMs));
  return wifi.result() == WifiResult::Timeout && equal(port.stored, previous);
}
constexpr bool invalidSubmission() {
  FakeWifi port; WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning();
  return !wifi.submit(wifiCredentials("", "candidate-pass"), 0) && port.cancels == 0 && port.connects == 0 && port.saves == 0;
}
constexpr bool immediateConnectFailure() {
  FakeWifi port; port.connectOK = false;
  WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning(); wifi.submit(candidate, 0); wifi.poll(1);
  return wifi.mode() == WifiMode::Provisioning && wifi.result() == WifiResult::ConnectFailed && equal(port.stored, previous) && port.saves == 0;
}
constexpr bool apStartFailure() {
  FakeWifi port; port.apStartOK = false;
  WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load();
  return !wifi.enterProvisioning() && wifi.mode() == WifiMode::NormalConnect && port.saves == 0;
}
constexpr bool apStopFailure() {
  FakeWifi port; port.apStopOK = false;
  WifiProvisioning<FakeWifi> wifi(port, configured); wifi.load(); wifi.enterProvisioning(); wifi.submit(candidate, 0);
  wifi.poll(1); port.candidateReady = true;
  return !wifi.poll(2) && port.saves == 1 && equal(port.stored, candidate) &&
    wifi.mode() == WifiMode::Provisioning && wifi.result() == WifiResult::SoftApFailed;
}

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
// Positive consistency witness: every accepted add/update and every rejected add
// (overflow, invalid credentials) must leave a store a reload still accepts.
constexpr bool addKeepsStoreConsistent() {
  WifiNetworkStore store{};
  if (!addNetwork(store, cred("net-a", "password1")) || !storeConsistent(store)) return false;
  if (!addNetwork(store, cred("net-b", "password2")) || !storeConsistent(store)) return false;
  if (!addNetwork(store, cred("net-c", "password3")) || !storeConsistent(store)) return false;
  if (addNetwork(store, cred("net-d", "password4"))) return false;
  if (!storeConsistent(store) || store.count != 3) return false;
  if (!addNetwork(store, cred("net-b", "newpass99")) || !storeConsistent(store)) return false;
  if (findNetwork(store, "net-b") != 1) return false;
  if (addNetwork(store, cred("", "password1"))) return false;
  return storeConsistent(store) && store.count == 3;
}
// Positive consistency and tail-clear witness: forgetting compacts leftwards, so
// the vacated last slot must be blank or the persisted blob fails to reload.
constexpr bool forgetClearsTailSlot() {
  WifiNetworkStore store{};
  if (!addNetwork(store, cred("net-a", "password1"))) return false;
  if (!addNetwork(store, cred("net-b", "password2"))) return false;
  if (!addNetwork(store, cred("net-c", "password3"))) return false;
  if (!storeConsistent(store)) return false;
  if (!forgetNetwork(store, 1)) return false;
  if (store.slots[kMaxWifiNetworks - 1].used) return false;
  if (store.slots[kMaxWifiNetworks - 1].value.ssid[0] != '\0') return false;
  if (!storeConsistent(store)) return false;
  if (!forgetNetwork(store, 1)) return false;
  if (store.slots[1].used || store.slots[kMaxWifiNetworks - 1].used) return false;
  if (!storeConsistent(store)) return false;
  if (!forgetNetwork(store, 0)) return false;
  if (forgetNetwork(store, 0)) return false;
  return storeConsistent(store) && !store.slots[0].used && !store.slots[1].used && !store.slots[2].used;
}

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

static_assert(kMaxWifiNetworks == 3, "store holds three networks");
static_assert(sizeof(WifiNetworkSlot) == 99, "slot layout changed");
static_assert(sizeof(WifiNetworkStore) == 301, "store layout changed");
static_assert(storeAddUpdate(), "add, update in place, reject when full");
static_assert(storeForget(), "forget compacts and fixes lastOk");
static_assert(storeRejectsMismatch(), "count must match used flags");
static_assert(rejectsInvalidEntry(), "invalid credentials never enter the store");
static_assert(rejectsBadLastOk(), "lastOk must point at a used slot");
static_assert(addKeepsStoreConsistent(), "every add and rejected add leaves a reloadable store");
static_assert(forgetClearsTailSlot(), "forget clears the vacated tail slot and leaves a reloadable store");

static_assert(selectionOrder(), "lastOk first, then stored order");
static_assert(fallsBackInOrder(), "three attempts then exhaustion");
static_assert(remembersSuccess(), "success updates lastOk once");

static_assert(selection(false), "configured credentials remain the initial source");
static_assert(selection(true), "validated persisted credentials have priority");
static_assert(invalidStored(), "invalid stored data does not replace configured credentials");
static_assert(normalFailure(), "normal Wi-Fi failure never opens provisioning");
static_assert(explicitEntry(), "explicit entry starts SoftAP");
static_assert(candidatePath(), "candidate connects before any save");
static_assert(staleAssociation(), "old connection cannot validate new credentials");
static_assert(candidateSuccess(), "success persists, stops SoftAP and permits R2 handoff");
static_assert(candidateFailure(false), "connection failure retains previous credentials and SoftAP");
static_assert(candidateFailure(true), "timeout retains previous credentials and SoftAP");
static_assert(reboot(), "new instance uses the successfully saved credentials");
static_assert(normalHandoff(), "normal saved connection is ready for existing R2");
static_assert(saveFailure(), "failed persistence does not permit handoff");
static_assert(busySubmission(), "one active candidate, no automatic retry");
static_assert(timeoutRollover(), "bounded candidate timeout follows millis rollover");
static_assert(invalidSubmission(), "invalid input is not connected or saved");
static_assert(immediateConnectFailure(), "immediate connection rejection retains old credentials");
static_assert(apStartFailure(), "failed setup does not enter provisioning");
static_assert(apStopFailure(), "failed SoftAP exit does not permit R2 handoff");
static_assert(validWifiCredentials(wifiCredentials("open-lan", "")), "explicit open LAN remains supported");
static_assert(!validWifiCredentials(wifiCredentials("lan", "short")), "short PSK is rejected");
static_assert(validWifiCredentials(wifiCredentials("lan", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")), "64 hex PSK remains supported");
static_assert(!validWifiCredentials(wifiCredentials("lan", "g123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")), "64 nonhex PSK is rejected");
