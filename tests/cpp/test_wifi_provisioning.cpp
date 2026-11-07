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
