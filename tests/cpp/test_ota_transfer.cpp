#include "../../hardware/gdey042t81_esp32/src/network_progress/ota.h"
#include <cassert>
#include <cstring>
#include <string>
using namespace eink::network_progress;

const std::string SHA(64, 'a');
const std::string BODY(33, char(0xA5));

struct FakePort final : Port {
  uint32_t clock = 0;
  std::string incoming;
  size_t offset = 0;
  bool connectedNow = true;
  unsigned connects = 0, closes = 0;
  std::string sent;
  ResolvedHost host{{192, 168, 1, 2}, 8000, HostSource::CONFIGURED_FALLBACK};
  uint32_t now() override { return clock; }
  ConfigResult validateConfiguration() override { return ConfigResult::Valid; }
  WifiInitResult initializeWifi() override { return WifiInitResult::Ready; }
  bool connected() override { return connectedNow; }
  bool associationFailed() override { return false; }
  void beginWifi() override {}
  void cancelWifi() override {}
  bool beginProvisioning() override { return false; }
  bool pollProvisioning() override { return false; }
  void resolveHost() override {}
  ConnectResult beginTcp() override { ++connects; offset = 0; return ConnectResult::Connected; }
  ConnectResult pollTcp() override { return ConnectResult::Connected; }
  int send(const uint8_t* bytes, size_t size) override {
    sent.append(reinterpret_cast<const char*>(bytes), size); return int(size);
  }
  int receive(uint8_t* out, size_t size) override {
    if (offset == incoming.size()) return 0;
    const size_t n = std::min(size, incoming.size() - offset);
    std::memcpy(out, incoming.data() + offset, n); offset += n; return int(n);
  }
  bool finishTcp() override { ++closes; return true; }
  size_t request(char*, size_t, const char*) override { return 0; }
  bool hashTag(const uint8_t*, size_t, char (&)[67]) override { return false; }
  bool display(const uint8_t*, size_t) override { return false; }
  ReportResult beginReport(ReportStage, const char*) override { return ReportResult::Failed; }
  ReportResult pollReport() override { return ReportResult::Failed; }
};

struct FakeSink final : OtaSink {
  bool begun = false, finished = false, activated = false, aborted = false;
  std::string data;
  bool begin(size_t) override { begun = true; return true; }
  bool write(const uint8_t* bytes, size_t size) override {
    data.append(reinterpret_cast<const char*>(bytes), size); return true;
  }
  bool finish(const char* expected) override {
    finished = std::strcmp(expected, SHA.c_str()) == 0; return finished;
  }
  bool activate() override { activated = true; return true; }
  void reboot() override {}
  void abort() override { aborted = true; }
};

std::string manifestHead() {
  const std::string body = "{\"armed\":true,\"version\":\"round2-r6-2\",\"size\":33,\"sha256\":\"" + SHA + "\"}";
  return "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " +
    std::to_string(body.size()) + "\r\nConnection: close\r\n\r\n" + body;
}

std::string imageHead() {
  return "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: 33\r\n"
    "X-Firmware-Version: round2-r6-2\r\nX-Firmware-SHA256: " + SHA +
    "\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n" + BODY;
}

int main() {
  FakePort port; FakeSink sink; OtaUpdater updater(port, port.host, sink);
  port.incoming = manifestHead();
  auto check = updater.beginCheck();
  for (unsigned i = 0; i < 100 && check == FirmwareCheckResult::Pending; ++i) {
    ++port.clock; check = updater.pollCheck();
  }
  assert(check == FirmwareCheckResult::UpdateAvailable);
  assert(port.closes == 1);

  port.incoming = imageHead();
  auto update = updater.beginUpdate();
  for (unsigned i = 0; i < 100 && update == FirmwareUpdateResult::Pending; ++i) {
    ++port.clock; update = updater.pollUpdate();
  }
  assert(update == FirmwareUpdateResult::ReadyToReboot);
  assert(sink.begun && sink.finished && sink.activated && !sink.aborted);
  assert(sink.data == BODY);
  assert(port.closes == 2);
  for (int kind = 0; kind < 3; ++kind) {
    FakePort badPort; FakeSink badSink;
    OtaUpdater badUpdater(badPort, badPort.host, badSink);
    badPort.incoming = manifestHead();
    auto checked = badUpdater.beginCheck();
    for (unsigned i = 0; i < 100 && checked == FirmwareCheckResult::Pending; ++i) {
      ++badPort.clock; checked = badUpdater.pollCheck();
    }
    assert(checked == FirmwareCheckResult::UpdateAvailable);

    std::string image = imageHead();
    if (kind == 0) image.replace(image.find("X-Firmware-SHA256: "), 19, "X-Firmware-SHA256: b");
    if (kind == 1) image.replace(image.find("Content-Length: 33"), 17, "Content-Length: 34");
    if (kind == 2) image.resize(image.size() - 1);
    badPort.incoming = image;
    auto updated = badUpdater.beginUpdate();
    for (unsigned i = 0; i < 100 && updated == FirmwareUpdateResult::Pending; ++i) {
      ++badPort.clock; updated = badUpdater.pollUpdate();
    }
    assert(updated == FirmwareUpdateResult::Failed);
    assert(!badSink.activated && !badSink.finished);
    assert(badSink.aborted);
    assert(badPort.closes == 2);
  }
  return 0;
}
