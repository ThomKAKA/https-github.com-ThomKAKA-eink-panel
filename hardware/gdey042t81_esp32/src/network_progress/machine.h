#pragma once
#include "protocol.h"
#include "transport.h"

namespace eink::network_progress {
enum class State {
  Boot, ConfigValidate, WifiInit, WifiConnect, HttpConnect, RequestSend, ResponseValidate, FrameReceive,
  ResponseEnd, FrameValidate, DisplayPending, DisplayUpdate, PollWait,
  FailureWait, FaultStop, DeviceReport, HostResolve, Provisioning,
  FirmwareCheck = 18,
  FirmwareUpdate = 19
};
enum class ReportStage { Communication, FrameAccepted, RefreshFlowComplete };
enum class ReportResult { Pending, Finished, Failed, InvariantFailure };
enum class ConfigResult { Valid, Invalid };
enum class WifiInitResult { Ready, Failed };
enum class Failure {
  None, ConfigInvalid, WifiInitFailure, WifiAssociationFailure, NetworkDisconnected,
  TcpConnectFailure, HttpProtocolFailure, FrameValidationFailure,
  DisplayInvariantFailure, InternalInvariantFailure, FirmwareUpdateFailure
};
enum class FirmwareCheckResult { Pending, NoUpdate, UpdateAvailable, Failed, InvariantFailure };
enum class FirmwareUpdateResult { Pending, ReadyToReboot, Failed, InvariantFailure };

// Port owns the socket. -1 = no progress, -2 = network error, -3 = invariant
// failure, 0 = receive EOF. finishTcp must report cleanup failure, not hide it.
// No application task other than Machine may use Port or the frame buffer.
class Port {
 public:
  virtual ~Port() = default;
  virtual uint32_t now() = 0;
  virtual ConfigResult validateConfiguration() = 0;
  virtual WifiInitResult initializeWifi() = 0;
  virtual bool connected() = 0;
  virtual bool associationFailed() = 0;
  virtual void beginWifi() = 0;
  virtual void cancelWifi() = 0;
  virtual bool beginProvisioning() = 0;
  virtual bool pollProvisioning() = 0;
  virtual void resolveHost() = 0;
  virtual ConnectResult beginTcp() = 0;
  virtual ConnectResult pollTcp() = 0;
  virtual int send(const uint8_t*, size_t) = 0;
  virtual int receive(uint8_t*, size_t) = 0;
  virtual bool finishTcp() = 0;
  virtual size_t request(char*, size_t, const char*) = 0;
  virtual bool hashTag(const uint8_t*, size_t, char (&)[67]) = 0;
  virtual bool display(const uint8_t*, size_t) = 0;
  virtual ReportResult beginReport(ReportStage, const char*) = 0;
  virtual ReportResult pollReport() = 0;
  // Default keeps existing fakes compiling; the device overrides it in Task 6.
  virtual const char* firmwareVersion() { return ""; }
  virtual FirmwareCheckResult beginFirmwareCheck() = 0;
  virtual FirmwareCheckResult pollFirmwareCheck() = 0;
  virtual FirmwareUpdateResult beginFirmwareUpdate() = 0;
  virtual FirmwareUpdateResult pollFirmwareUpdate() = 0;
  virtual void rebootForFirmware() = 0;
};

class Machine {
 public:
  Machine(Port& port, uint8_t (&frame)[kFrameBytes], uint32_t pollSeconds)
      : port_(port), frame_(frame), pollSeconds_(pollSeconds) {}
  State state() const { return state_; }
  const char* acceptedIdentity() const { return accepted_; }
  const char* attemptIdentity() const { return attempt_; }
  int httpStatus() const { return headers_.status(); }
  Failure failure() const { return failure_; }

  // Explicit software entry only at an initialized, idle socket boundary.
  // No GPIO/serial command or failure-triggered entry is invented here.
  bool requestProvisioning() {
    if (!initialized_ || (state_ != State::PollWait && state_ != State::FailureWait)) return false;
    if (!port_.beginProvisioning()) return false;
    state_ = State::Provisioning;
    return true;
  }

  void tick() {
    if (state_ == State::FaultStop) return;  // Not even a network status query.
    const uint32_t n = port_.now();
    if (httpActive_ && expired(n, transaction_, 15000)) { fail(transactionFailure()); return; }
    if (httpActive_ && !port_.connected()) { fail(Failure::NetworkDisconnected); return; }
    switch (state_) {
      case State::Boot:
        state_ = State::ConfigValidate; return;
      case State::ConfigValidate:
        if (pollSeconds_ < 60 || pollSeconds_ > 86400 ||
            port_.validateConfiguration() != ConfigResult::Valid) { fault(Failure::ConfigInvalid); return; }
        state_ = State::WifiInit; return;
      case State::WifiInit:
        initialized_ = false;
        if (port_.initializeWifi() != WifiInitResult::Ready) { fail(Failure::WifiInitFailure); return; }
        initialized_ = true;
        startWifi(); return;
      case State::WifiConnect:
        if (expired(n, segment_, 15000)) { cancelAssociation(); fail(Failure::WifiAssociationFailure); return; }
        if (port_.connected()) { associating_ = false; state_ = State::HostResolve; }
        else if (port_.associationFailed()) { cancelAssociation(); fail(Failure::WifiAssociationFailure); }
        return;
      case State::HostResolve:
        // One bounded discovery before the unchanged HTTP transaction budgets.
        port_.resolveHost();
        firmwareStarted_ = false;
        state_ = State::FirmwareCheck;
        return;
      case State::FirmwareCheck: {
        const auto result = firmwareStarted_ ? port_.pollFirmwareCheck()
                                            : port_.beginFirmwareCheck();
        firmwareStarted_ = true;
        if (result == FirmwareCheckResult::Pending) return;
        firmwareStarted_ = false;
        if (result == FirmwareCheckResult::InvariantFailure) {
          fault(Failure::InternalInvariantFailure);
          return;
        }
        if (result == FirmwareCheckResult::UpdateAvailable) {
          state_ = State::FirmwareUpdate;
          return;
        }
        state_ = State::HttpConnect;
        return;
      }
      case State::FirmwareUpdate: {
        const auto result = firmwareStarted_ ? port_.pollFirmwareUpdate()
                                            : port_.beginFirmwareUpdate();
        firmwareStarted_ = true;
        if (result == FirmwareUpdateResult::Pending) return;
        firmwareStarted_ = false;
        if (result == FirmwareUpdateResult::InvariantFailure) {
          fault(Failure::InternalInvariantFailure);
          return;
        }
        // A failed update enters FailureWait with no display and no retry: the
        // Host offer is one-shot, so the next manifest reports armed=false and
        // the ordinary frame poll resumes with the old identity retained.
        if (result == FirmwareUpdateResult::Failed) {
          fail(Failure::FirmwareUpdateFailure);
          return;
        }
        port_.rebootForFirmware();
        state_ = State::FaultStop;
        return;
      }
      case State::Provisioning:
        if (port_.pollProvisioning()) { failure_ = Failure::None; state_ = State::HostResolve; }
        return;
      case State::HttpConnect: {
        if (!initialized_) { fault(Failure::InternalInvariantFailure); return; }
        if (!port_.connected()) { fail(Failure::NetworkDisconnected); return; }
        if (!httpActive_) {
          candidate_[0] = 0; failure_ = Failure::None;
          transaction_ = segment_ = port_.now(); httpActive_ = true;
          tcpStarted_ = false;
        }
        if (expired(port_.now(), segment_, 3000)) { fail(Failure::TcpConnectFailure); return; }
        const auto result = tcpStarted_ ? port_.pollTcp() : port_.beginTcp();
        tcpStarted_ = true;
        if (result == ConnectResult::InvariantFailure) { fault(Failure::InternalInvariantFailure); return; }
        if (expired(port_.now(), segment_, 3000) || expired(port_.now(), transaction_, 15000) ||
            result == ConnectResult::Failed) { fail(Failure::TcpConnectFailure); return; }
        if (!port_.connected()) { fail(Failure::NetworkDisconnected); return; }
        if (result == ConnectResult::Pending) return;
        headers_.reset(accepted_[0] ? accepted_ : nullptr);
        received_ = sent_ = 0;
        requestSize_ = port_.request(request_, sizeof(request_), accepted_);
        if (!requestSize_ || requestSize_ >= sizeof(request_)) { fault(Failure::InternalInvariantFailure); return; }
        state_ = State::RequestSend; segment_ = port_.now(); return;
      }
      case State::RequestSend: {
        if (expired(n, segment_, 1000)) { fail(Failure::HttpProtocolFailure); return; }
        const int count = port_.send(reinterpret_cast<const uint8_t*>(request_) + sent_, requestSize_ - sent_);
        if (count == kIoInvariant) { fault(Failure::InternalInvariantFailure); return; }
        if (expired(port_.now(), segment_, 1000) || expired(port_.now(), transaction_, 15000)) { fail(Failure::HttpProtocolFailure); return; }
        if (count == -1) return;
        if (count <= 0) { fail(Failure::HttpProtocolFailure); return; }
        if (size_t(count) > requestSize_ - sent_) { fault(Failure::InternalInvariantFailure); return; }
        sent_ += size_t(count);
        if (sent_ == requestSize_) { state_ = State::ResponseValidate; segment_ = idle_ = port_.now(); }
        return;
      }
      case State::ResponseValidate:
        // Bounded work per tick; never reads a body byte into the header buffer.
        for (unsigned i = 0; i < 256; ++i) {
          if (receiveExpired(5000)) { fail(Failure::HttpProtocolFailure); return; }
          uint8_t byte = 0;
          const int count = port_.receive(&byte, 1);
          if (count == kIoInvariant) { fault(Failure::InternalInvariantFailure); return; }
          if (receiveExpired(5000)) { fail(Failure::HttpProtocolFailure); return; }
          if (count == -1) return;
          if (count > 1) { fault(Failure::InternalInvariantFailure); return; }
          if (count != 1 || !headers_.feed(byte)) { fail(Failure::HttpProtocolFailure); return; }
          idle_ = port_.now();
          if (headers_.done()) {
            segment_ = idle_;
            state_ = headers_.status() == 304 ? State::ResponseEnd : State::FrameReceive;
            return;
          }
        }
        return;
      case State::FrameReceive: {
        if (receiveExpired(5000)) { fail(Failure::FrameValidationFailure); return; }
        const size_t remaining = kFrameBytes - received_;
        const size_t amount = remaining < 1024 ? remaining : 1024;
        const int count = port_.receive(frame_ + received_, amount);
        if (count == kIoInvariant) { fault(Failure::InternalInvariantFailure); return; }
        if (receiveExpired(5000)) { fail(Failure::FrameValidationFailure); return; }
        if (count == -1) return;
        if (count <= 0) { fail(Failure::FrameValidationFailure); return; }
        if (size_t(count) > amount) { fault(Failure::InternalInvariantFailure); return; }
        received_ += size_t(count); idle_ = port_.now();
        if (received_ == kFrameBytes) { state_ = State::ResponseEnd; segment_ = idle_; }
        return;
      }
      case State::ResponseEnd: {
        if (receiveExpired(2000)) { fail(Failure::HttpProtocolFailure); return; }
        uint8_t excess = 0;  // Never write byte 15001 into frame_.
        const int count = port_.receive(&excess, 1);
        if (count == kIoInvariant) { fault(Failure::InternalInvariantFailure); return; }
        if (receiveExpired(2000)) { fail(Failure::HttpProtocolFailure); return; }
        if (count == -1) return;
        if (count != 0) { fail(Failure::FrameValidationFailure); return; }
        if (!closeConnection()) { fault(Failure::InternalInvariantFailure); return; }
        if (expired(port_.now(), transaction_, 15000)) { fail(Failure::HttpProtocolFailure); return; }
        if (headers_.status() == 304) { startReport(ReportStage::Communication); return; }
        state_ = State::FrameValidate; return;
      }
      case State::FrameValidate:
        if (!port_.hashTag(frame_, kFrameBytes, candidate_) ||
            expired(port_.now(), transaction_, 15000) || std::strcmp(candidate_, headers_.etag())) { fail(Failure::FrameValidationFailure); return; }
        httpActive_ = false;
        if (!std::strcmp(candidate_, accepted_)) { startReport(ReportStage::Communication); return; }
        state_ = State::DisplayPending; return;
      case State::DisplayPending:
        if (httpActive_ || tcpStarted_) { fault(Failure::InternalInvariantFailure); return; }
        std::memcpy(attempt_, candidate_, sizeof(attempt_));
        startReport(ReportStage::FrameAccepted); return;
      case State::DisplayUpdate:
        if (httpActive_ || tcpStarted_) { fault(Failure::InternalInvariantFailure); return; }
        if (!port_.display(frame_, kFrameBytes)) { fault(Failure::DisplayInvariantFailure); return; }
        std::memcpy(accepted_, attempt_, sizeof(accepted_));
        startReport(ReportStage::RefreshFlowComplete); return;
      case State::DeviceReport: {
        // The frame socket is closed; reports share the same exclusive owner.
        const auto result = reportStarted_ ? port_.pollReport() : port_.beginReport(
          reportStage_, reportStage_ == ReportStage::FrameAccepted ? attempt_ : accepted_);
        reportStarted_ = true;
        if (result == ReportResult::InvariantFailure) { fault(Failure::InternalInvariantFailure); return; }
        if (result == ReportResult::Pending) return;
        // Ordinary report failure does not change frame/display eligibility. No retry.
        if (reportStage_ == ReportStage::FrameAccepted) state_ = State::DisplayUpdate;
        else wait(State::PollWait);
        return;
      }
      case State::PollWait:
      case State::FailureWait:
        if (expired(n, segment_, pollSeconds_ * 1000u)) {
          if (!initialized_) state_ = State::WifiInit;
          else if (port_.connected()) state_ = State::HostResolve;
          else startWifi();
        }
        return;
      case State::FaultStop: return;
    }
    fault(Failure::InternalInvariantFailure);  // Invalid enum/state, not network failure.
  }
 private:
  void startReport(ReportStage stage) {
    httpActive_ = false; reportStage_ = stage; reportStarted_ = false;
    state_ = State::DeviceReport;
  }
  bool receiveExpired(uint32_t budget) {
    const uint32_t n = port_.now();
    return expired(n, transaction_, 15000) || expired(n, segment_, budget) || expired(n, idle_, 2000);
  }
  void startWifi() {
    if (!initialized_) { fault(Failure::InternalInvariantFailure); return; }
    segment_ = port_.now(); associating_ = true; port_.beginWifi(); state_ = State::WifiConnect;
  }
  void cancelAssociation() { if (associating_) { port_.cancelWifi(); associating_ = false; } }
  void wait(State s) {
    httpActive_ = false; candidate_[0] = 0; state_ = s; segment_ = port_.now();
  }
  bool closeConnection() {
    if (!tcpStarted_) return true;
    tcpStarted_ = false;  // Never repeat release after failure/uncertainty.
    return port_.finishTcp();
  }
  Failure transactionFailure() const {
    return state_ == State::HttpConnect ? Failure::TcpConnectFailure :
      state_ == State::FrameReceive || state_ == State::FrameValidate
      ? Failure::FrameValidationFailure : Failure::HttpProtocolFailure;
  }
  void fail(Failure reason) {
    if (!closeConnection()) { fault(Failure::InternalInvariantFailure); return; }
    failure_ = reason; wait(State::FailureWait);
  }
  void fault(Failure reason) {
    if (!closeConnection()) reason = Failure::InternalInvariantFailure;
    httpActive_ = false; candidate_[0] = 0; failure_ = reason; state_ = State::FaultStop;
  }
  Port& port_;
  uint8_t* const frame_;
  const uint32_t pollSeconds_;
  State state_ = State::Boot;
  Headers headers_;
  char request_[512]{}, candidate_[67]{}, attempt_[67]{}, accepted_[67]{};
  size_t requestSize_ = 0, sent_ = 0, received_ = 0;
  uint32_t transaction_ = 0, segment_ = 0, idle_ = 0;
  bool httpActive_ = false;
  bool tcpStarted_ = false, initialized_ = false, associating_ = false;
  ReportStage reportStage_ = ReportStage::Communication;
  bool reportStarted_ = false;
  bool firmwareStarted_ = false;
  Failure failure_ = Failure::None;
};
}  // namespace eink::network_progress
