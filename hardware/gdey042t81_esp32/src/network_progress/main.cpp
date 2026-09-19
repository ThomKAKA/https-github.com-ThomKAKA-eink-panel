#ifdef EINK_NETWORK_PROGRESS
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <lwip/sockets.h>
#include <mbedtls/sha256.h>
#include <cerrno>
#include <cstdio>
#include "machine.h"
#include "config.h"
#include "../h1/atomic_display.h"

namespace {
using namespace eink::network_progress;
static uint8_t frame[kFrameBytes];  // Single network/display frame, never on stack.

class EspPort final : public Port {
 public:
  uint32_t now() override { return millis(); }
  bool configure() override {
    if (!validConfig()) return false;
    WiFi.persistent(false);
    if (!WiFi.setAutoReconnect(false) || !WiFi.mode(WIFI_STA)) return false;
    return true;
  }
  bool connected() override { return WiFi.status() == WL_CONNECTED; }
  void beginWifi() override { WiFi.begin(kSsid, kPassword); }
  void cancelWifi() override { WiFi.disconnect(false, false); }
  bool connectTcp() override {
    return client_.connect(IPAddress(kHost[0], kHost[1], kHost[2], kHost[3]), uint16_t(kPort), 3000) == 1;
  }
  int send(const uint8_t* bytes, size_t size) override {
    return ioResult(::send(client_.fd(), bytes, size, MSG_DONTWAIT));
  }
  int receive(uint8_t* bytes, size_t size) override {
    return ioResult(::recv(client_.fd(), bytes, size, MSG_DONTWAIT));
  }
  void close() override { client_.stop(); }
  size_t request(char* out, size_t capacity, const char* accepted) override {
    const int n = std::snprintf(out, capacity,
      "GET %s HTTP/1.1\r\nHost: %u.%u.%u.%u:%u\r\nConnection: close\r\n"
      "Accept: application/octet-stream\r\nAccept-Encoding: identity\r\n%s%s%s\r\n",
      kEndpoint, kHost[0], kHost[1], kHost[2], kHost[3], kPort,
      accepted[0] ? "If-None-Match: " : "", accepted, accepted[0] ? "\r\n" : "");
    return n > 0 && size_t(n) < capacity ? size_t(n) : 0;
  }
  bool hashTag(const uint8_t* bytes, size_t size, char (&out)[67]) override {
    unsigned char digest[32];
    if (mbedtls_sha256_ret(bytes, size, digest, 0)) return false;
    constexpr char hex[] = "0123456789abcdef";
    out[0] = '"';
    for (unsigned i = 0; i < 32; ++i) { out[1 + i * 2] = hex[digest[i] >> 4]; out[2 + i * 2] = hex[digest[i] & 15]; }
    out[65] = '"'; out[66] = 0; return true;
  }
  bool display(const uint8_t* bytes, size_t size) override {
    if (size != eink::h1::kBytes) return false;
    pinMode(EPD_BUSY, INPUT);
    if (digitalRead(EPD_BUSY) == HIGH) return false;
    eink::h1::H1SafeGDEY042T81 session(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY);
    SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
    if (!session.coldInit(SPI) || !session.prepareColdStartFullFrame(bytes, size, 0, 0, 400, 300)) return false;
    if (digitalRead(EPD_BUSY) == HIGH) return false;
    const uint32_t start = micros();
    const bool invoked = session.refreshOnce();
    const uint32_t elapsed = uint32_t(micros() - start);
    const bool busy = digitalRead(EPD_BUSY) == HIGH;
    // No EPD operation, cleanup or retry follows this refresh, including destruction.
    const bool accepted = invoked && !eink::h1::timedOutOrUnknown(elapsed, busy);
    Serial.println(accepted ? "NETWORK_SOFTWARE_RETURN_CONDITIONS_MET_NOT_PHYSICAL_PASS" : "NETWORK_DISPLAY_TIMEOUT_OR_UNKNOWN");
    return accepted;
  }
 private:
  static int ioResult(int n) {
    if (n >= 0) return n;
    return errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR ? -1 : -2;
  }
  WiFiClient client_;  // Sole fd owner; never mix buffered reads or close(fd).
};
EspPort port;
Machine machine(port, frame, kPollSeconds);
}  // namespace

void setup() { Serial.begin(115200); }
void loop() {
  const State previous = machine.state();
  machine.tick();
  if (machine.state() != previous)
    Serial.printf("NETWORK_STATE=%u HTTP_STATUS=%d\n", unsigned(machine.state()), machine.httpStatus());
  delay(1);  // FAULT_STOP performs no application network or EPD operations.
}
#endif
