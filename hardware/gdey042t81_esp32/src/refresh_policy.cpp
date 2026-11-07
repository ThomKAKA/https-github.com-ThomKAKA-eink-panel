#include "refresh_policy.h"

namespace eink {

RefreshPolicy::RefreshPolicy(std::uint8_t max_fast_updates,
                             std::uint32_t min_interval_ms, bool prefer_fast_full)
    : max_fast_updates_(max_fast_updates),
      min_interval_ms_(min_interval_ms),
      prefer_fast_full_(prefer_fast_full) {}

RefreshMode RefreshPolicy::decide(bool content_changed, std::uint32_t now_ms) const {
  if (!has_frame_) return RefreshMode::Full;
  if (!content_changed ||
      static_cast<std::uint32_t>(now_ms - last_completed_at_ms_) < min_interval_ms_) {
    return RefreshMode::None;
  }
  if (fast_update_count_ >= max_fast_updates_) return RefreshMode::Full;
  return prefer_fast_full_ ? RefreshMode::FastFull : RefreshMode::Partial;
}

void RefreshPolicy::recordSuccess(RefreshMode mode, std::uint32_t completed_at_ms) {
  if (mode == RefreshMode::None) return;
  has_frame_ = true;
  last_completed_at_ms_ = completed_at_ms;
  if (mode == RefreshMode::Full) {
    fast_update_count_ = 0;
  } else if (fast_update_count_ < 255) {
    ++fast_update_count_;
  }
}

const char* refreshModeName(RefreshMode mode) {
  switch (mode) {
    case RefreshMode::None: return "HOLD";
    case RefreshMode::Full: return "FULL";
    case RefreshMode::FastFull: return "FAST_FULL";
    case RefreshMode::Partial: return "PARTIAL";
  }
  return "UNKNOWN";
}

}  // namespace eink
