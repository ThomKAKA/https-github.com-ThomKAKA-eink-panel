#pragma once
#include "protocol.h"

namespace eink::network_progress {
enum class State {
  Boot, ConfigValidate, WifiConnect, HttpConnect, RequestSend, ResponseValidate, FrameReceive,
  ResponseEnd, FrameValidate, DisplayPending, DisplayUpdate, PollWait,
  FailureWait, FaultStop
};

// Port owns the socket. -1 = no progress (EAGAIN/EINTR), -2 = error, 0 = EOF.
// No application task other than Machine may use Port or the frame buffer.
class Port {
 public:
  virtual ~Port() = default;
  virtual uint32_t now() = 0;
  virtual bool configure() = 0;
  virtual bool connected() = 0;
  virtual void beginWifi() = 0;
  virtual void cancelWifi() = 0;
  virtual bool connectTcp() = 0;
  virtual int send(const uint8_t*, size_t) = 0;
  virtual int receive(uint8_t*, size_t) = 0;
  virtual void close() = 0;
  virtual size_t request(char*, size_t, const char*) = 0;
  virtual bool hashTag(const uint8_t*, size_t, char (&)[67]) = 0;
  virtual bool display(const uint8_t*, size_t) = 0;
};

class Machine {
 public:
  Machine(Port& port, uint8_t (&frame)[kFrameBytes], uint32_t pollSeconds)
      : port_(port), frame_(frame), pollSeconds_(pollSeconds) {}
  State state() const { return state_; }
  const char* acceptedIdentity() const { return accepted_; }
  const char* attemptIdentity() const { return attempt_; }
  int httpStatus() const { return headers_.status(); }

  void tick() {
    if (state_ == State::FaultStop) return;  // Not even a network status query.
    const uint32_t n = port_.now();
    if (httpActive_ && expired(n, transaction_, 15000)) { fail(); return; }
    switch (state_) {
      case State::Boot:
        state_ = State::ConfigValidate; return;
      case State::ConfigValidate:
        if (pollSeconds_ < 60 || pollSeconds_ > 86400 || !port_.configure()) { fault(); return; }
        startWifi(); return;
      case State::WifiConnect:
        if (expired(n, segment_, 15000)) { port_.cancelWifi(); fail(); return; }
        if (port_.connected()) state_ = State::HttpConnect;
        return;
      case State::HttpConnect: {
        transaction_ = segment_ = port_.now(); httpActive_ = true; connectionOwned_ = true;
        const bool ok = port_.connectTcp();
        if (!ok || expired(port_.now(), segment_, 3000)) { fail(); return; }
        headers_.reset(accepted_[0] ? accepted_ : nullptr);
        received_ = sent_ = 0;
        requestSize_ = port_.request(request_, sizeof(request_), accepted_);
        if (!requestSize_ || requestSize_ >= sizeof(request_)) { fail(); return; }
        state_ = State::RequestSend; segment_ = port_.now(); return;
      }
      case State::RequestSend: {
        if (expired(n, segment_, 1000)) { fail(); return; }
        const int count = port_.send(reinterpret_cast<const uint8_t*>(request_) + sent_, requestSize_ - sent_);
        if (expired(port_.now(), segment_, 1000) || expired(port_.now(), transaction_, 15000)) { fail(); return; }
        if (count == -1) return;
        if (count <= 0 || size_t(count) > requestSize_ - sent_) { fail(); return; }
        sent_ += size_t(count);
        if (sent_ == requestSize_) { state_ = State::ResponseValidate; segment_ = idle_ = port_.now(); }
        return;
      }
      case State::ResponseValidate:
        // Bounded work per tick; never reads a body byte into the header buffer.
        for (unsigned i = 0; i < 256; ++i) {
          if (receiveExpired(5000)) { fail(); return; }
          uint8_t byte = 0;
          const int count = port_.receive(&byte, 1);
          if (receiveExpired(5000)) { fail(); return; }
          if (count == -1) return;
          if (count != 1 || !headers_.feed(byte)) { fail(); return; }
          idle_ = port_.now();
          if (headers_.done()) {
            segment_ = idle_;
            state_ = headers_.status() == 304 ? State::ResponseEnd : State::FrameReceive;
            return;
          }
        }
        return;
      case State::FrameReceive: {
        if (receiveExpired(5000)) { fail(); return; }
        const size_t remaining = kFrameBytes - received_;
        const size_t amount = remaining < 1024 ? remaining : 1024;
        const int count = port_.receive(frame_ + received_, amount);
        if (receiveExpired(5000)) { fail(); return; }
        if (count == -1) return;
        if (count <= 0 || size_t(count) > amount) { fail(); return; }
        received_ += size_t(count); idle_ = port_.now();
        if (received_ == kFrameBytes) { state_ = State::ResponseEnd; segment_ = idle_; }
        return;
      }
      case State::ResponseEnd: {
        if (receiveExpired(2000)) { fail(); return; }
        uint8_t excess = 0;  // Never write byte 15001 into frame_.
        const int count = port_.receive(&excess, 1);
        if (receiveExpired(2000)) { fail(); return; }
        if (count == -1) return;
        if (count != 0) { fail(); return; }
        closeConnection();
        if (expired(port_.now(), transaction_, 15000)) { fail(); return; }
        if (headers_.status() == 304) { wait(State::PollWait); return; }
        state_ = State::FrameValidate; return;
      }
      case State::FrameValidate:
        if (!port_.hashTag(frame_, kFrameBytes, candidate_) ||
            expired(port_.now(), transaction_, 15000) || std::strcmp(candidate_, headers_.etag())) { fail(); return; }
        httpActive_ = false;
        if (!std::strcmp(candidate_, accepted_)) { wait(State::PollWait); return; }
        state_ = State::DisplayPending; return;
      case State::DisplayPending:
        std::memcpy(attempt_, candidate_, sizeof(attempt_));
        state_ = State::DisplayUpdate; return;
      case State::DisplayUpdate:
        if (!port_.display(frame_, kFrameBytes)) { fault(); return; }
        std::memcpy(accepted_, attempt_, sizeof(accepted_));
        wait(State::PollWait); return;
      case State::PollWait:
      case State::FailureWait:
        if (expired(n, segment_, pollSeconds_ * 1000u)) {
          if (port_.connected()) state_ = State::HttpConnect;
          else startWifi();
        }
        return;
      case State::FaultStop: return;
    }
  }
 private:
  bool receiveExpired(uint32_t budget) {
    const uint32_t n = port_.now();
    return expired(n, transaction_, 15000) || expired(n, segment_, budget) || expired(n, idle_, 2000);
  }
  void startWifi() { segment_ = port_.now(); port_.beginWifi(); state_ = State::WifiConnect; }
  void wait(State s) {
    httpActive_ = false; candidate_[0] = 0; state_ = s; segment_ = port_.now();
  }
  void closeConnection() { if (connectionOwned_) { port_.close(); connectionOwned_ = false; } }
  void fail() { closeConnection(); wait(State::FailureWait); }
  void fault() { httpActive_ = false; candidate_[0] = 0; state_ = State::FaultStop; }
  Port& port_;
  uint8_t* const frame_;
  const uint32_t pollSeconds_;
  State state_ = State::Boot;
  Headers headers_;
  char request_[512]{}, candidate_[67]{}, attempt_[67]{}, accepted_[67]{};
  size_t requestSize_ = 0, sent_ = 0, received_ = 0;
  uint32_t transaction_ = 0, segment_ = 0, idle_ = 0;
  bool httpActive_ = false;
  bool connectionOwned_ = false;
};
}  // namespace eink::network_progress
