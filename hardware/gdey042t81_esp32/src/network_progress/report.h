#pragma once
#include "machine.h"
#include "host_resolution.h"
#include <cstdio>

namespace eink::network_progress {
constexpr const char* kFirmwareVersion = "round2-r1a-1";
constexpr const char* kReportEndpoint = "/api/panels/progress/device-report";

// One bounded POST per observation, using the existing Port/socket owner.
// No queue, retry, second frame buffer, wall clock or display operation.
class DeviceReporter {
 public:
  DeviceReporter(Port& port, const ResolvedHost& host)
      : port_(port), host_(host) {}

  ReportResult begin(ReportStage stage, const char* identity) {
    if (active_) return ReportResult::InvariantFailure;
    if (!validTag(identity)) return ReportResult::Failed;
    const char* name = stage == ReportStage::FrameAccepted ? "\"DEVICE_FRAME_ACCEPTED\"" :
      stage == ReportStage::RefreshFlowComplete ? "\"DEVICE_REFRESH_FLOW_COMPLETE\"" : "null";
    char body[256];
    const int bodySize = std::snprintf(body, sizeof(body),
      "{\"frame_version\":\"%.64s\",\"firmware_version\":\"%s\",\"refresh_stage\":%s}",
      identity + 1, kFirmwareVersion, name);
    if (bodySize <= 0 || size_t(bodySize) >= sizeof(body)) return ReportResult::Failed;
    const int size = std::snprintf(request_, sizeof(request_),
      "POST %s HTTP/1.1\r\nHost: %u.%u.%u.%u:%u\r\nConnection: close\r\n"
      "Content-Type: application/json\r\nContent-Length: %d\r\n\r\n%s",
      kReportEndpoint, host_.address[0], host_.address[1], host_.address[2], host_.address[3], host_.port, bodySize, body);
    if (size <= 0 || size_t(size) >= sizeof(request_)) return ReportResult::Failed;
    size_ = size_t(size); sent_ = received_ = lineSize_ = 0;
    lineDone_ = ok_ = connected_ = false; active_ = true; start_ = port_.now();
    const auto result = port_.beginTcp();
    if (result == ConnectResult::InvariantFailure) return finish(ReportResult::InvariantFailure);
    if (result == ConnectResult::Failed) return finish(ReportResult::Failed);
    connected_ = result == ConnectResult::Connected;
    return ReportResult::Pending;
  }

  ReportResult poll() {
    if (!active_) return ReportResult::InvariantFailure;
    if (expired(port_.now(), start_, 3000) || !port_.connected()) return finish(ReportResult::Failed);
    if (!connected_) {
      const auto result = port_.pollTcp();
      if (result == ConnectResult::InvariantFailure) return finish(ReportResult::InvariantFailure);
      if (result == ConnectResult::Failed) return finish(ReportResult::Failed);
      connected_ = result == ConnectResult::Connected;
      return ReportResult::Pending;
    }
    if (sent_ < size_) {
      const int n = port_.send(reinterpret_cast<const uint8_t*>(request_) + sent_, size_ - sent_);
      if (n == kIoInvariant) return finish(ReportResult::InvariantFailure);
      if (n == kIoPending) return ReportResult::Pending;
      if (n <= 0) return finish(ReportResult::Failed);
      if (size_t(n) > size_ - sent_) return finish(ReportResult::InvariantFailure);
      sent_ += size_t(n); return ReportResult::Pending;
    }
    uint8_t bytes[128];
    const int n = port_.receive(bytes, sizeof(bytes));
    if (n == kIoInvariant) return finish(ReportResult::InvariantFailure);
    if (n == kIoPending) return ReportResult::Pending;
    if (n < 0) return finish(ReportResult::Failed);
    if (n == 0) return finish(lineDone_ && ok_ ? ReportResult::Finished : ReportResult::Failed);
    if (size_t(n) > sizeof(bytes)) return finish(ReportResult::InvariantFailure);
    received_ += size_t(n);
    if (received_ > 4096) return finish(ReportResult::Failed);
    for (int i = 0; i < n && !lineDone_; ++i) {
      if (lineSize_ == sizeof(line_) - 1) return finish(ReportResult::Failed);
      line_[lineSize_++] = char(bytes[i]); line_[lineSize_] = 0;
      if (bytes[i] == '\n') {
        lineDone_ = true;
        ok_ = (std::strncmp(line_, "HTTP/1.1 200 ", 13) == 0 ||
               std::strncmp(line_, "HTTP/1.0 200 ", 13) == 0) &&
              lineSize_ >= 2 && line_[lineSize_ - 2] == '\r';
      }
    }
    return ReportResult::Pending;
  }
 private:
  ReportResult finish(ReportResult result) {
    active_ = false;
    return port_.finishTcp() ? result : ReportResult::InvariantFailure;
  }
  Port& port_;
  const ResolvedHost& host_;
  char request_[512]{}, line_[64]{};
  size_t size_ = 0, sent_ = 0, received_ = 0, lineSize_ = 0;
  uint32_t start_ = 0;
  bool active_ = false, connected_ = false, lineDone_ = false, ok_ = false;
};
}  // namespace eink::network_progress
