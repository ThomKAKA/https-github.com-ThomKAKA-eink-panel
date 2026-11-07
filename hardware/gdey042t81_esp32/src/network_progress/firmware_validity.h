#pragma once
#include <cstdint>

namespace eink::network_progress {
// Marks a pending OTA image valid only after continuous connection for holdMs.
class FirmwareValidity {
 public:
  explicit FirmwareValidity(uint32_t holdMs = 120000) : holdMs_(holdMs) {}

  // Returns true at most once per pending-image session.
  bool observe(uint32_t now, bool pending, bool connected) {
    if (!pending) {
      active_ = false;
      marked_ = false;
      return false;
    }
    if (!connected) {
      active_ = false;
      return false;
    }
    if (!active_) {
      active_ = true;
      since_ = now;
    }
    if (!marked_ && uint32_t(now - since_) >= holdMs_) {
      marked_ = true;
      return true;
    }
    return false;
  }

 private:
  uint32_t holdMs_, since_ = 0;
  bool active_ = false, marked_ = false;
};
}  // namespace eink::network_progress
