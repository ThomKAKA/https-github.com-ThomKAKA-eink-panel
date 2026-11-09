#pragma once
#include <cstddef>
#include <cstdint>

namespace eink::network_progress {
struct WifiCredentials {
  char ssid[33]{};
  char password[65]{};
};

constexpr WifiCredentials wifiCredentials(const char* ssid, const char* password) {
  WifiCredentials value{};
  size_t i = 0;
  while (i < sizeof(value.ssid) && ssid[i]) { value.ssid[i] = ssid[i]; ++i; }
  if (i == sizeof(value.ssid)) return {};
  i = 0;
  while (i < sizeof(value.password) && password[i]) { value.password[i] = password[i]; ++i; }
  if (i == sizeof(value.password)) return {};
  return value;
}

constexpr bool validWifiCredentials(const WifiCredentials& value) {
  size_t ssid = 0, password = 0;
  while (ssid < sizeof(value.ssid) && value.ssid[ssid]) ++ssid;
  while (password < sizeof(value.password) && value.password[password]) ++password;
  if (!ssid || ssid > 32 || password > 64 || (password && password < 8)) return false;
  if (password == 64) for (size_t i = 0; i < password; ++i) {
    const char c = value.password[i];
    if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'))) return false;
  }
  return true;
}

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

enum class WifiSource { Configured, Persisted };
enum class WifiMode { NormalConnect, Provisioning, CandidateConnect, Connected };
enum class WifiResult { None, Connecting, Saved, Timeout, ConnectFailed, SaveFailed, SoftApFailed };
constexpr uint32_t kCandidateWifiTimeoutMs = 15000;

// Port supplies only credential storage, Wi-Fi connection and SoftAP lifecycle.
// The existing network Machine remains the sole owner of discovery/frame/display.
template<class WifiPort>
class WifiProvisioning {
 public:
  constexpr WifiProvisioning(WifiPort& port, WifiCredentials configured)
      : port_(port), configured_(configured), active_(configured) {}
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
  constexpr bool enterProvisioning() {
    if (mode_ == WifiMode::Provisioning || mode_ == WifiMode::CandidateConnect) return false;
    if (!port_.startSoftAP()) { result_ = WifiResult::SoftApFailed; return false; }
    mode_ = WifiMode::Provisioning; result_ = WifiResult::None;
    return true;
  }
  constexpr bool submit(WifiCredentials candidate, uint32_t now) {
    if (mode_ != WifiMode::Provisioning || !validWifiCredentials(candidate)) return false;
    candidate_ = candidate; startedAt_ = now; candidateStarted_ = false;
    mode_ = WifiMode::CandidateConnect; result_ = WifiResult::Connecting;
    port_.cancelConnect();
    return true;
  }
  constexpr bool poll(uint32_t now) {
    if (mode_ != WifiMode::CandidateConnect) return false;
    if (uint32_t(now - startedAt_) >= kCandidateWifiTimeoutMs) { reject(WifiResult::Timeout); return false; }
    if (!candidateStarted_) {
      // Do not accept the old association (including a same-SSID old password).
      if (port_.stationConnected()) return false;
      candidateStarted_ = true;
      if (!port_.connect(candidate_)) reject(WifiResult::ConnectFailed);
      return false;
    }
    if (port_.candidateConnected(candidate_)) {
      if (!port_.saveCredentials(candidate_)) { reject(WifiResult::SaveFailed); return false; }
      active_ = candidate_; source_ = WifiSource::Persisted;
      candidate_ = {};
      if (!port_.stopSoftAP()) {
        mode_ = WifiMode::Provisioning; result_ = WifiResult::SoftApFailed;
        return false;
      }
      mode_ = WifiMode::Connected; result_ = WifiResult::Saved;
      return true;  // Existing Machine enters its original HostResolve state.
    }
    if (port_.connectionFailed()) reject(WifiResult::ConnectFailed);
    return false;
  }
  constexpr const WifiCredentials& selected() const { return active_; }
  constexpr const WifiNetworkStore& store() const { return store_; }
  constexpr WifiSource source() const { return source_; }
  constexpr WifiMode mode() const { return mode_; }
  constexpr WifiResult result() const { return result_; }
 private:
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
  constexpr void reject(WifiResult result) {
    port_.cancelConnect(); candidate_ = {};
    mode_ = WifiMode::Provisioning; result_ = result;
  }
  WifiPort& port_;
  const WifiCredentials configured_;
  WifiCredentials active_, candidate_{};
  WifiNetworkStore store_{};
  uint8_t triedMask_ = 0;
  uint8_t attempt_ = kNoWifiSlot;
  WifiSource source_ = WifiSource::Configured;
  WifiMode mode_ = WifiMode::NormalConnect;
  WifiResult result_ = WifiResult::None;
  uint32_t startedAt_ = 0;
  bool candidateStarted_ = false;
};
}  // namespace eink::network_progress
