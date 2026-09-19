// STEP017E host-run harness. Compile with C++17; no Arduino, socket or hardware.
#include "../../hardware/gdey042t81_esp32/src/network_progress/machine.h"
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
  uint32_t clock = 0, ioAdvance = 0;
  bool configOK = true, wifi = true, tcp = true, eof = true, crypto = true, accept = true;
  unsigned starts = 0, connects = 0, closes = 0, displays = 0, cancellations = 0, calls = 0;
  size_t offset = 0;
  std::string response = head() + "\r\n" + std::string(kFrameBytes, char(0xA5));
  std::string identity = tag, sentIdentity;
  uint32_t now() override { ++calls; return clock; }
  bool configure() override { ++calls; return configOK; }
  bool connected() override { ++calls; return wifi; }
  void beginWifi() override { ++calls; ++starts; }
  void cancelWifi() override { ++calls; ++cancellations; }
  bool connectTcp() override { ++calls; ++connects; offset = 0; return tcp; }
  int send(const uint8_t*, size_t size) override { ++calls; clock += ioAdvance; return int(size); }
  int receive(uint8_t* out, size_t size) override {
    ++calls; clock += ioAdvance;
    if (offset == response.size()) return eof ? 0 : -1;
    const size_t n = std::min(size, response.size() - offset);
    std::memcpy(out, response.data() + offset, n); offset += n; return int(n);
  }
  void close() override { ++calls; ++closes; }
  size_t request(char* out, size_t, const char* accepted) override {
    ++calls; sentIdentity = accepted; out[0] = 'x'; return 1;
  }
  bool hashTag(const uint8_t* bytes, size_t n, char (&out)[67]) override {
    ++calls; assert(n == kFrameBytes);
    for (size_t i = 0; i < n; ++i) assert(bytes[i] == 0xA5);
    std::memcpy(out, identity.c_str(), 67); return crypto;
  }
  bool display(const uint8_t* bytes, size_t n) override {
    ++calls; ++displays; assert(closes == connects); assert(n == kFrameBytes);
    for (size_t i = 0; i < n; ++i) assert(bytes[i] == 0xA5);
    return accept;
  }
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
int main() {
  parserCases();
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
    settle(m, f); assert(m.state() == State::FaultStop && f.starts == 0);
  }
  {
    Fake f; f.wifi = false; f.clock = 0xFFFFF000u;
    uint8_t frame[kFrameBytes]{}; Machine m(f, frame, 60);
    settle(m, f); assert(m.state() == State::FailureWait && f.cancellations == 1 && f.connects == 0);
  }
}
