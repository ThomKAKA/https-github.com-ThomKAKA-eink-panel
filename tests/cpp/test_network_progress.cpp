// STEP017E host-run harness. Compile with C++17; no Arduino, socket or hardware.
#include "../../hardware/gdey042t81_esp32/src/network_progress/machine.h"
#include "../../hardware/gdey042t81_esp32/src/network_progress/report.h"
#include "../../hardware/gdey042t81_esp32/src/network_progress/provisioning_button.h"
#include <cassert>
#include <string>
#include <vector>
#include <algorithm>
using namespace eink::network_progress;

const std::string tag = "\"" + std::string(64, 'a') + "\"";
std::string head(int status = 200, const std::string& identity = tag) {
  return "HTTP/1.1 " + std::to_string(status) + " OK\r\n" +
    (status == 200 ? "Content-Type: application/octet-stream\r\nContent-Length: 15000\r\n" : "") +
    "ETag: " + identity + "\r\nX-Frame-Format: " + kFormat +
    "\r\nCache-Control: no-cache, no-transform\r\nConnection: close\r\n";
}
bool parse(const std::string& text, const char* sent = nullptr) {
  Headers h; h.reset(sent);
  for (unsigned char c : text) if (!h.feed(c)) return false;
  return h.done();
}

struct Fake final : Port {
  uint32_t clock = 0, ioAdvance = 0, hashAdvance = 0;
  bool configOK = true, initOK = true, wifi = true, associationBad = false;
  bool tcp = true, eof = true, crypto = true, accept = true, closeOK = true;
  unsigned pendingConnect = 0, initializations = 0, polls = 0;
  int sendResult = 1, receiveError = 0;
  unsigned starts = 0, connects = 0, closes = 0, displays = 0, cancellations = 0, calls = 0;
  size_t offset = 0, sendChunk = 512;
  std::string response = head() + "\r\n" + std::string(kFrameBytes, char(0xA5));
  std::string identity = tag, sentIdentity;
  struct Observation { ReportStage stage; std::string identity; unsigned displays; };
  std::vector<Observation> reports;
  ReportResult reportResult = ReportResult::Finished;
  std::string sentBytes;
  ResolvedHost configured{{192, 168, 1, 2}, 8000, HostSource::CONFIGURED_FALLBACK};
  ResolvedHost discovered{{192, 168, 1, 23}, 8765, HostSource::DISCOVERED};
  ResolvedHost endpoint = configured;
  bool discoveryAvailable = false;
  uint32_t resolveAdvance = 0;
  std::vector<ResolvedHost> connections;
  uint32_t now() override { ++calls; return clock; }
  ConfigResult validateConfiguration() override { ++calls; return configOK ? ConfigResult::Valid : ConfigResult::Invalid; }
  WifiInitResult initializeWifi() override { ++calls; ++initializations; return initOK ? WifiInitResult::Ready : WifiInitResult::Failed; }
  bool connected() override { ++calls; return wifi; }
  bool associationFailed() override { ++calls; return associationBad; }
  void beginWifi() override { ++calls; ++starts; }
  void cancelWifi() override { ++calls; ++cancellations; }
  unsigned provisioningEntries = 0, provisioningPolls = 0;
  bool provisioningReady = false;
  bool beginProvisioning() override { ++provisioningEntries; return true; }
  bool pollProvisioning() override { ++provisioningPolls; return provisioningReady; }
  void resolveHost() override {
    ++calls; clock += resolveAdvance;
    endpoint = eink::network_progress::resolveHost(discoveryAvailable ? &discovered : nullptr, configured);
  }
  ConnectResult beginTcp() override {
    ++calls; ++connects; offset = 0;
    connections.push_back(endpoint);
    return !tcp ? ConnectResult::Failed : pendingConnect ? ConnectResult::Pending : ConnectResult::Connected;
  }
  ConnectResult pollTcp() override {
    ++calls; ++polls;
    if (pendingConnect) { --pendingConnect; return ConnectResult::Pending; }
    return tcp ? ConnectResult::Connected : ConnectResult::Failed;
  }
  int send(const uint8_t* bytes, size_t size) override {
    ++calls; clock += ioAdvance;
    if (sendResult > 0) sentBytes.append(reinterpret_cast<const char*>(bytes), std::min(size, sendChunk));
    return sendResult > 0 ? int(std::min(size, sendChunk)) : sendResult;
  }
  int receive(uint8_t* out, size_t size) override {
    ++calls; clock += ioAdvance;
    if (receiveError) return receiveError;
    if (offset == response.size()) return eof ? 0 : -1;
    const size_t n = std::min(size, response.size() - offset);
    std::memcpy(out, response.data() + offset, n); offset += n; return int(n);
  }
  bool finishTcp() override { ++calls; ++closes; return closeOK; }
  size_t request(char* out, size_t, const char* accepted) override {
    ++calls; sentIdentity = accepted; std::memset(out, 'x', 8); return 8;
  }
  bool hashTag(const uint8_t* bytes, size_t n, char (&out)[67]) override {
    ++calls; clock += hashAdvance; assert(n == kFrameBytes);
    for (size_t i = 0; i < n; ++i) assert(bytes[i] == 0xA5);
    std::memcpy(out, identity.c_str(), 67); return crypto;
  }
  bool display(const uint8_t* bytes, size_t n) override {
    ++calls; ++displays; assert(closes == connects); assert(n == kFrameBytes);
    for (size_t i = 0; i < n; ++i) assert(bytes[i] == 0xA5);
    return accept;
  }
  ReportResult beginReport(ReportStage stage, const char* frame) override {
    ++calls; reports.push_back({stage, frame, displays}); return reportResult;
  }
  ReportResult pollReport() override { ++calls; return reportResult; }
  FirmwareCheckResult checkResult = FirmwareCheckResult::NoUpdate;
  FirmwareUpdateResult updateResult = FirmwareUpdateResult::ReadyToReboot;
  unsigned firmwareChecks = 0, firmwareUpdates = 0, reboots = 0;
  const char* firmwareVersion() override { return "round2-r6-1"; }
  FirmwareCheckResult beginFirmwareCheck() override { ++firmwareChecks; return checkResult; }
  FirmwareCheckResult pollFirmwareCheck() override { ++calls; return checkResult; }
  FirmwareUpdateResult beginFirmwareUpdate() override { ++firmwareUpdates; return updateResult; }
  FirmwareUpdateResult pollFirmwareUpdate() override { ++calls; return updateResult; }
  void rebootForFirmware() override { ++reboots; }
};
void settle(Machine& m, Fake& f) {
  for (unsigned i = 0; i < 20000; ++i) {
    m.tick();
    if (m.state() == State::PollWait || m.state() == State::FailureWait || m.state() == State::FaultStop) return;
    ++f.clock;
  }
  assert(false);
}
void next(Machine& m, Fake& f) { f.clock += 60000; m.tick(); settle(m, f); }
void parserCases() {
  assert(parse(head() + "\r\n"));
  assert(parse(head(304) + "\r\n", tag.c_str()));
  assert(!parse(head(304) + "\r\n"));
  assert(!parse(head(304) + "Content-Length: 0\r\n\r\n", tag.c_str()));
  for (const auto& h : {"Content-Length: 15000", "ETag: "})
    assert(!parse(head() + h + "\r\n\r\n"));
  for (const auto& h : {"Transfer-Encoding: chunked", "Content-Encoding: identity", " bad: x", "bad : x"})
    assert(!parse(head() + h + "\r\n\r\n"));
  assert(!parse(head(200, "W/" + tag) + "\r\n"));
  assert(!parse(head(200, "\"" + std::string(64, 'A') + "\"") + "\r\n"));
  assert(!parse(head() + "X: " + std::string(510, 'x') + "\r\n\r\n"));
  std::string longHeaders = head();
  for (unsigned i = 0; i < 20; ++i) longHeaders += "X: " + std::string(250, 'x') + "\r\n";
  assert(!parse(longHeaders + "\r\n"));
  assert(!parse("HTTP/1.1 302 Found\r\n\r\n"));
  assert(!parse(head() + "X: bare\n\r\n"));
  assert(expired(5, 0xFFFFFFFEu, 7));
  assert(!expired(5, 0xFFFFFFFEu, 8));
}
void remediationCases() {
  {
    Fake f; f.initOK = false; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(m.state() == State::FailureWait && m.failure() == Failure::WifiInitFailure);
    assert(f.initializations == 1 && f.starts == 0 && f.connects == 0);
    // Even an already recovered link must not bypass failed initialization.
    f.clock += 59999; m.tick(); assert(f.initializations == 1 && f.connects == 0);
    ++f.clock; m.tick(); assert(m.state() == State::WifiInit);
    f.initOK = true; settle(m, f);
    assert(f.initializations == 2 && f.displays == 1);
  }
  {
    Fake f; f.wifi = false; f.associationBad = true;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60); settle(m, f);
    assert(m.failure() == Failure::WifiAssociationFailure && f.cancellations == 1);
    f.wifi = true; f.associationBad = false;
    f.clock += 59999; m.tick(); assert(f.connects == 0 && f.displays == 0);
    ++f.clock; m.tick(); settle(m, f); assert(f.displays == 1);
  }
  for (bool rollover : {false, true}) {
    Fake f; f.pendingConnect = 100000;
    if (rollover) f.clock = 0xFFFFF800u;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60); settle(m, f);
    assert(m.state() == State::FailureWait && m.failure() == Failure::TcpConnectFailure);
    assert(f.connects == 1 && f.closes == 1 && f.displays == 0);
  }
  for (int kind = 0; kind < 6; ++kind) {
    Fake f; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    if (kind == 0) f.tcp = false;
    if (kind == 1) f.sendResult = kIoFailed;
    if (kind == 2) f.sendResult = kIoPending;
    if (kind == 3) f.receiveError = kIoFailed;
    if (kind == 4) f.receiveError = kIoPending;
    if (kind == 5) f.response = "HTTP/1.1 503 Unavailable\r\n\r\n";
    settle(m, f);
    assert(m.state() == State::FailureWait && f.closes == 1 && f.displays == 0);
    next(m, f); assert(f.closes == 2 && f.connects == 2 && f.displays == 0);
  }
  {
    Fake f; f.pendingConnect = 1; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    while (f.connects == 0) m.tick();
    f.wifi = false; m.tick();
    assert(m.state() == State::FailureWait && m.failure() == Failure::NetworkDisconnected);
    assert(f.closes == 1 && f.displays == 0);
  }
  for (bool malformed : {false, true}) {
    Fake f; f.closeOK = false;
    if (malformed) f.response = "bad\r\n";
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60); settle(m, f);
    assert(m.state() == State::FaultStop && m.failure() == Failure::InternalInvariantFailure);
    assert(f.closes == 1 && f.displays == 0 && !m.acceptedIdentity()[0]);
    const auto calls = f.calls;
    f.clock += 86400000; for (unsigned i = 0; i < 100; ++i) m.tick();
    assert(f.calls == calls);
  }
  {
    Fake f; f.sendChunk = 1; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f); assert(m.state() == State::PollWait && f.displays == 1 && f.closes == 1);
  }
  {
    Fake f; f.hashAdvance = 15000; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(m.failure() == Failure::FrameValidationFailure && f.displays == 0 && f.closes == 1);
  }
  {
    Fake f; f.pendingConnect = 100; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    while (!f.connects) m.tick();
    f.clock += 3000; m.tick();
    assert(f.polls == 0 && f.closes == 1 && m.failure() == Failure::TcpConnectFailure);
  }
}
void observabilityCases() {
  {
    Fake f; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(f.reports.size() == 2);
    assert(f.reports[0].stage == ReportStage::FrameAccepted && f.reports[0].identity == tag);
    assert(f.reports[0].displays == 0);
    assert(f.reports[1].stage == ReportStage::RefreshFlowComplete && f.reports[1].identity == tag);
    assert(f.reports[1].displays == 1);
    f.response = head(304) + "\r\n";
    next(m, f);
    assert(f.displays == 1 && f.reports.size() == 3);
    assert(f.reports.back().stage == ReportStage::Communication && m.acceptedIdentity() == tag);
    for (int rejected = 0; rejected < 4; ++rejected) {
      const auto size = f.reports.size();
      f.identity = "\"" + std::string(64, 'b') + "\"";
      f.response = head(200, f.identity) + "\r\n" + std::string(kFrameBytes, char(0xA5));
      if (rejected == 0) f.response.pop_back();
      if (rejected == 1) f.identity = tag; // SHA does not match response ETag.
      if (rejected == 2) f.response.replace(f.response.find(kFormat), std::strlen(kFormat), "invalid-format");
      if (rejected == 3) f.response += 'x';
      next(m, f);
      assert(m.state() == State::FailureWait && m.acceptedIdentity() == tag);
      assert(f.displays == 1 && f.reports.size() == size);
    }
  }
  for (auto result : {ReportResult::Finished, ReportResult::Failed}) {
    Fake f; f.reportResult = result; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(m.state() == State::PollWait && f.displays == 1 && m.acceptedIdentity() == tag);
  }
  {
    Fake f; f.accept = false; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(m.state() == State::FaultStop && f.reports.size() == 1);
    assert(f.reports[0].stage == ReportStage::FrameAccepted && !m.acceptedIdentity()[0]);
  }
  {
    Fake f; f.reportResult = ReportResult::InvariantFailure;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60); settle(m, f);
    assert(m.state() == State::FaultStop && f.displays == 0);
  }
}
void reporterCases() {
  const ResolvedHost host{{192, 168, 1, 2}, 8000, HostSource::CONFIGURED_FALLBACK};
  for (auto stage : {ReportStage::Communication, ReportStage::FrameAccepted, ReportStage::RefreshFlowComplete}) {
    Fake f; f.sendChunk = 1; f.response = "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n";
    DeviceReporter reporter(f, host);
    auto result = reporter.begin(stage, tag.c_str());
    for (unsigned i = 0; i < 2000 && result == ReportResult::Pending; ++i) { ++f.clock; result = reporter.poll(); }
    assert(result == ReportResult::Finished && f.closes == 1 && f.displays == 0);
    assert(f.sentBytes.find("POST /api/panels/progress/device-report HTTP/1.1\r\n") == 0);
    assert(f.sentBytes.find("\"frame_version\":\"" + std::string(64, 'a') + "\"") != std::string::npos);
    assert(f.sentBytes.find(kFirmwareVersion) != std::string::npos);
    assert((f.sentBytes.find("\"refresh_stage\":null") != std::string::npos) == (stage == ReportStage::Communication));
  }
  for (bool cleanupFailure : {false, true}) {
    Fake f; f.pendingConnect = 100000; f.closeOK = !cleanupFailure;
    DeviceReporter reporter(f, host);
    assert(reporter.begin(ReportStage::FrameAccepted, tag.c_str()) == ReportResult::Pending);
    f.clock += 3000;
    assert(reporter.poll() == (cleanupFailure ? ReportResult::InvariantFailure : ReportResult::Failed));
    assert(f.connects == 1 && f.closes == 1 && f.displays == 0); // No report retry.
  }
}
void discoveryCases() {
  for (bool discovered : {false, true}) {
    Fake f; f.discoveryAvailable = discovered; f.resolveAdvance = 1000;
    f.resolveHost();
    assert(f.displays == 0 && f.connects == 0 && f.reports.empty());
    const auto expected = discovered ? f.discovered : f.configured;
    assert(f.endpoint.source == expected.source && f.endpoint.port == expected.port);
    for (unsigned i = 0; i < 4; ++i) assert(f.endpoint.address[i] == expected.address[i]);
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60); settle(m, f);
    assert(m.state() == State::PollWait && f.displays == 1 && f.connects == 1);
    assert(f.connections.back().port == expected.port && f.connections.back().source == expected.source);
    // The same HTTP machine accepts 200, then preserves LKG on 304 or bad frames.
    f.discoveryAvailable = !discovered;
    f.response = head(304) + "\r\n"; next(m, f);
    assert(m.state() == State::PollWait && f.displays == 1 && f.sentIdentity == tag);
    assert(f.reports.back().stage == ReportStage::Communication);
    assert(f.connections.back().source != expected.source);
    for (int rejected = 0; rejected < 4; ++rejected) {
      f.discoveryAvailable = discovered;
      f.identity = "\"" + std::string(64, 'b') + "\"";
      f.response = head(200, f.identity) + "\r\n" + std::string(kFrameBytes, char(0xA5));
      if (rejected == 0) f.response.pop_back();
      if (rejected == 1) f.identity = tag;
      if (rejected == 2) f.response.replace(f.response.find(kFormat), std::strlen(kFormat), "bad-format");
      if (rejected == 3) f.response += 'x';
      const auto reports = f.reports.size(); next(m, f);
      assert(m.state() == State::FailureWait && f.displays == 1 && m.acceptedIdentity() == tag);
      assert(f.reports.size() == reports && f.connections.back().port == expected.port);
    }
    // Reports borrow the selected endpoint, including a changed advertised port.
    Fake reportPort; reportPort.response = "HTTP/1.1 200 OK\r\n\r\n";
    reportPort.endpoint = expected;
    DeviceReporter reporter(reportPort, reportPort.endpoint);
    auto result = reporter.begin(ReportStage::FrameAccepted, tag.c_str());
    for (unsigned i = 0; i < 2000 && result == ReportResult::Pending; ++i) { ++reportPort.clock; result = reporter.poll(); }
    assert(result == ReportResult::Finished);
    assert(reportPort.connections.back().port == expected.port);
    const auto address = discovered ? "192.168.1.23:8765" : "192.168.1.2:8000";
    assert(reportPort.sentBytes.find(std::string("Host: ") + address + "\r\n") != std::string::npos);
  }
  Fake f;
  for (int invalid = 0; invalid < 4; ++invalid) {
    auto candidate = f.discovered;
    if (invalid == 0) candidate.port = 0;
    if (invalid == 1) candidate.port = 65536;
    if (invalid == 2) candidate.address[0] = 224;
    if (invalid == 3) candidate.address[3] = 256;
    const auto endpoint = resolveHost(&candidate, f.configured);
    assert(endpoint.source == HostSource::CONFIGURED_FALLBACK && endpoint.port == 8000);
    assert(endpoint.address[3] == 2);
  }
}
void physicalButtonCases() {
  for (bool associationFails : {false, true}) {
    Fake f; f.wifi = !associationFails; f.associationBad = associationFails;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60); ProvisioningButton button;
    for (unsigned i = 0; i < 10 && m.state() != State::WifiConnect; ++i) m.tick();
    assert(m.state() == State::WifiConnect);
    button.poll(false, 0, m); button.poll(false, 30, m);
    // User gesture during an active connection: defer, with no Port call.
    button.poll(true, 100, m); button.poll(true, 130, m); button.poll(true, 2130, m);
    assert(f.provisioningEntries == 0 && m.state() == State::WifiConnect);
    settle(m, f);
    assert(m.state() == (associationFails ? State::FailureWait : State::PollWait));
    assert(button.poll(true, 2131, m) && f.provisioningEntries == 1);
    button.poll(true, 9000, m); assert(f.provisioningEntries == 1);
    f.wifi = true; f.associationBad = false; f.provisioningReady = true;
    m.tick(); assert(m.state() == State::HostResolve);
  }
}
void provisioningHandoffCases() {
  {
    Fake f; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    assert(!m.requestProvisioning()); // boot is not an initialized idle boundary
    settle(m, f);
    assert(f.provisioningEntries == 0 && f.displays == 1);
    const auto connects = f.connects;
    assert(m.requestProvisioning() && m.state() == State::Provisioning);
    m.tick();
    assert(m.state() == State::Provisioning && f.connects == connects && f.displays == 1);
    f.provisioningReady = true; m.tick();
    assert(m.state() == State::HostResolve);
    settle(m, f);
    assert(m.state() == State::PollWait && f.displays == 1 && m.acceptedIdentity() == tag);
    // Existing same-frame 200 and 304 semantics still use the original machine.
    f.response = head(304) + "\r\n"; next(m, f);
    assert(f.displays == 1 && f.reports.back().stage == ReportStage::Communication);
  }
  {
    Fake f; f.wifi = false; f.associationBad = true;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60); settle(m, f);
    assert(m.state() == State::FailureWait && f.provisioningEntries == 0);
    assert(m.requestProvisioning());
    f.provisioningReady = true; f.wifi = true; f.associationBad = false;
    m.tick(); assert(m.state() == State::HostResolve);
    settle(m, f); assert(m.state() == State::PollWait && f.displays == 1);
  }
  {
    Fake f; f.accept = false; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60); settle(m, f);
    assert(m.state() == State::FaultStop && !m.requestProvisioning() && f.provisioningEntries == 0);
  }
}
void firmwareCases() {
  {
    Fake f; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(f.firmwareChecks == 1 && f.firmwareUpdates == 0 && f.reboots == 0);
    assert(f.displays == 1 && m.state() == State::PollWait);
  }
  {
    Fake f; f.checkResult = FirmwareCheckResult::Failed;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(f.displays == 1 && m.failure() == Failure::None);
  }
  {
    Fake f; f.checkResult = FirmwareCheckResult::UpdateAvailable;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(f.firmwareUpdates == 1 && f.reboots == 1 && f.displays == 0);
    assert(m.state() == State::FaultStop);
    const auto calls = f.calls;
    f.clock += 60000; for (int i = 0; i < 10; ++i) m.tick();
    assert(f.calls == calls);
  }
  {
    Fake f; f.checkResult = FirmwareCheckResult::UpdateAvailable;
    f.updateResult = FirmwareUpdateResult::Failed;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(m.state() == State::FailureWait);
    assert(m.failure() == Failure::FirmwareUpdateFailure);
    assert(f.firmwareUpdates == 1 && f.reboots == 0 && f.displays == 0);
    // Pre-GET exception: the fake keeps offering the image on every manifest, which
    // models a failed attempt that never consumed the Host arm (partition/begin or
    // TCP connect failure). The per-boot latch, not a disarmed Host, is what stops a
    // second attempt, and the ordinary frame poll resumes with the old identity.
    next(m, f);
    assert(f.firmwareUpdates == 1);   // No second download; the target slot is not erased again.
    assert(f.firmwareChecks == 2);    // The manifest is still checked before each poll.
    assert(f.displays == 1 && m.state() == State::PollWait);
    assert(m.failure() == Failure::None && m.acceptedIdentity() == tag);
    // The latch holds for the rest of the boot.
    next(m, f);
    assert(f.firmwareUpdates == 1 && f.displays == 1 && m.state() == State::PollWait);
  }
  {
    Fake f; f.checkResult = FirmwareCheckResult::InvariantFailure;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(m.state() == State::FaultStop && f.displays == 0);
  }
  {
    Fake f; f.checkResult = FirmwareCheckResult::UpdateAvailable;
    f.updateResult = FirmwareUpdateResult::InvariantFailure;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f);
    assert(m.state() == State::FaultStop && f.reboots == 0 && f.displays == 0);
  }
}
int main() {
  firmwareCases();
  physicalButtonCases();
  provisioningHandoffCases();
  parserCases();
  remediationCases();
  observabilityCases();
  reporterCases();
  discoveryCases();
  {
    Fake f; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f); assert(m.state() == State::PollWait && f.displays == 1);
    assert(m.acceptedIdentity() == tag); assert(f.sentIdentity.empty());
    next(m, f); assert(f.displays == 1 && f.sentIdentity == tag); // same 200
    f.response = head(304) + "\r\n";
    next(m, f); assert(f.displays == 1 && m.state() == State::PollWait);
    f.identity = "\"" + std::string(64, 'b') + "\"";
    f.response = head(200, f.identity) + "\r\n" + std::string(kFrameBytes, char(0xA5));
    next(m, f); assert(f.displays == 2 && m.acceptedIdentity() == f.identity);
    f.accept = false; f.identity = tag;
    f.response = head() + "\r\n" + std::string(kFrameBytes, char(0xA5));
    const std::string old = m.acceptedIdentity();
    next(m, f); assert(m.state() == State::FaultStop && m.acceptedIdentity() == old);
    const auto calls = f.calls;
    f.clock += 86400000; for (int i = 0; i < 20; ++i) m.tick();
    assert(f.calls == calls); // terminal means no future port calls, including clock
  }
  for (int kind = 0; kind < 7; ++kind) {
    Fake f; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    if (kind == 0) f.response.pop_back();
    if (kind == 1) f.response += 'x';
    if (kind == 2) f.eof = false;
    if (kind == 3) f.crypto = false;
    if (kind == 4) f.identity = "\"" + std::string(64, 'b') + "\"";
    if (kind == 5) f.response = head(304) + "\r\n";
    if (kind == 6) f.ioAdvance = 20; // idle progresses but absolute header deadline wins
    settle(m, f);
    assert(m.state() == State::FailureWait && f.displays == 0 && !m.acceptedIdentity()[0]);
    assert(f.closes == 1);
  }
  {
    Fake f; f.configOK = false; uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f); assert(m.state() == State::FaultStop && f.starts == 0 && f.initializations == 0);
    assert(m.failure() == Failure::ConfigInvalid);
  }
  {
    Fake f; f.wifi = false; f.clock = 0xFFFFF000u;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f); assert(m.state() == State::FailureWait && f.cancellations == 1 && f.connects == 0);
  }
}
