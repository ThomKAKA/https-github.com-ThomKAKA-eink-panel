#ifdef EINK_NETWORK_PROGRESS
#include <Arduino.h>
#include <WiFi.h>
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

// Fixed lwIP APIs only; all descriptors here are borrowed from SocketOwner.
struct NativeSockets {
  int openSocket() { return lwip_socket(AF_INET, SOCK_STREAM, IPPROTO_TCP); }
  bool setNonblocking(int fd) {
    const int flags = lwip_fcntl(fd, F_GETFL, 0);
    return flags >= 0 && lwip_fcntl(fd, F_SETFL, flags | O_NONBLOCK) == 0;
  }
  SocketResult startConnect(int fd) {
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(uint16_t(kPort));
    address.sin_addr.s_addr = htonl((uint32_t(kHost[0]) << 24) |
      (uint32_t(kHost[1]) << 16) | (uint32_t(kHost[2]) << 8) | uint32_t(kHost[3]));
    if (lwip_connect(fd, reinterpret_cast<const sockaddr*>(&address), sizeof(address)) == 0)
      return SocketResult::Ok;
    return errno == EINPROGRESS ? SocketResult::Pending : SocketResult::Failed;
  }
  SocketResult checkReady(int fd) {
    // Respect the fixed SDK's socket offset and fd_set range before FD_SET.
    if (fd < LWIP_SOCKET_OFFSET || fd >= LWIP_SELECT_MAXNFDS) return SocketResult::Failed;
    fd_set writable, exceptional;
    FD_ZERO(&writable); FD_ZERO(&exceptional);
    FD_SET(fd, &writable); FD_SET(fd, &exceptional);
    timeval noWait{};
    const int n = lwip_select(fd + 1, nullptr, &writable, &exceptional, &noWait);
    if (n < 0) return transient() ? SocketResult::Pending : SocketResult::Failed;
    return n > 0 && (FD_ISSET(fd, &writable) || FD_ISSET(fd, &exceptional))
      ? SocketResult::Ok : SocketResult::Pending;
  }
  SocketResult checkError(int fd) {
    int error = 0; socklen_t size = sizeof(error);
    if (lwip_getsockopt(fd, SOL_SOCKET, SO_ERROR, &error, &size) != 0)
      return transient() ? SocketResult::Pending : SocketResult::Failed;
    if (size != sizeof(error)) return SocketResult::Failed;
    if (error == 0) return SocketResult::Ok;
    return error == EINPROGRESS ? SocketResult::Pending : SocketResult::Failed;
  }
  int writeBytes(int fd, const uint8_t* bytes, size_t size) {
    return ioResult(lwip_send(fd, bytes, size, MSG_DONTWAIT));
  }
  int readBytes(int fd, uint8_t* bytes, size_t size) {
    return ioResult(lwip_recv(fd, bytes, size, MSG_DONTWAIT));
  }
  bool releaseSocket(int fd) { return lwip_close(fd) == 0; }
 private:
  static bool transient() { return errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR; }
  static int ioResult(int n) { return n >= 0 ? n : transient() ? kIoPending : kIoFailed; }
};

class EspPort final : public Port {
 public:
  uint32_t now() override { return millis(); }
  ConfigResult validateConfiguration() override {
    return validConfig() ? ConfigResult::Valid : ConfigResult::Invalid;
  }
  WifiInitResult initializeWifi() override {
    WiFi.persistent(false);
    // Disables ordinary auto-retry, not the framework's first_connect branch.
    if (!WiFi.setAutoReconnect(false) || !WiFi.mode(WIFI_STA)) return WifiInitResult::Failed;
    return WifiInitResult::Ready;
  }
  bool connected() override { return WiFi.status() == WL_CONNECTED; }
  void beginWifi() override { WiFi.begin(kSsid, kPassword); }
  void cancelWifi() override { WiFi.disconnect(false, false); }
  bool associationFailed() override {
    const auto status = WiFi.status();
    return status == WL_CONNECT_FAILED || status == WL_NO_SSID_AVAIL;
  }
  ConnectResult beginTcp() override { return socket_.begin(); }
  ConnectResult pollTcp() override { return socket_.poll(); }
  int send(const uint8_t* bytes, size_t size) override {
    return socket_.write(bytes, size);
  }
  int receive(uint8_t* bytes, size_t size) override {
    return socket_.read(bytes, size);
  }
  bool finishTcp() override { return socket_.finish(); }
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
  NativeSockets sockets_;
  SocketOwner<NativeSockets> socket_{sockets_};
};
EspPort port;
Machine machine(port, frame, kPollSeconds);
}  // namespace

void setup() { Serial.begin(115200); }
void loop() {
  const State previous = machine.state();
  machine.tick();
  if (machine.state() != previous)
    Serial.printf("NETWORK_STATE=%u HTTP_STATUS=%d FAILURE=%u\n",
      unsigned(machine.state()), machine.httpStatus(), unsigned(machine.failure()));
  delay(1);  // FAULT_STOP performs no application network or EPD operations.
}
#endif
