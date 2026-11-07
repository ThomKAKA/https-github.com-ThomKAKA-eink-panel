#pragma once
#include "machine.h"
#include "host_resolution.h"
#include "ota_protocol.h"
#include <algorithm>
#include <cstdio>
#include <cstring>

namespace eink::network_progress {
class OtaSink {
 public:
  virtual ~OtaSink() = default;
  virtual bool begin(size_t size) = 0;
  virtual bool write(const uint8_t* data, size_t size) = 0;
  virtual bool finish(const char* expectedSha) = 0;
  virtual bool activate() = 0;
  virtual void reboot() = 0;
  virtual void abort() = 0;
};

class OtaUpdater {
 public:
  OtaUpdater(Port& port, const ResolvedHost& host, OtaSink& sink)
      : port_(port), host_(host), sink_(sink) {}

  FirmwareCheckResult beginCheck() {
    if (active_) return FirmwareCheckResult::InvariantFailure;
    const int n = std::snprintf(request_, sizeof(request_),
      "GET %s HTTP/1.1\r\nHost: %u.%u.%u.%u:%u\r\nConnection: close\r\n"
      "Accept: application/json\r\n\r\n",
      kOtaManifestEndpoint, host_.address[0], host_.address[1],
      host_.address[2], host_.address[3], host_.port);
    if (n <= 0 || size_t(n) >= sizeof(request_)) return FirmwareCheckResult::InvariantFailure;
    resetTransfer(size_t(n));
    phase_ = Phase::ManifestHeaders;
    const auto result = port_.beginTcp();
    if (result == ConnectResult::InvariantFailure) return finishCheck(FirmwareCheckResult::InvariantFailure);
    if (result == ConnectResult::Failed) return finishCheck(FirmwareCheckResult::Failed);
    tcpOpen_ = true;
    connected_ = result == ConnectResult::Connected;
    return FirmwareCheckResult::Pending;
  }

  FirmwareCheckResult pollCheck() {
    if (!active_ || (phase_ != Phase::ManifestHeaders && phase_ != Phase::ManifestBody))
      return FirmwareCheckResult::InvariantFailure;
    if (!connected_) {
      if (expired(port_.now(), start_, 3000) || !port_.connected())
        return finishCheck(FirmwareCheckResult::Failed);
      const auto result = port_.pollTcp();
      if (result == ConnectResult::InvariantFailure) return finishCheck(FirmwareCheckResult::InvariantFailure);
      if (result == ConnectResult::Failed) return finishCheck(FirmwareCheckResult::Failed);
      connected_ = result == ConnectResult::Connected;
      return FirmwareCheckResult::Pending;
    }
    const uint32_t now = port_.now();
    if (expired(now, start_, 5000) || expired(now, idle_, 2000))
      return finishCheck(FirmwareCheckResult::Failed);
    if (sent_ < requestSize_) {
      const int n = port_.send(reinterpret_cast<const uint8_t*>(request_) + sent_, requestSize_ - sent_);
      if (n == kIoInvariant) return finishCheck(FirmwareCheckResult::InvariantFailure);
      if (n == kIoPending) return FirmwareCheckResult::Pending;
      if (n <= 0) return finishCheck(FirmwareCheckResult::Failed);
      if (size_t(n) > requestSize_ - sent_) return finishCheck(FirmwareCheckResult::InvariantFailure);
      sent_ += size_t(n);
      return FirmwareCheckResult::Pending;
    }
    if (phase_ == Phase::ManifestHeaders) {
      uint8_t byte = 0;
      const int n = port_.receive(&byte, 1);
      if (n == kIoInvariant) return finishCheck(FirmwareCheckResult::InvariantFailure);
      if (n == kIoPending) return FirmwareCheckResult::Pending;
      if (n != 1) return finishCheck(FirmwareCheckResult::Failed);
      idle_ = now;
      if (!manifestHeaders_.feed(byte)) return finishCheck(FirmwareCheckResult::Failed);
      if (manifestHeaders_.done()) {
        bodyLength_ = manifestHeaders_.headers().length;
        bodyUsed_ = 0;
        phase_ = Phase::ManifestBody;
      }
      return FirmwareCheckResult::Pending;
    }
    if (bodyUsed_ < bodyLength_) {
      const size_t amount = bodyLength_ - bodyUsed_;
      const int n = port_.receive(reinterpret_cast<uint8_t*>(checkBody_ + bodyUsed_), amount);
      if (n == kIoInvariant) return finishCheck(FirmwareCheckResult::InvariantFailure);
      if (n == kIoPending) return FirmwareCheckResult::Pending;
      if (n <= 0 || size_t(n) > amount) return finishCheck(FirmwareCheckResult::Failed);
      bodyUsed_ += size_t(n);
      idle_ = now;
      if (bodyUsed_ < bodyLength_) return FirmwareCheckResult::Pending;
    }
    uint8_t excess = 0;
    const int n = port_.receive(&excess, 1);
    if (n == kIoInvariant) return finishCheck(FirmwareCheckResult::InvariantFailure);
    if (n == kIoPending) return FirmwareCheckResult::Pending;
    if (n != 0) return finishCheck(FirmwareCheckResult::Failed);
    if (!closeSocket()) return finishCheck(FirmwareCheckResult::InvariantFailure);
    checkBody_[bodyUsed_] = 0;
    FirmwareOffer offer{};
    if (!parseManifestBody(checkBody_, offer)) return finishCheck(FirmwareCheckResult::Failed);
    if (!offer.armed || !std::strcmp(offer.version, port_.firmwareVersion()))
      return finishCheck(FirmwareCheckResult::NoUpdate);
    offer_ = offer;
    return finishCheck(FirmwareCheckResult::UpdateAvailable);
  }

  FirmwareUpdateResult beginUpdate() {
    if (active_ || !offer_.armed) return FirmwareUpdateResult::Failed;
    if (!sink_.begin(offer_.size)) return FirmwareUpdateResult::Failed;
    const int n = std::snprintf(request_, sizeof(request_),
      "GET %s HTTP/1.1\r\nHost: %u.%u.%u.%u:%u\r\nConnection: close\r\n"
      "Accept: application/octet-stream\r\nAccept-Encoding: identity\r\n\r\n",
      kOtaImageEndpoint, host_.address[0], host_.address[1],
      host_.address[2], host_.address[3], host_.port);
    if (n <= 0 || size_t(n) >= sizeof(request_)) {
      sink_.abort();
      return FirmwareUpdateResult::Failed;
    }
    resetTransfer(size_t(n));
    phase_ = Phase::ImageHeaders;
    const auto result = port_.beginTcp();
    if (result == ConnectResult::InvariantFailure) {
      sink_.abort();
      return FirmwareUpdateResult::InvariantFailure;
    }
    if (result == ConnectResult::Failed) {
      sink_.abort();
      return FirmwareUpdateResult::Failed;
    }
    tcpOpen_ = true;
    connected_ = result == ConnectResult::Connected;
    return FirmwareUpdateResult::Pending;
  }

  FirmwareUpdateResult pollUpdate() {
    if (!active_ || (phase_ != Phase::ImageHeaders && phase_ != Phase::ImageBody))
      return FirmwareUpdateResult::InvariantFailure;
    if (!connected_) {
      if (expired(port_.now(), start_, 3000) || !port_.connected())
        return finishUpdate(FirmwareUpdateResult::Failed);
      const auto result = port_.pollTcp();
      if (result == ConnectResult::InvariantFailure) return finishUpdate(FirmwareUpdateResult::InvariantFailure);
      if (result == ConnectResult::Failed) return finishUpdate(FirmwareUpdateResult::Failed);
      connected_ = result == ConnectResult::Connected;
      return FirmwareUpdateResult::Pending;
    }
    const uint32_t now = port_.now();
    if (expired(now, start_, 120000) || expired(now, idle_, 10000))
      return finishUpdate(FirmwareUpdateResult::Failed);
    if (sent_ < requestSize_) {
      const int n = port_.send(reinterpret_cast<const uint8_t*>(request_) + sent_, requestSize_ - sent_);
      if (n == kIoInvariant) return finishUpdate(FirmwareUpdateResult::InvariantFailure);
      if (n == kIoPending) return FirmwareUpdateResult::Pending;
      if (n <= 0) return finishUpdate(FirmwareUpdateResult::Failed);
      if (size_t(n) > requestSize_ - sent_) return finishUpdate(FirmwareUpdateResult::InvariantFailure);
      sent_ += size_t(n);
      return FirmwareUpdateResult::Pending;
    }
    if (phase_ == Phase::ImageHeaders) {
      uint8_t byte = 0;
      const int n = port_.receive(&byte, 1);
      if (n == kIoInvariant) return finishUpdate(FirmwareUpdateResult::InvariantFailure);
      if (n == kIoPending) return FirmwareUpdateResult::Pending;
      if (n != 1) return finishUpdate(FirmwareUpdateResult::Failed);
      idle_ = now;
      if (!imageHeaders_.feed(byte)) return finishUpdate(FirmwareUpdateResult::Failed);
      if (imageHeaders_.done()) {
        const auto& h = imageHeaders_.headers();
        if (h.length != offer_.size ||
            std::strcmp(h.version, offer_.version) ||
            std::strcmp(h.sha256, offer_.sha256))
          return finishUpdate(FirmwareUpdateResult::Failed);
        bodyLength_ = offer_.size;
        bodyUsed_ = 0;
        phase_ = Phase::ImageBody;
      }
      return FirmwareUpdateResult::Pending;
    }
    if (bodyUsed_ < bodyLength_) {
      const size_t amount = std::min(sizeof(otaBuffer_), bodyLength_ - bodyUsed_);
      const int n = port_.receive(otaBuffer_, amount);
      if (n == kIoInvariant) return finishUpdate(FirmwareUpdateResult::InvariantFailure);
      if (n == kIoPending) return FirmwareUpdateResult::Pending;
      if (n <= 0 || size_t(n) > amount) return finishUpdate(FirmwareUpdateResult::Failed);
      if (!sink_.write(otaBuffer_, size_t(n))) return finishUpdate(FirmwareUpdateResult::Failed);
      bodyUsed_ += size_t(n);
      idle_ = now;
      return FirmwareUpdateResult::Pending;
    }
    uint8_t excess = 0;
    const int n = port_.receive(&excess, 1);
    if (n == kIoInvariant) return finishUpdate(FirmwareUpdateResult::InvariantFailure);
    if (n == kIoPending) return FirmwareUpdateResult::Pending;
    if (n != 0) return finishUpdate(FirmwareUpdateResult::Failed);
    if (!closeSocket()) return finishUpdate(FirmwareUpdateResult::InvariantFailure);
    if (!sink_.finish(offer_.sha256)) return finishUpdate(FirmwareUpdateResult::Failed);
    if (!sink_.activate()) return finishUpdate(FirmwareUpdateResult::Failed);
    active_ = false;
    return FirmwareUpdateResult::ReadyToReboot;
  }

 private:
  enum class Phase { ManifestHeaders, ManifestBody, ImageHeaders, ImageBody };

  void resetTransfer(size_t size) {
    requestSize_ = size;
    sent_ = bodyUsed_ = bodyLength_ = 0;
    connected_ = false;
    active_ = true;
    start_ = idle_ = port_.now();
    manifestHeaders_.reset();
    imageHeaders_.reset();
  }

  bool closeSocket() {
    if (!tcpOpen_) return true;
    tcpOpen_ = false;
    return port_.finishTcp();
  }

  FirmwareCheckResult finishCheck(FirmwareCheckResult result) {
    active_ = false;
    if (!closeSocket()) return FirmwareCheckResult::InvariantFailure;
    return result;
  }

  FirmwareUpdateResult finishUpdate(FirmwareUpdateResult result) {
    active_ = false;
    if (result != FirmwareUpdateResult::ReadyToReboot) sink_.abort();
    if (!closeSocket()) return FirmwareUpdateResult::InvariantFailure;
    return result;
  }

  Port& port_;
  const ResolvedHost& host_;
  OtaSink& sink_;
  char request_[512]{};
  char checkBody_[kOtaManifestBytes + 1]{};
  uint8_t otaBuffer_[4096]{};
  size_t requestSize_ = 0, sent_ = 0, bodyUsed_ = 0, bodyLength_ = 0;
  uint32_t start_ = 0, idle_ = 0;
  bool active_ = false, connected_ = false, tcpOpen_ = false;
  Phase phase_ = Phase::ManifestHeaders;
  ManifestHeaderParser manifestHeaders_;
  ImageHeaderParser imageHeaders_;
  FirmwareOffer offer_{};
};
}  // namespace eink::network_progress
